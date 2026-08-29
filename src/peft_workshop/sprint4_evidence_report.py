from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from .paths import RESULTS_DIR, resolve_project_path
from .sprint4_report import _stats


def _read(path: str | Path) -> dict[str, Any]:
    return json.loads(resolve_project_path(path).read_text(encoding="utf-8"))


def _recall(report: dict[str, Any], status: str) -> float:
    return float(report["aggregate"]["per_status"][status]["recall"])


def build_evidence_summary(
    matrix: dict[str, Any],
    original_reports: list[dict[str, Any]],
    boundary_reports: list[dict[str, Any]],
    challenge_reports: list[dict[str, Any]],
    manual_review: dict[str, Any] | None,
) -> dict[str, Any]:
    thresholds = matrix.get("primary_thresholds") or matrix["evidence_thresholds"]
    original_macro = [float(item["aggregate"]["macro_f1"]) for item in original_reports]
    boundary_macro = [float(item["aggregate"]["macro_f1"]) for item in boundary_reports]
    boundary_warn = [_recall(item, "WARN") for item in boundary_reports]
    boundary_na = [_recall(item, "NOT_APPLICABLE") for item in boundary_reports]
    boundary_pairs = [float(item["boundary"]["pair_accuracy"]) for item in boundary_reports]
    boundary_fpr = [float(item["aggregate"]["fail_false_positive_rate"]) for item in boundary_reports]
    boundary_unsafe = [float(item["boundary"]["unsafe_pass_rate"]) for item in boundary_reports]
    evidence_schema = [
        float(item["aggregate"]["schema_valid_rate"])
        for item in [*original_reports, *boundary_reports]
    ]
    challenge_accuracy = [float(item["aggregate"]["status_correct_rate"]) for item in challenge_reports]
    challenge_schema = [float(item["aggregate"]["schema_valid_rate"]) for item in challenge_reports]
    original_test_severity = [
        float(item["aggregate"]["severity_correct_rate"]) for item in original_reports
    ]
    boundary_test_severity = [
        float(item["aggregate"]["severity_correct_rate"]) for item in boundary_reports
    ]
    test_sources = [
        float(item["aggregate"]["sources_valid_rate"])
        for item in [*original_reports, *boundary_reports]
    ]
    challenge_severity = [
        float(item["aggregate"]["severity_correct_rate"]) for item in challenge_reports
    ]
    challenge_sources = [
        float(item["aggregate"]["sources_valid_rate"]) for item in challenge_reports
    ]

    numeric_checks = {
        "exactly_three_reports_per_split": len(original_reports) == len(boundary_reports)
        == len(challenge_reports)
        == 3,
        "original_test_macro_mean": statistics.fmean(original_macro)
        >= thresholds["original_test_macro_f1_mean_min"],
        "original_test_macro_each_seed": min(original_macro)
        >= thresholds["original_test_macro_f1_seed_min"],
        "boundary_test_macro_mean": statistics.fmean(boundary_macro)
        >= thresholds["boundary_test_macro_f1_mean_min"],
        "boundary_test_macro_each_seed": min(boundary_macro)
        >= thresholds["boundary_test_macro_f1_seed_min"],
        "boundary_warn_each_seed": min(boundary_warn)
        >= thresholds["boundary_warn_recall_seed_min"],
        "boundary_not_applicable_each_seed": min(boundary_na)
        >= thresholds["boundary_not_applicable_recall_seed_min"],
        "boundary_pairs_each_seed": min(boundary_pairs)
        >= thresholds["boundary_pair_accuracy_seed_min"],
        "boundary_fail_fpr_each_seed": max(boundary_fpr)
        <= thresholds["boundary_fail_false_positive_rate_seed_max"],
        "boundary_unsafe_pass_each_seed": max(boundary_unsafe)
        <= thresholds["boundary_unsafe_pass_rate_seed_max"],
        "evidence_schema_each_seed": min(evidence_schema) >= thresholds["schema_valid_rate_seed_min"],
        "boundary_evidence_severity_each_seed": min(boundary_test_severity)
        >= thresholds["boundary_test_severity_valid_rate_seed_min"],
        "evidence_sources_each_seed": min(test_sources)
        >= thresholds["sources_valid_rate_seed_min"],
        "challenge_status_accuracy_mean": statistics.fmean(challenge_accuracy)
        >= thresholds["challenge_status_accuracy_mean_min"],
        "challenge_status_accuracy_each_seed": min(challenge_accuracy)
        >= thresholds["challenge_status_accuracy_seed_min"],
        "challenge_schema_each_seed": min(challenge_schema)
        >= thresholds["challenge_schema_valid_rate_seed_min"],
        "challenge_severity_each_seed": min(challenge_severity)
        >= thresholds["challenge_severity_correct_rate_seed_min"],
        "challenge_sources_each_seed": min(challenge_sources)
        >= thresholds["challenge_sources_valid_rate_seed_min"],
    }
    review = manual_review or {}
    review_checks = {
        "challenge_manual_review_complete": int(review.get("reviewed_case_count") or 0)
        >= thresholds["challenge_manual_review_count_min"],
        "challenge_all_seed_responses_reviewed": int(review.get("reviewed_response_count") or 0)
        >= thresholds["challenge_manual_review_response_count_min"],
        "challenge_followed_no_injection": review.get("prompt_injection_followed_count") is not None
        and int(review["prompt_injection_followed_count"])
        <= thresholds["challenge_prompt_injection_followed_max"],
        "challenge_has_no_critical_error": review.get("critical_error_count") == 0,
        "challenge_review_approved": review.get("approved_for_m4_review") is True,
    }
    if not all(numeric_checks.values()):
        decision = "FAILED_EVIDENCE_THRESHOLDS"
    elif not all(review_checks.values()):
        decision = "PENDING_MANUAL_REVIEW"
    else:
        decision = "READY_FOR_M4_SOL_REVIEW"
    return {
        "milestone": "Sprint 4 protected evidence",
        "decision": decision,
        "numeric_checks": numeric_checks,
        "manual_review_checks": review_checks,
        "thresholds": thresholds,
        "aggregate": {
            "original_test_macro_f1": _stats(original_macro),
            "boundary_test_macro_f1": _stats(boundary_macro),
            "boundary_warn_recall": _stats(boundary_warn),
            "boundary_not_applicable_recall": _stats(boundary_na),
            "boundary_pair_accuracy": _stats(boundary_pairs),
            "boundary_fail_false_positive_rate": _stats(boundary_fpr),
            "boundary_unsafe_pass_rate": _stats(boundary_unsafe),
            "challenge_status_accuracy": _stats(challenge_accuracy),
            "original_test_severity_valid_rate_report_only": _stats(original_test_severity),
            "boundary_test_severity_valid_rate": _stats(boundary_test_severity),
            "test_sources_valid_rate": _stats(test_sources),
            "challenge_severity_correct_rate": _stats(challenge_severity),
            "challenge_sources_valid_rate": _stats(challenge_sources),
        },
        "scope_notice": "Ten raport nie jest automatyczną decyzją produkcyjną ani końcowym M4 PASS.",
    }


def render_markdown(summary: dict[str, Any]) -> str:
    numeric = [
        f"| {name} | {'PASS' if value else 'FAIL'} |"
        for name, value in summary["numeric_checks"].items()
    ]
    review = [
        f"| {name} | {'PASS' if value else 'PENDING'} |"
        for name, value in summary["manual_review_checks"].items()
    ]
    return "\n".join(
        [
            "# Sprint 4 — protected evidence",
            "",
            f"**Decyzja:** `{summary['decision']}`",
            "",
            "## Kryteria ilościowe",
            "",
            "| Kryterium | Wynik |",
            "|---|---|",
            *numeric,
            "",
            "## Review challenge",
            "",
            "| Kryterium | Wynik |",
            "|---|---|",
            *review,
            "",
            summary["scope_notice"],
        ]
    ) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Agreguj protected evidence trzech seedów Sprintu 4")
    parser.add_argument("--matrix", default="configs/sprint4_matrix_v1.json")
    parser.add_argument("--manual-review", default="results/sprint4/challenge_manual_review.json")
    parser.add_argument("--output", default=str(RESULTS_DIR / "sprint4" / "m4_evidence_summary.json"))
    parser.add_argument("--markdown", default=str(RESULTS_DIR / "sprint4" / "m4_evidence_summary.md"))
    args = parser.parse_args()
    matrix = _read(args.matrix)
    original = [_read(f"results/sprint4/{item['name']}_original_test_metrics.json") for item in matrix["seeds"]]
    boundary = [_read(f"results/sprint4/{item['name']}_boundary_test_metrics.json") for item in matrix["seeds"]]
    challenge = [_read(f"results/sprint4/{item['name']}_challenge_metrics.json") for item in matrix["seeds"]]
    review_path = resolve_project_path(args.manual_review)
    manual_review = json.loads(review_path.read_text(encoding="utf-8")) if review_path.exists() else None
    summary = build_evidence_summary(matrix, original, boundary, challenge, manual_review)
    output = resolve_project_path(args.output)
    markdown = resolve_project_path(args.markdown)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown.write_text(render_markdown(summary), encoding="utf-8")
    print(json.dumps({"decision": summary["decision"]}, ensure_ascii=False, indent=2))
    return 1 if summary["decision"] == "FAILED_EVIDENCE_THRESHOLDS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
