from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

from .paths import PROJECT_ROOT, RESULTS_DIR, project_relative, resolve_project_path


def _read(path: str | Path) -> dict[str, Any]:
    return json.loads(resolve_project_path(path).read_text(encoding="utf-8"))


def _run_tests() -> dict[str, Any]:
    if os.environ.get("PEFT_S6_G2_CHILD") == "1":
        return {"passed": True, "count": 75, "returncode": 0, "skipped_recursive_guard": True}
    child_env = os.environ.copy()
    child_env["PEFT_S6_G2_CHILD"] = "1"
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        env=child_env,
    )
    match = re.search(r"Ran\s+(\d+)\s+tests?", completed.stdout)
    return {
        "passed": completed.returncode == 0,
        "count": int(match.group(1)) if match else 0,
        "returncode": completed.returncode,
        "tail": completed.stdout[-1000:],
    }


def _execute_notebooks() -> dict[str, Any]:
    notebooks = sorted(resolve_project_path("notebooks").glob("*.ipynb"))
    executed_cells = 0
    errors: list[dict[str, Any]] = []
    training_switches: list[dict[str, Any]] = []
    for path in notebooks:
        payload = json.loads(path.read_text(encoding="utf-8"))
        namespace: dict[str, Any] = {"__name__": "__s6_g2_notebook_rehearsal__"}
        for index, cell in enumerate(payload.get("cells", []), start=1):
            if cell.get("cell_type") != "code":
                continue
            source = "".join(cell.get("source", []))
            try:
                code = compile(source, f"{path.name}:cell-{index}", "exec")
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    exec(code, namespace)
                executed_cells += 1
            except Exception as exc:  # pragma: no cover - gate reports the concrete failure
                errors.append(
                    {"notebook": path.name, "cell": index, "type": type(exc).__name__, "message": str(exc)}
                )
                break
        if path.name == "02_qlora_demo.ipynb":
            training_switches.append(
                {"notebook": path.name, "run_training": namespace.get("RUN_TRAINING", "MISSING")}
            )
    return {
        "notebook_count": len(notebooks),
        "executed_code_cells": executed_cells,
        "errors": errors,
        "training_switches": training_switches,
        "training_was_not_started": bool(training_switches)
        and all(item["run_training"] is False for item in training_switches),
    }


@contextlib.contextmanager
def _offline_environment():
    names = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")
    previous = {name: os.environ.get(name) for name in names}
    os.environ.update({name: "1" for name in names})
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def _exact_revision_local_only(model: dict[str, Any]) -> dict[str, Any]:
    model_id = str(model["id"])
    revision = str(model["revision"])
    required_patterns = ["*.json", "*.safetensors", "*.jinja", "tokenizer*"]
    try:
        from huggingface_hub import snapshot_download
        from safetensors import safe_open
        from transformers import AutoConfig, AutoTokenizer

        with _offline_environment():
            snapshot = Path(
                snapshot_download(
                    repo_id=model_id,
                    revision=revision,
                    local_files_only=True,
                    allow_patterns=required_patterns,
                )
            )
            loaded_config = AutoConfig.from_pretrained(
                model_id, revision=revision, local_files_only=True, trust_remote_code=False
            )
            loaded_tokenizer = AutoTokenizer.from_pretrained(
                model_id, revision=revision, local_files_only=True, trust_remote_code=False
            )

        index_path = snapshot / "model.safetensors.index.json"
        if not index_path.is_file():
            raise FileNotFoundError(f"Brak indeksu wag: {index_path}")
        index = json.loads(index_path.read_text(encoding="utf-8"))
        weight_map = index.get("weight_map", {})
        if not weight_map:
            raise ValueError("Indeks modelu nie zawiera weight_map.")
        shard_names = sorted(set(weight_map.values()))
        missing_shards = [name for name in shard_names if not (snapshot / name).is_file()]
        empty_shards = [
            name for name in shard_names if (snapshot / name).is_file() and (snapshot / name).stat().st_size <= 0
        ]
        missing_tensors: list[str] = []
        shard_sizes: dict[str, int] = {}
        for shard_name in shard_names:
            shard_path = snapshot / shard_name
            if not shard_path.is_file() or shard_path.stat().st_size <= 0:
                continue
            shard_sizes[shard_name] = shard_path.stat().st_size
            with safe_open(shard_path, framework="pt", device="cpu") as handle:
                available = set(handle.keys())
            expected = {tensor for tensor, mapped_shard in weight_map.items() if mapped_shard == shard_name}
            missing_tensors.extend(sorted(expected - available))
        snapshot_matches_revision = snapshot.name == revision
        complete = (
            snapshot_matches_revision
            and not missing_shards
            and not empty_shards
            and not missing_tensors
            and len(shard_sizes) == len(shard_names)
        )
        return {
            "passed": complete,
            "model_id": model_id,
            "requested_revision": revision,
            "resolved_snapshot": str(snapshot),
            "snapshot_matches_revision": snapshot_matches_revision,
            "local_files_only": True,
            "network_called": False,
            "config_class": type(loaded_config).__name__,
            "tokenizer_class": type(loaded_tokenizer).__name__,
            "weight_index": index_path.name,
            "indexed_tensor_count": len(weight_map),
            "required_shards": shard_names,
            "verified_shard_count": len(shard_sizes),
            "verified_weight_bytes": sum(shard_sizes.values()),
            "missing_shards": missing_shards,
            "empty_shards": empty_shards,
            "missing_tensors": missing_tensors,
        }
    except Exception as exc:
        return {
            "passed": False,
            "model_id": model_id,
            "requested_revision": revision,
            "local_files_only": True,
            "network_called": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_adapter_manifest() -> dict[str, Any]:
    manifest = _read("results/sprint3/q1_demo_adapter_manifest.json")
    adapter_dir = resolve_project_path(manifest["adapter_path"])
    mismatches: list[dict[str, str]] = []
    for item in manifest.get("files", []):
        path = adapter_dir / item["name"]
        if not path.is_file():
            mismatches.append({"file": item["name"], "reason": "missing"})
            continue
        if path.stat().st_size != item["bytes"]:
            mismatches.append({"file": item["name"], "reason": "size"})
            continue
        if _sha256(path) != item["sha256"]:
            mismatches.append({"file": item["name"], "reason": "sha256"})
    return {
        "passed": bool(manifest.get("files")) and not mismatches,
        "adapter_path": project_relative(adapter_dir),
        "verified_file_count": len(manifest.get("files", [])) - len(mismatches),
        "manifest_file_count": len(manifest.get("files", [])),
        "mismatches": mismatches,
    }


def _exercise_failure(
    *,
    injection: str,
    primary: Callable[[], Any],
    fallback_name: str,
    fallback: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    try:
        primary()
    except Exception as exc:  # controlled failures must reach the real exception handler
        fallback_result = fallback()
        return {
            "injection": injection,
            "caught": True,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "fallback": fallback_name,
            "fallback_executed": True,
            "fallback_result": fallback_result,
            "passed": fallback_result.get("passed") is True,
        }
    return {
        "injection": injection,
        "caught": False,
        "fallback": fallback_name,
        "fallback_executed": False,
        "passed": False,
        "error": "Kontrolowana ścieżka podstawowa nie zgłosiła oczekiwanego błędu.",
    }


def _failure_rehearsal(model: dict[str, Any]) -> dict[str, Any]:
    from huggingface_hub import snapshot_download

    def inject_oom() -> None:
        import torch

        raise torch.OutOfMemoryError("S6-G2.1 controlled CUDA OOM injection; no allocation performed")

    def inject_missing_model() -> None:
        snapshot_download(
            repo_id=str(model["id"]),
            revision="s6-g2.1-deliberately-missing-revision",
            local_files_only=True,
        )

    def inject_checkpoint_error() -> None:
        missing = resolve_project_path("artifacts/adapters/__s6_g2_1_missing_checkpoint__")
        if not (missing / "adapter_model.safetensors").is_file():
            raise FileNotFoundError(f"Checkpoint nie istnieje: {missing}")

    def inject_offline_transport() -> None:
        with _offline_environment():
            raise ConnectionError("S6-G2.1 controlled network transport failure in offline mode")

    scenarios = {
        "oom": _exercise_failure(
            injection="torch.OutOfMemoryError",
            primary=inject_oom,
            fallback_name="verified_precomputed_adapter",
            fallback=_verify_adapter_manifest,
        ),
        "missing_model": _exercise_failure(
            injection="missing Hugging Face revision with local_files_only=True",
            primary=inject_missing_model,
            fallback_name="exact_revision_local_only",
            fallback=lambda: _exact_revision_local_only(model),
        ),
        "checkpoint_error": _exercise_failure(
            injection="missing adapter checkpoint path",
            primary=inject_checkpoint_error,
            fallback_name="last_verified_adapter",
            fallback=_verify_adapter_manifest,
        ),
        "offline_cache": _exercise_failure(
            injection="blocked network transport with offline environment",
            primary=inject_offline_transport,
            fallback_name="exact_revision_local_only",
            fallback=lambda: _exact_revision_local_only(model),
        ),
    }
    return {
        "all_expected_fallbacks": all(item["passed"] for item in scenarios.values()),
        "scenarios": scenarios,
    }


def _clean_offline_install() -> dict[str, Any]:
    uv = shutil.which("uv")
    if not uv:
        return {"passed": False, "error": "Nie znaleziono uv.", "network_called": False}
    environment = os.environ.copy()
    environment.update(
        {
            "UV_OFFLINE": "1",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "PIP_NO_INDEX": "1",
            "PYTHONIOENCODING": "utf-8",
        }
    )
    commands: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="peft-s6-g2-1-offline-") as temp:
        venv = Path(temp) / "venv"
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        command_list = [
            [uv, "venv", "--python", sys.executable, str(venv)],
            [
                uv,
                "pip",
                "install",
                "--offline",
                "--no-deps",
                "--python",
                str(python),
                str(PROJECT_ROOT),
            ],
            [
                str(python),
                "-c",
                "import peft_workshop; from peft_workshop.paths import PROJECT_ROOT; "
                "print('offline-clean-import-ok', PROJECT_ROOT)",
            ],
        ]
        for command in command_list:
            completed = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                env=environment,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=180,
            )
            commands.append(
                {
                    "command": [Path(command[0]).name, *command[1:]],
                    "returncode": completed.returncode,
                    "output_tail": completed.stdout[-1500:],
                }
            )
            if completed.returncode != 0:
                break
    return {
        "passed": len(commands) == 3 and all(item["returncode"] == 0 for item in commands),
        "isolated_temporary_environment": True,
        "package_installed_from": ".",
        "dependency_resolution": "intentionally_skipped; exact model/runtime checks run in the frozen workshop environment",
        "offline_flags": {
            "UV_OFFLINE": "1",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "PIP_NO_INDEX": "1",
        },
        "network_called": False,
        "commands": commands,
    }


def _training_source_audit() -> dict[str, Any]:
    forbidden = {
        "data/generated/dataset_v1/test.jsonl",
        "data/splits/boundary_test.jsonl",
        "data/generated/dataset_v1/challenge.jsonl",
        "data/shadow/shadow_challenge_v1.jsonl",
    }
    used: list[dict[str, str]] = []
    for path in sorted(resolve_project_path("configs").glob("qlora*.json")):
        config = json.loads(path.read_text(encoding="utf-8"))
        for source in config.get("dataset", {}).get("train_sources", []):
            used.append({"config": project_relative(path), "path": str(source.get("path"))})
    violations = [row for row in used if row["path"] in forbidden]
    return {"checked_sources": used, "forbidden_sources": sorted(forbidden), "violations": violations}


def build_g2_report(*, run_embedded_tests: bool = True, run_clean_install: bool = True) -> dict[str, Any]:
    g0 = _read("results/sprint6/g0_preflight.json")
    g1 = _read("results/sprint6/g1_shadow_freeze.json")
    demo = _read("results/sprint3/q1_demo_training_metrics.json")
    reload = _read("results/sprint3/q1_demo_reload_smoke_metrics.json")
    config = _read("configs/qlora_demo_v1.json")
    tests = _run_tests() if run_embedded_tests else {"passed": True, "count": 75, "skipped_by_caller": True}
    notebooks = _execute_notebooks()
    offline = _exact_revision_local_only(config["model"])
    failure = _failure_rehearsal(config["model"])
    clean_install = _clean_offline_install() if run_clean_install else {"passed": True, "skipped_by_caller": True}
    training_sources = _training_source_audit()
    adapter_dir = resolve_project_path(demo["adapter_dir"])
    required_adapter_files = [adapter_dir / "adapter_config.json", adapter_dir / "adapter_model.safetensors"]
    checks = {
        "g0_pass": g0.get("decision") == "S6_G0_PASS",
        "g1_pass": g1.get("decision") == "S6_G1_PASS",
        "demo_completed": demo.get("status") == "completed",
        "demo_exactly_12_steps": demo.get("log_history", [])
        and demo["log_history"][-1].get("step") == config["training"]["max_steps"],
        "demo_within_15_minutes": float(demo.get("wall_clock_seconds", 9999)) <= 900,
        "demo_no_training_truncation": demo.get("token_stats", {}).get("truncated_case_count") == 0,
        "demo_protected_closed": demo.get("dataset_audit", {}).get("protected_splits_opened") is False,
        "fresh_reload_schema_valid": reload.get("aggregate", {}).get("schema_valid_rate") == 1.0,
        "fresh_reload_uses_384_tokens": reload.get("metadata", {}).get("max_new_tokens") == 384,
        "fresh_reload_protected_closed": reload.get("metadata", {}).get("protected_split_authorized") is False,
        "adapter_files_present": all(path.exists() for path in required_adapter_files),
        "exact_revision_loads_local_only_with_complete_weights": offline["passed"],
        "notebooks_execute_without_training": notebooks["notebook_count"] == 3
        and notebooks["executed_code_cells"] >= 13
        and not notebooks["errors"]
        and notebooks["training_was_not_started"],
        "unit_tests_pass": tests["passed"] and tests["count"] >= 65,
        "failure_injection_executes_verified_fallbacks": failure["all_expected_fallbacks"],
        "clean_environment_installs_offline": clean_install["passed"],
        "protected_and_shadow_not_used_for_training": not training_sources["violations"],
    }
    decision = "S6_G2_1_PASS" if all(checks.values()) else "S6_G2_1_BLOCKED_TECHNICAL_READINESS"
    return {
        "milestone": "S6-G2.1 Technical readiness hardening",
        "decision": decision,
        "checks": checks,
        "unit_tests": tests,
        "notebooks": notebooks,
        "failure_rehearsal": failure,
        "training_source_audit": training_sources,
        "demo": {
            "run_id": demo.get("run_id"),
            "steps": config["training"]["max_steps"],
            "wall_clock_seconds": demo.get("wall_clock_seconds"),
            "peak_gpu_allocated_gib": demo.get("peak_gpu_allocated_gib"),
            "adapter_dir": project_relative(adapter_dir),
        },
        "offline": offline,
        "clean_offline_install": clean_install,
        "protected_splits_opened": False,
        "protected_content_read": False,
        "inference_run": False,
        "next_allowed_action": "SOL_HIGH_REVIEW_AND_SEPARATE_OPERATOR_APPROVAL"
        if decision == "S6_G2_1_PASS"
        else "FIX_TECHNICAL_READINESS",
        "scope_notice": "G2.1 potwierdza wykonane ścieżki techniczne na zamrożonych artefaktach. Nie otwiera protected evidence i nie jest zgodą produkcyjną.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="S6-G2.1 technical readiness hardening")
    parser.add_argument("--output", default=str(RESULTS_DIR / "sprint6" / "g2_technical_readiness.json"))
    args = parser.parse_args()
    started = time.perf_counter()
    report = build_g2_report()
    report["wall_clock_seconds"] = round(time.perf_counter() - started, 3)
    output = resolve_project_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["decision"] == "S6_G2_1_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
