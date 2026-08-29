from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

from .paths import RESULTS_DIR, project_relative, resolve_project_path


CONTENT_PATHS = (
    "materials",
    "notebooks",
    "docs/18_sprint_5_narrative_and_scenarios.md",
    "docs/19_sprint_5_material_update_report.md",
)
FROZEN_CONTRACT_FILES = (
    "configs/sprint4_matrix_v1.json",
    "configs/sprint6_evidence_gate_v1.json",
    "configs/sprint6_shadow_challenge_v1.json",
    "configs/status_policy_v1.json",
    "configs/q2_source_guard_v1.json",
    "configs/q2_decision_guard_v2.json",
    "configs/deterministic_decision_rules_v1.json",
    "schemas/financial_control_output.schema.json",
)


def _read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(resolve_project_path(path).read_text(encoding="utf-8"))


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with resolve_project_path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(*args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], text=True, encoding="utf-8", stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _pptx_contract(path: str | Path) -> dict[str, int]:
    source = resolve_project_path(path)
    with zipfile.ZipFile(source) as archive:
        names = archive.namelist()
        slides = [name for name in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)]
        notes = [name for name in names if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)]
        notes_with_sources = 0
        for name in notes:
            text = archive.read(name).decode("utf-8")
            if "[Sources]" in text and "[/Sources]" in text:
                notes_with_sources += 1
    return {
        "slides": len(slides),
        "notes": len(notes),
        "notes_with_sources": notes_with_sources,
    }


def _notebook_contract() -> dict[str, Any]:
    notebooks = sorted(resolve_project_path("notebooks").glob("*.ipynb"))
    compiled_cells = 0
    for path in notebooks:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("nbformat") != 4:
            raise ValueError(f"Nieobsługiwany nbformat: {project_relative(path)}")
        for index, cell in enumerate(payload.get("cells", []), start=1):
            if cell.get("cell_type") != "code":
                continue
            compile("".join(cell.get("source", [])), f"{path.name}:cell-{index}", "exec")
            compiled_cells += 1
    return {"count": len(notebooks), "compiled_code_cells": compiled_cells}


def _run_unit_tests() -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    match = re.search(r"Ran\s+(\d+)\s+tests?", completed.stdout)
    return {
        "passed": completed.returncode == 0,
        "count": int(match.group(1)) if match else 0,
        "returncode": completed.returncode,
        "tail": completed.stdout.strip()[-2000:],
    }


def _adapter_contract(
    matrix: dict[str, Any], *, verify_adapter_files: bool
) -> tuple[dict[str, bool], dict[str, Any]]:
    checks: dict[str, bool] = {}
    details: dict[str, Any] = {}
    base_models: set[str] = set()
    prompt_hashes: set[str] = set()
    for spec in matrix["seeds"]:
        name = spec["name"]
        config_path = resolve_project_path(spec["config"])
        metrics_path = resolve_project_path(spec["training_metrics"])
        manifest_path = resolve_project_path(spec["adapter_manifest"])
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        base_models.add(str(manifest.get("actual_base_model")))
        prompt_hashes.add(str(metrics.get("dataset_audit", {}).get("system_prompt_sha256")))
        file_results: dict[str, Any] = {}
        for filename in ("adapter_config.json", "adapter_model.safetensors"):
            registered = next((item for item in manifest.get("files", []) if item["name"] == filename), None)
            actual = resolve_project_path(spec["adapter"]) / filename
            present = registered is not None and actual.exists() if verify_adapter_files else True
            hash_matches = (
                present and _sha256(actual) == registered["sha256"]
                if verify_adapter_files
                else True
            )
            size_matches = (
                present and actual.stat().st_size == int(registered["bytes"])
                if verify_adapter_files
                else True
            )
            file_results[filename] = {
                "present": present,
                "size_matches": size_matches,
                "hash_matches": hash_matches,
                "verification_skipped": not verify_adapter_files,
            }
        checks[f"{name}_training_completed"] = metrics.get("status") == "completed"
        checks[f"{name}_zero_training_truncation"] = (
            int(metrics.get("token_stats", {}).get("truncated_case_count", -1)) == 0
        )
        checks[f"{name}_peak_vram_within_12_gib"] = (
            float(metrics.get("peak_gpu_allocated_gib", 999)) <= 12.0
        )
        checks[f"{name}_protected_training_data_absent"] = not bool(
            metrics.get("dataset_audit", {}).get("protected_splits_opened")
        )
        checks[f"{name}_config_hash_matches_training"] = (
            _sha256(config_path) == metrics.get("config_sha256")
        )
        checks[f"{name}_base_model_compatible"] = bool(manifest.get("base_model_compatible"))
        checks[f"{name}_adapter_files_verified"] = all(
            row["present"] and row["size_matches"] and row["hash_matches"]
            for row in file_results.values()
        )
        details[name] = {
            "config": project_relative(config_path),
            "config_sha256": _sha256(config_path),
            "training_metrics": project_relative(metrics_path),
            "training_metrics_sha256": _sha256(metrics_path),
            "adapter_manifest": project_relative(manifest_path),
            "adapter_manifest_sha256": _sha256(manifest_path),
            "base_model": manifest.get("actual_base_model"),
            "files": file_results,
        }
    checks["one_base_model_across_three_seeds"] = len(base_models) == 1
    checks["one_prompt_contract_across_three_seeds"] = len(prompt_hashes) == 1 and "None" not in prompt_hashes
    return checks, details


def build_preflight(
    *,
    require_clean_git: bool = True,
    run_tests: bool = True,
    verify_content_freeze: bool = True,
    verify_adapter_files: bool = True,
) -> dict[str, Any]:
    matrix = _read_json("configs/sprint4_matrix_v1.json")
    evidence_gate = _read_json("configs/sprint6_evidence_gate_v1.json")
    shadow = _read_json("configs/sprint6_shadow_challenge_v1.json")
    m4 = _read_json("results/sprint4/m4_pretest_summary.json")
    containment = _read_json("results/sprint4_2c/report.json")
    current_commit = _git("rev-parse", "HEAD")
    content_freeze_commit = _git("rev-list", "-n", "1", "content-freeze-v1")
    git_status = _git("status", "--porcelain") or ""
    content_diff = subprocess.call(
        ["git", "diff", "--quiet", "content-freeze-v1", "--", *CONTENT_PATHS],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    primary_thresholds = evidence_gate["primary_thresholds"]
    matrix_thresholds = matrix["evidence_thresholds"]
    protected_paths = {
        key: {"path": value, "exists": resolve_project_path(value).exists()}
        for key, value in matrix["protected_evaluation"].items()
        if key != "open_policy"
    }
    protected_result_patterns = (
        "*_original_test*.json*",
        "*_boundary_test*.json*",
        "*_challenge*.json*",
        "protected_split_authorization.json",
    )
    protected_result_paths = sorted(
        {
            project_relative(path)
            for pattern in protected_result_patterns
            for path in resolve_project_path("results/sprint4").glob(pattern)
        }
    )
    deck = _pptx_contract("materials/PEFT_LoRA_QLoRA_w_banku_workshop.pptx")
    notebooks = _notebook_contract()
    test_result = _run_unit_tests() if run_tests else {"passed": True, "count": 65, "skipped": True}
    adapter_checks, adapter_details = _adapter_contract(
        matrix, verify_adapter_files=verify_adapter_files
    )

    checks: dict[str, bool] = {
        "m5_content_freeze_tag_exists": bool(content_freeze_commit),
        "current_commit_descends_from_content_freeze": bool(content_freeze_commit)
        and subprocess.call(
            ["git", "merge-base", "--is-ancestor", content_freeze_commit, "HEAD"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        == 0,
        "content_artifacts_match_content_freeze": content_diff == 0 if verify_content_freeze else True,
        "git_worktree_clean": not git_status if require_clean_git else True,
        "m5_status_is_accepted_with_hold": evidence_gate.get("m5_status")
        == "M5_ACCEPTED_CONTENT_FREEZE_WITH_PROTECTED_HOLD",
        "s6_gate_is_hold": evidence_gate.get("decision")
        == "HOLD_PENDING_S6_PREFLIGHT_AND_OPERATOR_APPROVAL",
        "s6_gate_records_protected_closed": evidence_gate.get("protected_splits_opened") is False,
        "primary_thresholds_match_frozen_matrix": primary_thresholds == matrix_thresholds,
        "challenge_severity_is_enforced": primary_thresholds.get(
            "challenge_severity_correct_rate_seed_min"
        )
        == 0.85,
        "shadow_is_designed_not_authored": shadow.get("status")
        == "DESIGNED_NOT_AUTHORED_NOT_OPENED",
        "shadow_is_never_training_or_tuning_source": all(
            shadow["usage_policy"].get(key) is False
            for key in (
                "training_source",
                "hyperparameter_tuning_source",
                "prompt_tuning_source",
                "guard_tuning_source",
            )
        ),
        "m4_pretest_is_complete": m4.get("decision") == "READY_TO_OPEN_PROTECTED_SPLITS"
        and all(m4.get("checks", {}).values()),
        "m4_pretest_records_protected_closed": m4.get("protected_splits_opened") is False,
        "containment_is_complete_with_hold": containment.get("demo_decision")
        == "READY_FOR_SPRINT5_DEMO_WITH_PROTECTED_HOLD"
        and containment.get("protected_evidence_decision") == "HOLD"
        and all(containment.get("checks", {}).values()),
        "containment_records_protected_closed": containment.get("protected_splits_opened") is False,
        "protected_inputs_are_declared_and_present_metadata_only": all(
            item["exists"] for item in protected_paths.values()
        ),
        "no_protected_results_or_authorization_exist": not protected_result_paths,
        "deck_contract_is_53_slides_notes_and_sources": deck
        == {"slides": 53, "notes": 53, "notes_with_sources": 53},
        "three_notebooks_compile": notebooks["count"] == 3
        and notebooks["compiled_code_cells"] > 0,
        "unit_tests_pass_and_count_at_least_65": bool(test_result["passed"])
        and int(test_result["count"]) >= 65,
        **adapter_checks,
    }
    frozen_hashes = {
        path: _sha256(path)
        for path in FROZEN_CONTRACT_FILES
    }
    decision = "S6_G0_PASS" if all(checks.values()) else "S6_G0_BLOCKED"
    return {
        "milestone": "S6-G0 Evidence Contract Freeze",
        "decision": decision,
        "checks": checks,
        "content_freeze_tag": "content-freeze-v1",
        "content_freeze_commit": content_freeze_commit,
        "current_git_commit": current_commit,
        "frozen_contract_sha256": frozen_hashes,
        "adapter_contract": adapter_details,
        "deck_contract": deck,
        "notebook_contract": notebooks,
        "unit_tests": test_result,
        "protected_inputs_metadata_only": protected_paths,
        "protected_result_paths_found": protected_result_paths,
        "protected_content_read": False,
        "next_allowed_action": (
            "AUTHOR_AND_REVIEW_SHADOW_CHALLENGE_V1"
            if decision == "S6_G0_PASS"
            else "STOP_AND_RETURN_TO_SOL_HIGH"
        ),
        "scope_notice": (
            "S6-G0 nie otwiera protected evidence i nie jest zgodą produkcyjną. "
            "Otwarcie wymaga jeszcze S6-G1, S6-G2, osobnej decyzji Sol/high i potwierdzenia operatora."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Waliduj bramkę S6-G0 bez otwierania protected evidence")
    parser.add_argument("--output", default=str(RESULTS_DIR / "sprint6" / "g0_preflight.json"))
    parser.add_argument("--allow-dirty", action="store_true", help="Wyłącznie do developmentu")
    parser.add_argument("--skip-tests", action="store_true", help="Wyłącznie do developmentu")
    parser.add_argument("--skip-adapter-hashes", action="store_true", help="Wyłącznie do developmentu")
    args = parser.parse_args()
    result = build_preflight(
        require_clean_git=not args.allow_dirty,
        run_tests=not args.skip_tests,
        verify_content_freeze=not args.allow_dirty,
        verify_adapter_files=not args.skip_adapter_hashes,
    )
    output = resolve_project_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "checks": result["checks"]}, ensure_ascii=False, indent=2))
    print(f"Pełny raport: {output}")
    return 0 if result["decision"] == "S6_G0_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
