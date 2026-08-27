from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from .paths import RESULTS_DIR, project_relative, resolve_project_path
from .train import load_config
from .training_data import load_training_cases


def _git(*args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], text=True, encoding="utf-8", stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(resolve_project_path(path).read_text(encoding="utf-8"))


def _training_contract(config: dict[str, Any]) -> dict[str, Any]:
    contract = {
        key: copy.deepcopy(config[key])
        for key in ("model", "dataset", "quantization", "lora", "training", "evaluation")
    }
    contract["training"].pop("seed", None)
    contract["training"].pop("resume_from_checkpoint", None)
    return contract


def build_preflight(
    matrix_path: str | Path = "configs/sprint4_matrix_v1.json", *, require_clean_git: bool = True
) -> dict[str, Any]:
    matrix_resolved = resolve_project_path(matrix_path)
    matrix = json.loads(matrix_resolved.read_text(encoding="utf-8"))
    seed_specs = matrix.get("seeds", [])
    checks: dict[str, bool] = {
        "exactly_three_seeds": len(seed_specs) == 3,
        "one_reused_and_two_new_seeds": [item.get("role") for item in seed_specs].count("reuse_m3") == 1
        and [item.get("role") for item in seed_specs].count("train") == 2,
        "seed_values_are_unique": len({item.get("seed") for item in seed_specs}) == len(seed_specs),
        "seed_names_are_unique": len({item.get("name") for item in seed_specs}) == len(seed_specs),
    }

    configs: list[dict[str, Any]] = []
    config_paths: list[Path] = []
    data_audits: dict[str, Any] = {}
    for spec in seed_specs:
        config, config_path = load_config(spec["config"])
        configs.append(config)
        config_paths.append(config_path)
        _, audit = load_training_cases(config)
        data_audits[spec["name"]] = audit

    reference_contract = _training_contract(configs[0]) if configs else {}
    checks["training_contracts_are_identical"] = bool(configs) and all(
        _training_contract(config) == reference_contract for config in configs
    )
    checks["matrix_seeds_match_configs"] = all(
        int(spec["seed"]) == int(config["training"]["seed"])
        for spec, config in zip(seed_specs, configs, strict=True)
    )
    checks["all_training_sources_are_train_only"] = all(
        audit["opened_splits"] == ["train"] and not audit["protected_splits_opened"]
        for audit in data_audits.values()
    )
    checks["all_configs_disallow_truncation"] = all(
        not config["training"].get("allow_truncation", False) for config in configs
    )
    checks["all_configs_use_model_only_checkpoints"] = all(
        bool(config["training"].get("save_only_model")) for config in configs
    )
    output_dirs = [spec["adapter"] for spec in seed_specs]
    metrics_outputs = [spec["training_metrics"] for spec in seed_specs]
    checks["adapter_outputs_are_unique"] = len(set(output_dirs)) == len(output_dirs)
    checks["training_metric_outputs_are_unique"] = len(set(metrics_outputs)) == len(metrics_outputs)

    reused = next((item for item in seed_specs if item.get("role") == "reuse_m3"), None)
    if reused:
        metrics_path = resolve_project_path(reused["training_metrics"])
        manifest_path = resolve_project_path(reused["adapter_manifest"])
        adapter_path = resolve_project_path(reused["adapter"])
        metrics = _read_json(metrics_path) if metrics_path.exists() else {}
        manifest = _read_json(manifest_path) if manifest_path.exists() else {}
        checks["m3_seed_training_is_completed"] = metrics.get("status") == "completed"
        checks["m3_seed_adapter_is_present"] = (adapter_path / "adapter_model.safetensors").exists()
        checks["m3_seed_adapter_manifest_is_compatible"] = bool(manifest.get("base_model_compatible"))
    else:
        checks["m3_seed_training_is_completed"] = False
        checks["m3_seed_adapter_is_present"] = False
        checks["m3_seed_adapter_manifest_is_compatible"] = False

    protected = matrix.get("protected_evaluation", {})
    protected_paths = [value for key, value in protected.items() if key != "open_policy"]
    protected_names = {Path(value).stem.lower() for value in protected_paths}
    checks["protected_paths_are_declared_but_not_training_sources"] = (
        {"test", "boundary_test", "challenge"} <= protected_names
        and all(
            path not in {
                source["path"]
                for config in configs
                for source in config["dataset"]["train_sources"]
            }
            for path in protected_paths
        )
    )

    reference_commit = matrix.get("reference_commit")
    tag_commit = _git("rev-list", "-n", "1", matrix.get("reference_tag", ""))
    current_commit = _git("rev-parse", "HEAD")
    checks["reference_tag_matches_m3_commit"] = bool(reference_commit) and tag_commit == reference_commit
    checks["current_commit_descends_from_m3"] = bool(reference_commit) and subprocess.call(
        ["git", "merge-base", "--is-ancestor", reference_commit, "HEAD"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ) == 0
    git_status = _git("status", "--porcelain") or ""
    non_result_changes = [
        line
        for line in git_status.splitlines()
        if not line[3:].replace("\\", "/").startswith("results/sprint4/")
    ]
    checks["git_source_worktree_is_clean"] = not non_result_changes if require_clean_git else True

    config_hashes = {
        spec["name"]: hashlib.sha256(path.read_bytes()).hexdigest()
        for spec, path in zip(seed_specs, config_paths, strict=True)
    }
    run_queue = [
        {
            "name": spec["name"],
            "seed": spec["seed"],
            "config": spec["config"],
            "action": "reuse" if spec["role"] == "reuse_m3" else "train",
        }
        for spec in seed_specs
    ]
    return {
        "milestone": "Sprint 4 training preflight",
        "decision": "READY_FOR_TRAINING" if all(checks.values()) else "BLOCKED",
        "checks": checks,
        "matrix": project_relative(matrix_resolved),
        "matrix_sha256": hashlib.sha256(matrix_resolved.read_bytes()).hexdigest(),
        "config_sha256": config_hashes,
        "current_git_commit": current_commit,
        "data_audits": data_audits,
        "run_queue": run_queue,
        "protected_splits_opened": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight replikacji Q1 w Sprincie 4")
    parser.add_argument("--matrix", default="configs/sprint4_matrix_v1.json")
    parser.add_argument("--output", default=str(RESULTS_DIR / "sprint4" / "preflight.json"))
    parser.add_argument("--allow-dirty", action="store_true", help="Wyłącznie do developmentu preflightu")
    args = parser.parse_args()
    result = build_preflight(args.matrix, require_clean_git=not args.allow_dirty)
    output = resolve_project_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "checks": result["checks"]}, ensure_ascii=False, indent=2))
    print(f"Pełny raport: {output}")
    return 0 if result["decision"] == "READY_FOR_TRAINING" else 1


if __name__ == "__main__":
    raise SystemExit(main())
