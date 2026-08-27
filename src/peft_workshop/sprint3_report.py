from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .paths import RESULTS_DIR, resolve_project_path


STATUSES = ("PASS", "WARN", "FAIL", "INSUFFICIENT_DATA", "NOT_APPLICABLE")


def _read(path: str | Path) -> dict[str, Any]:
    return json.loads(resolve_project_path(path).read_text(encoding="utf-8"))


def _recall(report: dict[str, Any], status: str) -> float:
    return float(report["aggregate"]["per_status"][status]["recall"])


def _compact_eval(report: dict[str, Any]) -> dict[str, Any]:
    compact = {
        "count": report["aggregate"]["count"],
        "schema_valid_rate": report["aggregate"]["schema_valid_rate"],
        "status_accuracy": report["aggregate"]["status_correct_rate"],
        "macro_f1": report["aggregate"]["macro_f1"],
        "fail_false_positive_rate": report["aggregate"]["fail_false_positive_rate"],
        "recall": {status: _recall(report, status) for status in STATUSES},
        "mean_input_tokens": report["runtime"]["input_tokens"]["mean"],
        "p95_latency_s": report["runtime"]["latency_s"]["p95"],
        "peak_gpu_allocated_gib": report["runtime"]["peak_gpu_allocated_gib"]["max"],
        "truncated_rate": report["runtime"]["truncated_rate"],
    }
    if "boundary" in report:
        compact.update(report["boundary"])
    return compact


def build_summary(
    q0_original: dict[str, Any],
    q0_boundary: dict[str, Any],
    q1_original: dict[str, Any],
    q1_boundary: dict[str, Any],
    q0_training: dict[str, Any],
    q1_training: dict[str, Any],
    demo_training: dict[str, Any],
    reload_smoke: dict[str, Any],
    b3_boundary: dict[str, Any],
) -> dict[str, Any]:
    q0o, q0b = _compact_eval(q0_original), _compact_eval(q0_boundary)
    q1o, q1b = _compact_eval(q1_original), _compact_eval(q1_boundary)
    b3 = _compact_eval(b3_boundary)
    token_reduction = 1 - q1b["mean_input_tokens"] / b3["mean_input_tokens"]
    quality_alternative = q1b["macro_f1"] >= b3["macro_f1"] + 0.05 or (
        q1b["macro_f1"] >= b3["macro_f1"] - 0.02 and token_reduction >= 0.30
    )
    checks = {
        "q0_training_completed": q0_training.get("status") == "completed",
        "q1_training_completed": q1_training.get("status") == "completed",
        "q1_zero_training_truncation": q1_training.get("token_stats", {}).get("truncated_case_count") == 0,
        "q1_peak_vram_at_most_12_gib": float(q1_training.get("peak_gpu_allocated_gib", 99)) <= 12.0,
        "demo_at_most_15_minutes": float(demo_training.get("wall_clock_seconds", 9999)) <= 900,
        "adapter_reload_schema_valid": reload_smoke.get("aggregate", {}).get("schema_valid_rate") == 1.0,
        "schema_valid_at_least_98_percent": q1b["schema_valid_rate"] >= 0.98,
        "boundary_quality_or_token_efficiency": quality_alternative,
        "warn_recall_no_regression": q1b["recall"]["WARN"] >= b3["recall"]["WARN"],
        "not_applicable_recall_at_least_60_percent": q1b["recall"]["NOT_APPLICABLE"] >= 0.60,
        "fail_false_positive_rate_at_most_15_percent": q1b["fail_false_positive_rate"] <= 0.15,
        "pass_recall_regression_at_most_5pp": q1b["recall"]["PASS"] >= b3["recall"]["PASS"] - 0.05,
        "fail_recall_regression_at_most_5pp": q1b["recall"]["FAIL"] >= b3["recall"]["FAIL"] - 0.05,
    }
    return {
        "milestone": "M3 Adapter candidate",
        "decision": "PASS" if all(checks.values()) else "FAIL_REVIEW_Q1B",
        "checks": checks,
        "comparison": {
            "B3_boundary": b3,
            "Q0_original_validation": q0o,
            "Q0_boundary_validation": q0b,
            "Q1_original_validation": q1o,
            "Q1_boundary_validation": q1b,
        },
        "ablation": {
            "boundary_data_macro_f1_delta": q1b["macro_f1"] - q0b["macro_f1"],
            "boundary_data_pair_accuracy_delta": q1b["pair_accuracy"] - q0b["pair_accuracy"],
            "boundary_data_warn_recall_delta": q1b["recall"]["WARN"] - q0b["recall"]["WARN"],
            "boundary_data_not_applicable_recall_delta": q1b["recall"]["NOT_APPLICABLE"]
            - q0b["recall"]["NOT_APPLICABLE"],
            "boundary_data_insufficient_recall_delta": q1b["recall"]["INSUFFICIENT_DATA"]
            - q0b["recall"]["INSUFFICIENT_DATA"],
            "boundary_data_unsafe_pass_delta": q1b["unsafe_pass_rate"] - q0b["unsafe_pass_rate"],
            "boundary_data_unnecessary_escalation_delta": q1b["unnecessary_escalation_rate"]
            - q0b["unnecessary_escalation_rate"],
        },
        "efficiency": {
            "q1_input_token_reduction_vs_b3": token_reduction,
            "q0_training_seconds": q0_training.get("wall_clock_seconds"),
            "q1_training_seconds": q1_training.get("wall_clock_seconds"),
            "demo_training_seconds": demo_training.get("wall_clock_seconds"),
            "q0_peak_gpu_allocated_gib": q0_training.get("peak_gpu_allocated_gib"),
            "q1_peak_gpu_allocated_gib": q1_training.get("peak_gpu_allocated_gib"),
        },
        "protected_splits": {
            "original_test": "unopened",
            "boundary_test": "unopened",
            "challenge": "unopened",
        },
        "scope_notice": "Wyniki dotyczą danych syntetycznych i nie stanowią polityki produkcyjnej banku; wymagany jest human-in-the-loop.",
    }


def render_markdown(summary: dict[str, Any]) -> str:
    comparison = summary["comparison"]
    rows = []
    for name in ("B3_boundary", "Q0_boundary_validation", "Q1_boundary_validation"):
        item = comparison[name]
        rows.append(
            f"| {name} | {item['schema_valid_rate']:.1%} | {item['macro_f1']:.3f} | "
            f"{item['recall']['WARN']:.1%} | {item['recall']['NOT_APPLICABLE']:.1%} | "
            f"{item['recall']['INSUFFICIENT_DATA']:.1%} | {item['pair_accuracy']:.1%} | "
            f"{item['fail_false_positive_rate']:.1%} | {item['unsafe_pass_rate']:.1%} | "
            f"{item['unnecessary_escalation_rate']:.1%} | {item['mean_input_tokens']:.0f} |"
        )
    check_rows = [f"| {name} | {'PASS' if passed else 'FAIL'} |" for name, passed in summary["checks"].items()]
    return "\n".join(
        [
            "# Sprint 3 — wynik bramki M3",
            "",
            f"**Decyzja:** `{summary['decision']}`",
            "",
            "| Wariant | Schemat | Macro-F1 | WARN | N/A | Brak danych | Pary | FAIL FPR | Unsafe PASS | Eskalacja | Input |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            *rows,
            "",
            f"Redukcja tokenów Q1 względem B3: {summary['efficiency']['q1_input_token_reduction_vs_b3']:.1%}.",
            "",
            "## Bramka",
            "",
            "| Kryterium | Wynik |",
            "|---|---|",
            *check_rows,
            "",
            "## Ograniczenia",
            "",
            summary["scope_notice"],
            "Oryginalny test, boundary test i challenge pozostają nieotwarte do Sprintu 4.",
        ]
    ) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Zbuduj formalny raport M3 dla Q0/Q1")
    parser.add_argument("--q0-original", default="results/sprint3/q0_original_validation_metrics.json")
    parser.add_argument("--q0-boundary", default="results/sprint3/q0_boundary_validation_metrics.json")
    parser.add_argument("--q1-original", default="results/sprint3/q1_original_validation_metrics.json")
    parser.add_argument("--q1-boundary", default="results/sprint3/q1_boundary_validation_metrics.json")
    parser.add_argument("--q0-training", default="results/sprint3/q0_training_metrics.json")
    parser.add_argument("--q1-training", default="results/sprint3/q1_training_metrics.json")
    parser.add_argument("--demo-training", default="results/sprint3/q1_demo_training_metrics.json")
    parser.add_argument("--reload-smoke", default="results/sprint3/q1_demo_reload_smoke_metrics.json")
    parser.add_argument("--b3-boundary", default="results/b3_boundary_validation_metrics.json")
    parser.add_argument("--output", default=str(RESULTS_DIR / "sprint3" / "m3_summary.json"))
    parser.add_argument("--markdown", default=str(RESULTS_DIR / "sprint3" / "m3_summary.md"))
    args = parser.parse_args()
    summary = build_summary(
        *[_read(path) for path in (
            args.q0_original,
            args.q0_boundary,
            args.q1_original,
            args.q1_boundary,
            args.q0_training,
            args.q1_training,
            args.demo_training,
            args.reload_smoke,
            args.b3_boundary,
        )]
    )
    output = resolve_project_path(args.output)
    markdown = resolve_project_path(args.markdown)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown.write_text(render_markdown(summary), encoding="utf-8")
    print(json.dumps({"decision": summary["decision"], "checks": summary["checks"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

