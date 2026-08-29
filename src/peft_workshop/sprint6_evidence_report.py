from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from .cases import load_cases
from .paths import RESULTS_DIR, resolve_project_path
from .sprint4_evidence_report import build_evidence_summary


STATUSES = ("PASS", "WARN", "FAIL", "INSUFFICIENT_DATA", "NOT_APPLICABLE")


def _read(path: str | Path) -> dict[str, Any]:
    return json.loads(resolve_project_path(path).read_text(encoding="utf-8"))


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    with resolve_project_path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def _stats(values: list[float]) -> dict[str, float]:
    return {"mean": statistics.fmean(values), "min": min(values), "max": max(values), "range": max(values) - min(values)}


def _unsafe_pass_rate(report: dict[str, Any]) -> float:
    cases = [row for row in report["cases"] if row.get("expected_status") in {"WARN", "FAIL", "INSUFFICIENT_DATA"}]
    return sum(row.get("predicted_status") == "PASS" for row in cases) / len(cases) if cases else 0.0


def _guard_metrics(
    reports: list[dict[str, Any]], guarded: list[list[dict[str, Any]]]
) -> dict[str, Any]:
    false_block_rates: list[float] = []
    detection_rates: list[float] = []
    blocked_accepted: list[int] = []
    for report, records in zip(reports, guarded, strict=True):
        scores = {row["case_id"]: row for row in report["cases"]}
        eligible = 0
        false_blocks = 0
        mismatch_count = 0
        mismatch_detected = 0
        accepted_blocked = 0
        for record in records:
            score = scores[record["case_id"]]
            raw_correct = all(
                score.get(field) is True
                for field in ("schema_valid", "sources_valid", "status_correct", "severity_correct", "human_review_correct")
            )
            if raw_correct:
                eligible += 1
                false_blocks += record["guard"]["decision"] == "BLOCK_FOR_HUMAN_REVIEW"
            issue_codes = {item["code"] for item in record["guard"].get("issues", [])}
            if "DETERMINISTIC_DECISION_MISMATCH" in issue_codes:
                mismatch_count += 1
                mismatch_detected += record["guard"]["decision"] == "BLOCK_FOR_HUMAN_REVIEW"
            accepted_blocked += (
                record["guard"]["decision"] == "BLOCK_FOR_HUMAN_REVIEW"
                and record["guard"].get("guarded_output") is not None
            )
        false_block_rates.append(false_blocks / eligible if eligible else 0.0)
        detection_rates.append(mismatch_detected / mismatch_count if mismatch_count else 1.0)
        blocked_accepted.append(accepted_blocked)
    return {
        "false_block_rate": false_block_rates,
        "deterministic_mismatch_detection_rate": detection_rates,
        "blocked_output_accepted_count": blocked_accepted,
    }


def build_shadow_summary(
    thresholds: dict[str, Any],
    reports: list[dict[str, Any]],
    guarded: list[list[dict[str, Any]]],
    manual_review: dict[str, Any] | None,
) -> dict[str, Any]:
    macro = [float(row["aggregate"]["macro_f1"]) for row in reports]
    recall = {
        status: [float(row["aggregate"]["per_status"][status]["recall"]) for row in reports]
        for status in ("WARN", "NOT_APPLICABLE", "INSUFFICIENT_DATA")
    }
    unsafe = [_unsafe_pass_rate(row) for row in reports]
    schema = [float(row["aggregate"]["schema_valid_rate"]) for row in reports]
    severity = [float(row["aggregate"]["severity_correct_rate"]) for row in reports]
    sources = [float(row["aggregate"]["sources_valid_rate"]) for row in reports]
    guard = _guard_metrics(reports, guarded)
    numeric_checks = {
        "exactly_three_shadow_reports": len(reports) == len(guarded) == 3,
        "exactly_50_cases_each_seed": all(row["aggregate"]["count"] == thresholds["case_count"] for row in reports),
        "macro_f1_mean": statistics.fmean(macro) >= thresholds["macro_f1_mean_min"],
        "macro_f1_each_seed": min(macro) >= thresholds["macro_f1_seed_min"],
        "macro_f1_seed_range": max(macro) - min(macro) <= thresholds["macro_f1_seed_range_max"],
        "warn_recall_each_seed": min(recall["WARN"]) >= thresholds["warn_recall_seed_min"],
        "not_applicable_recall_each_seed": min(recall["NOT_APPLICABLE"]) >= thresholds["not_applicable_recall_seed_min"],
        "insufficient_data_recall_each_seed": min(recall["INSUFFICIENT_DATA"]) >= thresholds["insufficient_data_recall_seed_min"],
        "unsafe_pass_each_seed": max(unsafe) <= thresholds["unsafe_pass_rate_seed_max"],
        "schema_each_seed": min(schema) >= thresholds["schema_valid_rate_seed_min"],
        "severity_each_seed": min(severity) >= thresholds["severity_correct_rate_seed_min"],
        "sources_each_seed": min(sources) >= thresholds["sources_valid_rate_seed_min"],
        "deterministic_mismatch_detection_each_seed": min(guard["deterministic_mismatch_detection_rate"]) >= thresholds["deterministic_mismatch_detection_rate_min"],
        "guard_false_block_each_seed": max(guard["false_block_rate"]) <= thresholds["guard_false_block_rate_max"],
        "guard_never_accepts_blocked_output": sum(guard["blocked_output_accepted_count"]) <= thresholds["guard_blocked_output_accepted_max"],
    }
    review = manual_review or {}
    review_checks = {
        "manual_case_review_complete": int(review.get("reviewed_case_count") or 0) >= thresholds["manual_case_review_min"],
        "manual_response_review_complete": int(review.get("reviewed_response_count") or 0) >= thresholds["manual_response_review_min"],
        "prompt_injection_followed_zero": review.get("prompt_injection_followed_count") is not None
        and int(review["prompt_injection_followed_count"]) <= thresholds["prompt_injection_followed_max"],
        "critical_errors_zero": review.get("critical_error_count") == 0,
        "shadow_review_approved": review.get("approved_for_m6_review") is True,
    }
    return {
        "decision": "FAILED_SHADOW_THRESHOLDS" if not all(numeric_checks.values()) else "PENDING_MANUAL_REVIEW" if not all(review_checks.values()) else "READY_FOR_M6_SOL_REVIEW",
        "numeric_checks": numeric_checks,
        "manual_review_checks": review_checks,
        "aggregate": {
            "macro_f1": _stats(macro),
            "warn_recall": _stats(recall["WARN"]),
            "not_applicable_recall": _stats(recall["NOT_APPLICABLE"]),
            "insufficient_data_recall": _stats(recall["INSUFFICIENT_DATA"]),
            "unsafe_pass_rate": _stats(unsafe),
            "schema_valid_rate": _stats(schema),
            "severity_correct_rate": _stats(severity),
            "sources_valid_rate": _stats(sources),
            "guard_false_block_rate": _stats(guard["false_block_rate"]),
            "deterministic_mismatch_detection_rate": _stats(guard["deterministic_mismatch_detection_rate"]),
            "blocked_output_accepted_count": sum(guard["blocked_output_accepted_count"]),
        },
    }


def build_combined_summary(
    evidence_gate: dict[str, Any],
    primary: dict[str, Any],
    shadow: dict[str, Any],
) -> dict[str, Any]:
    if primary["decision"] == "FAILED_EVIDENCE_THRESHOLDS" or shadow["decision"] == "FAILED_SHADOW_THRESHOLDS":
        decision = "FAILED_EVIDENCE_THRESHOLDS"
    elif primary["decision"] == "PENDING_MANUAL_REVIEW" or shadow["decision"] == "PENDING_MANUAL_REVIEW":
        decision = "PENDING_MANUAL_REVIEW"
    else:
        decision = "READY_FOR_M6_SOL_REVIEW"
    return {
        "milestone": "Sprint 6 primary and shadow evidence",
        "decision": decision,
        "primary_protected_evidence": primary,
        "shadow_risk_directed_evidence": shadow,
        "methodology": evidence_gate["methodology"],
        "protected_splits_opened": True,
        "retuning_after_evidence": False,
        "scope_notice": "Primary i risk-directed shadow są raportowane oddzielnie. Wynik nie jest zgodą produkcyjną.",
    }


def _write_shadow_review_template(path: Path, seed_names: list[str]) -> None:
    if path.exists():
        return
    cases = load_cases(resolve_project_path("data/shadow/shadow_challenge_v1.jsonl"))
    payload = {
        "review_status": "PENDING_HUMAN_REVIEW",
        "reviewer": None,
        "reviewed_at": None,
        "responses": [
            {"seed": seed, "case_id": case["case_id"], "decision": "PENDING", "prompt_injection_followed": None, "critical_error": None, "notes": ""}
            for seed in seed_names for case in cases
        ],
        "reviewed_case_count": 50,
        "reviewed_response_count": 0,
        "prompt_injection_followed_count": None,
        "critical_error_count": None,
        "approved_for_m6_review": False,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate Sprint 6 primary and shadow evidence without retuning.")
    parser.add_argument("--primary-review", default="results/sprint4/challenge_manual_review.json")
    parser.add_argument("--shadow-review", default="results/sprint6/shadow_manual_response_review.json")
    parser.add_argument("--output", default=str(RESULTS_DIR / "sprint6" / "evidence_summary.json"))
    args = parser.parse_args()
    matrix = _read("configs/sprint4_matrix_v1.json")
    gate = _read("configs/sprint6_evidence_gate_v1.json")
    seeds = [item["name"] for item in matrix["seeds"]]
    primary_reports = {
        split: [_read(f"results/sprint4/{seed}_{split}_metrics.json") for seed in seeds]
        for split in ("original_test", "boundary_test", "challenge")
    }
    primary_review_path = resolve_project_path(args.primary_review)
    primary = build_evidence_summary(
        gate,
        primary_reports["original_test"],
        primary_reports["boundary_test"],
        primary_reports["challenge"],
        json.loads(primary_review_path.read_text(encoding="utf-8")) if primary_review_path.exists() else None,
    )
    shadow_reports = [_read(f"results/sprint6/{seed}_shadow_challenge_metrics.json") for seed in seeds]
    guarded = [_read_jsonl(f"results/sprint6/{seed}_shadow_challenge_guarded.jsonl") for seed in seeds]
    shadow_review_path = resolve_project_path(args.shadow_review)
    _write_shadow_review_template(shadow_review_path, seeds)
    shadow_review = json.loads(shadow_review_path.read_text(encoding="utf-8"))
    shadow = build_shadow_summary(gate["shadow_thresholds"], shadow_reports, guarded, shadow_review)
    summary = build_combined_summary(gate, primary, shadow)
    output = resolve_project_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": summary["decision"], "primary": primary["decision"], "shadow": shadow["decision"]}, ensure_ascii=False, indent=2))
    return 1 if summary["decision"] == "FAILED_EVIDENCE_THRESHOLDS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
