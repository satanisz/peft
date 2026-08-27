from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .paths import RESULTS_DIR, resolve_project_path


def _read(path: str | Path) -> dict[str, Any]:
    return json.loads(resolve_project_path(path).read_text(encoding="utf-8"))


def build_gate(
    config: dict[str, Any],
    metrics: list[dict[str, Any]] | None,
    guard_reports: list[dict[str, Any]] | None,
    review: dict[str, Any],
) -> dict[str, Any]:
    thresholds = config["diagnostic_thresholds"]
    metrics = metrics or []
    guard_reports = guard_reports or []
    numeric_checks: dict[str, bool] = {
        "three_seed_reports_present": len(metrics) == 3 and len(guard_reports) == 3,
    }
    if len(metrics) == 3 and len(guard_reports) == 3:
        numeric_checks.update(
            {
                "case_count_each_seed": all(item["aggregate"]["count"] == thresholds["case_count"] for item in metrics),
                "schema_each_seed": min(item["aggregate"]["schema_valid_rate"] for item in metrics) >= thresholds["schema_valid_rate_min"],
                "macro_f1_each_seed": min(item["aggregate"]["macro_f1"] for item in metrics) >= thresholds["status_macro_f1_min"],
                "sources_each_seed": min(item["aggregate"]["sources_valid_rate"] for item in metrics) >= thresholds["sources_valid_rate_min"],
                "severity_each_seed": min(item["aggregate"]["severity_correct_rate"] for item in metrics) >= thresholds["severity_valid_rate_min"],
                "guard_never_accepts_blocked_output": all(item.get("blocked_output_accepted_count", 0) <= thresholds["guard_blocked_output_accepted_max"] for item in guard_reports),
            }
        )
    review_cases = review.get("cases", [])
    summary = review.get("summary", {})
    review_checks = {
        "reviewer_is_independent": review.get("reviewer_independent_from_authoring") is True,
        "all_cases_reviewed": int(summary.get("reviewed_case_count") or 0) >= thresholds["independent_review_case_count_min"],
        "all_cases_approved": int(summary.get("approved_case_count") or 0) == thresholds["independent_review_case_count_min"],
        "no_critical_errors": summary.get("critical_error_count") == thresholds["independent_review_critical_errors_max"],
        "no_injection_followed": summary.get("prompt_injection_followed_count") == thresholds["prompt_injection_followed_max"],
        "case_register_complete": len(review_cases) == thresholds["case_count"],
        "approved_for_q2_validation": summary.get("approved_for_q2_validation") is True,
    }
    if not all(review_checks.values()):
        decision = "HOLD_PENDING_INDEPENDENT_REVIEW"
    elif not numeric_checks["three_seed_reports_present"]:
        decision = "HOLD_MISSING_DIAGNOSTIC_RESULTS"
    elif not all(numeric_checks.values()):
        decision = "HOLD_DIAGNOSTIC_THRESHOLDS"
    else:
        decision = "READY_FOR_SOL_HIGH_APPROVAL_REVIEW"
    return {
        "milestone": "Sprint 4.2A gate",
        "decision": decision,
        "numeric_checks": numeric_checks,
        "review_checks": review_checks,
        "protected_splits_opened": False,
        "automatic_approval": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Bramka Sprintu 4.2A")
    parser.add_argument("--config", default="configs/q2_source_guard_v1.json")
    parser.add_argument("--review", default="data/reviews/diagnostic_set_v1_review.json")
    parser.add_argument("--output", default=str(RESULTS_DIR / "sprint4_2a" / "gate.json"))
    args = parser.parse_args()
    config = _read(args.config)
    review = _read(args.review)
    matrix = _read("configs/sprint4_matrix_v1.json")
    metric_paths = [resolve_project_path(f"results/sprint4_2a/{item['name']}_diagnostic_metrics.json") for item in matrix["seeds"]]
    guard_paths = [resolve_project_path(f"results/sprint4_2a/{item['name']}_diagnostic_guard_report.json") for item in matrix["seeds"]]
    metrics = [_read(path) for path in metric_paths] if all(path.exists() for path in metric_paths) else None
    guard_reports = [_read(path) for path in guard_paths] if all(path.exists() for path in guard_paths) else None
    gate = build_gate(config, metrics, guard_reports, review)
    output = resolve_project_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(gate, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(gate, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
