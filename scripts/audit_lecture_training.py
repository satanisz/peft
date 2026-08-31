"""Read existing artifacts and export lecture facts; never train or infer."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results/lecture60/training_audit.json"
RUNS = (
    "results/sprint3/q0_training_metrics.json",
    "results/sprint3/q1_training_metrics.json",
    "results/sprint4/q1_seed_20260828_training_metrics.json",
    "results/sprint4/q1_seed_20260829_training_metrics.json",
    "results/sprint3/q1_demo_training_metrics.json",
)


def build_audit() -> dict:
    bindings: dict[str, str] = {}

    def digest(path: str) -> str:
        with (ROOT / path).open("rb") as stream:
            value = hashlib.file_digest(stream, "sha256").hexdigest()
        bindings[path] = value
        return value

    def read(path: str) -> dict:
        digest(path)
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    environment = read("results/sprint3/environment.json")
    runs = []
    forbidden = {
        "data/generated/dataset_v1/test.jsonl",
        "data/generated/dataset_v1/challenge.jsonl",
        "data/splits/boundary_test.jsonl",
        "data/shadow/shadow_challenge_v1.jsonl",
    }
    for path in RUNS:
        metrics = read(path)
        config = read(metrics["config_path"])
        training = config["training"]
        rows = [row for row in metrics["log_history"] if "loss" in row]
        batch = metrics["effective_batch_size"]
        count = metrics["dataset_audit"]["selected_case_count"]
        expected = training["max_steps"]
        if expected < 0:
            expected = math.ceil(count / batch) * training["epochs"]
        weights = next(f for f in metrics["adapter_files"] if f["path"] == "adapter_model.safetensors")
        adapter_path = metrics["adapter_dir"] + "/adapter_model.safetensors"
        adapter_ok = (ROOT / adapter_path).is_file() and digest(adapter_path) == weights["sha256"]
        source_paths = {s["path"] for s in metrics["dataset_audit"]["sources"]}
        checks = {
            "completed": metrics["status"] == "completed",
            "expected_steps": metrics["log_history"][-1]["step"] == expected,
            "zero_truncation": metrics["token_stats"]["truncated_case_count"] == 0,
            "finite_logged_values": bool(rows) and all(
                math.isfinite(row[key]) for row in rows for key in ("loss", "grad_norm", "learning_rate")
            ),
            "steps_strictly_increasing": all(a["step"] < b["step"] for a, b in zip(rows, rows[1:])),
            "config_hash_matches": digest(metrics["config_path"]) == metrics["config_sha256"],
            "training_source_hashes_match": all(
                digest(s["path"]) == s["sha256"] for s in metrics["dataset_audit"]["sources"]
            ),
            "no_protected_or_shadow_training": not (source_paths & forbidden)
            and metrics["dataset_audit"]["protected_splits_opened"] is False,
            "adapter_weight_hash_matches": adapter_ok,
        }
        runs.append({
            "source": path, "run_id": metrics["run_id"], "seed": training["seed"],
            "status": metrics["status"], "cases": count, "steps": metrics["log_history"][-1]["step"],
            "epochs": metrics["log_history"][-1]["epoch"], "seconds": metrics["wall_clock_seconds"],
            "train_loss_mean": metrics["training_metrics"]["train_loss"],
            "last_logged_loss": rows[-1]["loss"],
            "peak_allocated_gib": metrics["peak_gpu_allocated_gib"],
            "peak_reserved_gib": metrics["peak_gpu_reserved_gib"],
            "reserved_exceeds_reported_device_capacity": metrics["peak_gpu_reserved_gib"]
            > environment["cuda"]["total_memory_gib"],
            "trainable_parameters": metrics["model"]["trainable_parameters"],
            "adapter_weight_bytes": weights["bytes"],
            "eval_loss_logged": any("eval_loss" in r for r in metrics["log_history"]),
            "loss_curve": [{k: r[k] for k in ("step", "epoch", "loss")} for r in rows],
            "checks": checks,
        })
    m3 = read("results/sprint3/m3_summary.json")
    evidence = read("results/sprint6/evidence_summary.json")
    primary = read("results/sprint4/challenge_manual_review.json")
    shadow = read("results/sprint6/shadow_manual_response_review.json")
    closure = read("results/sprint6/protected_evidence_v1_closure.json")
    closure_ok = bool(closure["bound_sha256"]) and all(
        digest(path) == expected for path, expected in closure["bound_sha256"].items()
    )
    q1 = runs[1:4]
    checks = {"training_artifacts_verified": all(all(r["checks"].values()) for r in runs),
              "evidence_closure_hashes_unchanged": closure_ok}
    return {
        "scope": "Read-only audit for the 60-minute lecture; not a new experiment or release gate",
        "decision": "AUDIT_PASS_WITH_INTERPRETATION_CAVEATS" if all(checks.values()) else "AUDIT_BLOCKED",
        "checks": checks, "environment": environment, "runs": runs,
        "q1_three_seeds": {"count": len(q1), "mean_seconds": mean(r["seconds"] for r in q1),
                           "sum_seconds": sum(r["seconds"] for r in q1)},
        "development_comparison": m3["comparison"],
        "input_token_reduction_vs_b3": m3["efficiency"]["q1_input_token_reduction_vs_b3"],
        "evidence_decision": evidence["decision"],
        "primary_aggregate": evidence["primary_protected_evidence"]["aggregate"],
        "shadow_aggregate": evidence["shadow_risk_directed_evidence"]["aggregate"],
        "assisted_review": {
            "primary": {k: primary[k] for k in ("reviewed_case_count", "reviewed_response_count", "critical_error_count", "false_assurance_count")},
            "shadow": {k: shadow[k] for k in ("reviewed_case_count", "reviewed_response_count", "critical_error_count", "false_assurance_count")},
        },
        "caveats": [
            "No eval-loss curve: cannot establish absence of overfitting or the best stopping step.",
            "Q0/Q1 differ in data volume, optimizer steps, warmup and checkpoint cadence; not compute-matched.",
            "Allocated memory is not a minimum-GPU requirement; reserved-counter anomaly remains unexplained.",
            "Reported 1.475324 percent uses the quantized pipeline's visible-parameter denominator, not original 4B count.",
            "114.361 seconds is the current demo artifact; M3's 102.343 seconds is historical.",
            "Training wall clock surrounds trainer.train, excluding initial loading and final export.",
            "Evidence is already consumed, failed and read-only; no new run is authorized.",
        ],
        "bound_sha256": dict(sorted(bindings.items())),
    }


if __name__ == "__main__":
    report = build_audit()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"decision": report["decision"], "checks": report["checks"],
                      "runs": [{"id": r["run_id"], "checks": r["checks"]} for r in report["runs"]]}, indent=2))
    raise SystemExit(0 if all(report["checks"].values()) else 1)
