from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from .paths import RESULTS_DIR, resolve_project_path


def _read(path: str | Path) -> dict[str, Any]:
    return json.loads(resolve_project_path(path).read_text(encoding="utf-8"))


def _stats(values: list[float]) -> dict[str, float]:
    return {
        "mean": statistics.fmean(values),
        "min": min(values),
        "max": max(values),
        "range": max(values) - min(values),
        "population_std": statistics.pstdev(values),
    }


def _recall(report: dict[str, Any], status: str) -> float:
    return float(report["aggregate"]["per_status"][status]["recall"])


def build_pretest_summary(
    matrix: dict[str, Any],
    training_reports: list[dict[str, Any]],
    original_reports: list[dict[str, Any]],
    boundary_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    thresholds = matrix["pretest_thresholds"]
    original_macro = [float(item["aggregate"]["macro_f1"]) for item in original_reports]
    boundary_macro = [float(item["aggregate"]["macro_f1"]) for item in boundary_reports]
    schema = [
        float(item["aggregate"]["schema_valid_rate"])
        for item in [*original_reports, *boundary_reports]
    ]
    original_severity = [
        float(item["aggregate"]["severity_correct_rate"]) for item in original_reports
    ]
    boundary_severity = [
        float(item["aggregate"]["severity_correct_rate"]) for item in boundary_reports
    ]
    original_sources = [
        float(item["aggregate"]["sources_valid_rate"]) for item in original_reports
    ]
    boundary_sources = [
        float(item["aggregate"]["sources_valid_rate"]) for item in boundary_reports
    ]
    warn = [_recall(item, "WARN") for item in boundary_reports]
    not_applicable = [_recall(item, "NOT_APPLICABLE") for item in boundary_reports]
    pair_accuracy = [float(item["boundary"]["pair_accuracy"]) for item in boundary_reports]
    fail_fpr = [float(item["aggregate"]["fail_false_positive_rate"]) for item in boundary_reports]
    unsafe_pass = [float(item["boundary"]["unsafe_pass_rate"]) for item in boundary_reports]
    peak_vram = [float(item.get("peak_gpu_allocated_gib", 99)) for item in training_reports]
    truncation = [int(item.get("token_stats", {}).get("truncated_case_count", 999)) for item in training_reports]

    checks = {
        "exactly_three_complete_training_runs": len(training_reports) == 3
        and all(item.get("status") == "completed" for item in training_reports),
        "zero_training_truncation": max(truncation) <= thresholds["training_truncated_cases_max"],
        "peak_vram_within_budget": max(peak_vram) <= thresholds["training_peak_vram_max_gib"],
        "original_macro_mean": statistics.fmean(original_macro) >= thresholds["original_macro_f1_mean_min"],
        "original_macro_each_seed": min(original_macro) >= thresholds["original_macro_f1_seed_min"],
        "boundary_macro_mean": statistics.fmean(boundary_macro) >= thresholds["boundary_macro_f1_mean_min"],
        "boundary_macro_each_seed": min(boundary_macro) >= thresholds["boundary_macro_f1_seed_min"],
        "boundary_macro_seed_range": max(boundary_macro) - min(boundary_macro)
        <= thresholds["boundary_macro_f1_range_max"],
        "schema_each_seed": min(schema) >= thresholds["schema_valid_rate_seed_min"],
        "boundary_severity_each_seed": min(boundary_severity)
        >= thresholds["boundary_severity_valid_rate_seed_min"],
        "sources_each_seed": min([*original_sources, *boundary_sources])
        >= thresholds["sources_valid_rate_seed_min"],
        "warn_recall_each_seed": min(warn) >= thresholds["warn_recall_seed_min"],
        "not_applicable_recall_each_seed": min(not_applicable)
        >= thresholds["not_applicable_recall_seed_min"],
        "pair_accuracy_each_seed": min(pair_accuracy) >= thresholds["pair_accuracy_seed_min"],
        "fail_fpr_each_seed": max(fail_fpr) <= thresholds["fail_false_positive_rate_seed_max"],
        "unsafe_pass_each_seed": max(unsafe_pass) <= thresholds["unsafe_pass_rate_seed_max"],
    }
    seed_rows = []
    for spec, training, original, boundary in zip(
        matrix["seeds"], training_reports, original_reports, boundary_reports, strict=True
    ):
        seed_rows.append(
            {
                "name": spec["name"],
                "seed": spec["seed"],
                "training_seconds": training.get("wall_clock_seconds"),
                "peak_gpu_allocated_gib": training.get("peak_gpu_allocated_gib"),
                "original_macro_f1": original["aggregate"]["macro_f1"],
                "boundary_macro_f1": boundary["aggregate"]["macro_f1"],
                "original_severity_valid_rate": original["aggregate"]["severity_correct_rate"],
                "boundary_severity_valid_rate": boundary["aggregate"]["severity_correct_rate"],
                "original_sources_valid_rate": original["aggregate"]["sources_valid_rate"],
                "boundary_sources_valid_rate": boundary["aggregate"]["sources_valid_rate"],
                "warn_recall": _recall(boundary, "WARN"),
                "not_applicable_recall": _recall(boundary, "NOT_APPLICABLE"),
                "pair_accuracy": boundary["boundary"]["pair_accuracy"],
                "fail_false_positive_rate": boundary["aggregate"]["fail_false_positive_rate"],
                "unsafe_pass_rate": boundary["boundary"]["unsafe_pass_rate"],
            }
        )
    return {
        "milestone": "Sprint 4 pre-test freeze",
        "decision": "READY_TO_OPEN_PROTECTED_SPLITS"
        if all(checks.values())
        else "STOP_AND_RETURN_TO_SOL_HIGH",
        "checks": checks,
        "thresholds": thresholds,
        "seed_results": seed_rows,
        "aggregate": {
            "original_macro_f1": _stats(original_macro),
            "boundary_macro_f1": _stats(boundary_macro),
            "original_severity_valid_rate": _stats(original_severity),
            "boundary_severity_valid_rate": _stats(boundary_severity),
            "original_sources_valid_rate": _stats(original_sources),
            "boundary_sources_valid_rate": _stats(boundary_sources),
            "warn_recall": _stats(warn),
            "not_applicable_recall": _stats(not_applicable),
            "pair_accuracy": _stats(pair_accuracy),
            "fail_false_positive_rate": _stats(fail_fpr),
            "unsafe_pass_rate": _stats(unsafe_pass),
            "training_peak_vram_gib": _stats(peak_vram),
        },
        "protected_splits_opened": False,
        "automated_gate_only": True,
        "analytical_gate_path": matrix["policy"].get("analytical_gate_path"),
        "policy": matrix["policy"],
    }


def render_markdown(summary: dict[str, Any]) -> str:
    rows = [
        "| Seed | Oryginalny F1 | Boundary F1 | Severity orig. | Sources boundary | WARN | N/A | Pary | FAIL FPR | Unsafe PASS |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in summary["seed_results"]:
        rows.append(
            f"| {item['seed']} | {item['original_macro_f1']:.3f} | {item['boundary_macro_f1']:.3f} | "
            f"{item['original_severity_valid_rate']:.1%} | {item['boundary_sources_valid_rate']:.1%} | "
            f"{item['warn_recall']:.1%} | {item['not_applicable_recall']:.1%} | "
            f"{item['pair_accuracy']:.1%} | {item['fail_false_positive_rate']:.1%} | "
            f"{item['unsafe_pass_rate']:.1%} |"
        )
    checks = [f"| {name} | {'PASS' if value else 'FAIL'} |" for name, value in summary["checks"].items()]
    return "\n".join(
        [
            "# Sprint 4 — bramka przed otwarciem testów",
            "",
            f"**Decyzja:** `{summary['decision']}`",
            "",
            *rows,
            "",
            "| Kryterium | Wynik |",
            "|---|---|",
            *checks,
            "",
            "Protected splits pozostają nieotwarte. Decyzja READY dotyczy wyłącznie bramki automatycznej; "
            "obowiązuje także osobny review analityczny i jawne potwierdzenie operatora.",
        ]
    ) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Zbuduj bramkę pre-test dla trzech seedów Q1")
    parser.add_argument("--matrix", default="configs/sprint4_matrix_v1.json")
    parser.add_argument("--output", default=str(RESULTS_DIR / "sprint4" / "m4_pretest_summary.json"))
    parser.add_argument("--markdown", default=str(RESULTS_DIR / "sprint4" / "m4_pretest_summary.md"))
    args = parser.parse_args()
    matrix = _read(args.matrix)
    training = [_read(item["training_metrics"]) for item in matrix["seeds"]]
    original = [_read(item["original_validation_metrics"]) for item in matrix["seeds"]]
    boundary = [_read(item["boundary_validation_metrics"]) for item in matrix["seeds"]]
    summary = build_pretest_summary(matrix, training, original, boundary)
    output = resolve_project_path(args.output)
    markdown = resolve_project_path(args.markdown)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown.write_text(render_markdown(summary), encoding="utf-8")
    print(json.dumps({"decision": summary["decision"], "checks": summary["checks"]}, ensure_ascii=False, indent=2))
    return 0 if summary["decision"] == "READY_TO_OPEN_PROTECTED_SPLITS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
