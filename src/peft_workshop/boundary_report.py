from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .paths import resolve_project_path


VARIANTS = ("B1", "B2", "B3")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_boundary_summary(reports: dict[str, dict[str, Any]], split: str) -> dict[str, Any]:
    comparison: dict[str, Any] = {}
    for variant in VARIANTS:
        report = reports[variant]
        reported_variant = report.get("metadata", {}).get("baseline_variant")
        if reported_variant != variant:
            raise ValueError(f"Oczekiwano {variant}, otrzymano {reported_variant!r}")
        aggregate = report["aggregate"]
        boundary = report["boundary"]
        runtime = report["runtime"]
        comparison[variant] = {
            "count": aggregate["count"],
            "schema_valid_rate": aggregate["schema_valid_rate"],
            "status_accuracy": aggregate["status_correct_rate"],
            "macro_f1": aggregate["macro_f1"],
            "warn_recall": aggregate["per_status"]["WARN"]["recall"],
            "not_applicable_recall": aggregate["per_status"]["NOT_APPLICABLE"]["recall"],
            "insufficient_data_recall": aggregate["per_status"]["INSUFFICIENT_DATA"]["recall"],
            "fail_false_positive_rate": aggregate["fail_false_positive_rate"],
            "pair_accuracy": boundary["pair_accuracy"],
            "unsafe_pass_rate": boundary["unsafe_pass_rate"],
            "unnecessary_escalation_rate": boundary["unnecessary_escalation_rate"],
            "mean_business_cost": boundary["mean_business_cost"],
            "mean_input_tokens": runtime["input_tokens"]["mean"],
            "p95_latency_s": runtime["latency_s"]["p95"],
            "peak_gpu_allocated_gib": runtime["peak_gpu_allocated_gib"]["max"],
            "truncated_rate": runtime["truncated_rate"],
        }
    best_quality = max(VARIANTS, key=lambda item: comparison[item]["macro_f1"])
    lowest_cost = min(VARIANTS, key=lambda item: comparison[item]["mean_business_cost"])
    return {
        "boundary_pack_version": "1.0.0",
        "split": split,
        "comparison": comparison,
        "best_macro_f1": best_quality,
        "lowest_business_cost": lowest_cost,
    }


def _percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def render_markdown(summary: dict[str, Any]) -> str:
    rows = []
    for variant in VARIANTS:
        item = summary["comparison"][variant]
        rows.append(
            "| {variant} | {schema} | {accuracy} | {f1:.3f} | {warn} | {na} | "
            "{pair} | {fpr} | {unsafe} | {escalation} | {cost:.2f} | {tokens:.0f} | {vram:.2f} |".format(
                variant=variant,
                schema=_percent(item["schema_valid_rate"]),
                accuracy=_percent(item["status_accuracy"]),
                f1=item["macro_f1"],
                warn=_percent(item["warn_recall"]),
                na=_percent(item["not_applicable_recall"]),
                pair=_percent(item["pair_accuracy"]),
                fpr=_percent(item["fail_false_positive_rate"]),
                unsafe=_percent(item["unsafe_pass_rate"]),
                escalation=_percent(item["unnecessary_escalation_rate"]),
                cost=item["mean_business_cost"],
                tokens=item["mean_input_tokens"],
                vram=item["peak_gpu_allocated_gib"],
            )
        )
    return "\n".join(
        [
            f"# Boundary baseline — {summary['split']}",
            "",
            "| Wariant | Schemat | Accuracy | Macro-F1 | WARN recall | N/A recall | Pair accuracy | FAIL FPR | Unsafe PASS | Escalation | Śr. koszt | Input tok. | Peak VRAM |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            *rows,
            "",
            f"Najwyższe macro-F1: **{summary['best_macro_f1']}**.",
            f"Najniższy średni koszt błędu: **{summary['lowest_business_cost']}**.",
            "",
            "Wynik dotyczy diagnostycznego boundary pack, a nie częstości produkcyjnych.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Porównaj B1/B2/B3 na boundary pack")
    parser.add_argument("--split", default="validation")
    for variant in VARIANTS:
        parser.add_argument(f"--{variant.lower()}", required=True)
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    args = parser.parse_args()
    reports = {
        variant: _load(resolve_project_path(getattr(args, variant.lower())))
        for variant in VARIANTS
    }
    summary = build_boundary_summary(reports, args.split)
    json_output = resolve_project_path(args.json_output)
    markdown_output = resolve_project_path(args.markdown_output)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_output.write_text(render_markdown(summary), encoding="utf-8")
    print(render_markdown(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
