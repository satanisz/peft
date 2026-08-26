from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .paths import resolve_project_path


VARIANTS = ("B0", "B1", "B2")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _percent(value: float) -> str:
    return f"{100 * value:.1f}%"


def build_summary(reports: dict[str, dict[str, Any]], split: str) -> dict[str, Any]:
    comparison: dict[str, Any] = {}
    error_catalog: dict[str, list[dict[str, Any]]] = {}
    for variant in VARIANTS:
        report = reports[variant]
        reported_variant = report.get("metadata", {}).get("baseline_variant")
        if reported_variant != variant:
            raise ValueError(
                f"Oczekiwano raportu {variant}, otrzymano {reported_variant!r}"
            )
        aggregate = report["aggregate"]
        runtime = report["runtime"]
        comparison[variant] = {
            "count": aggregate["count"],
            "json_valid_rate": aggregate["json_valid_rate"],
            "schema_valid_rate": aggregate["schema_valid_rate"],
            "status_correct_rate": aggregate["status_correct_rate"],
            "macro_f1": aggregate["macro_f1"],
            "sources_valid_rate": aggregate["sources_valid_rate"],
            "human_review_correct_rate": aggregate["human_review_correct_rate"],
            "fail_false_positive_rate": aggregate["fail_false_positive_rate"],
            "mean_latency_s": runtime["latency_s"]["mean"],
            "p95_latency_s": runtime["latency_s"]["p95"],
            "mean_input_tokens": runtime["input_tokens"]["mean"],
            "mean_output_tokens": runtime["output_tokens"]["mean"],
            "mean_tokens_per_second": runtime["tokens_per_second"]["mean"],
            "peak_gpu_allocated_gib": runtime["peak_gpu_allocated_gib"]["max"],
            "truncated_rate": runtime["truncated_rate"],
        }
        errors = [
            {
                "case_id": case["case_id"],
                "control_type": case["control_type"],
                "expected_status": case["expected_status"],
                "predicted_status": case.get("predicted_status"),
                "json_valid": case["json_valid"],
                "schema_valid": case["schema_valid"],
                "status_correct": case["status_correct"],
                "errors": case["errors"],
            }
            for case in report["cases"]
            if not (case["schema_valid"] and case["status_correct"])
        ]
        error_catalog[variant] = errors
    return {
        "baseline_version": "1.0.0",
        "split": split,
        "comparison": comparison,
        "error_catalog": error_catalog,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    rows = []
    for variant in VARIANTS:
        item = summary["comparison"][variant]
        rows.append(
            "| {variant} | {count} | {json} | {schema} | {accuracy} | {f1:.3f} | "
            "{sources} | {fpr} | {latency:.2f} s | {vram:.2f} GiB |".format(
                variant=variant,
                count=item["count"],
                json=_percent(item["json_valid_rate"]),
                schema=_percent(item["schema_valid_rate"]),
                accuracy=_percent(item["status_correct_rate"]),
                f1=item["macro_f1"],
                sources=_percent(item["sources_valid_rate"]),
                fpr=_percent(item["fail_false_positive_rate"]),
                latency=item["p95_latency_s"],
                vram=item["peak_gpu_allocated_gib"],
            )
        )
    best = max(VARIANTS, key=lambda name: summary["comparison"][name]["macro_f1"])
    error_lines = [
        f"- {variant}: {len(summary['error_catalog'][variant])} przypadków z błędnym schematem lub statusem."
        for variant in VARIANTS
    ]
    return "\n".join(
        [
            f"# Baseline v1 — {summary['split']}",
            "",
            "| Wariant | N | JSON | Schemat | Status accuracy | Macro-F1 | Źródła | FAIL FPR | Latencja p95 | Peak VRAM |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            *rows,
            "",
            f"Najwyższe macro-F1 na tym splicie uzyskał **{best}**. Wybór baseline'u do porównań z adapterem musi dodatkowo uwzględniać schema validity, false positive rate i koszt kontekstu.",
            "",
            "## Katalog błędów",
            "",
            *error_lines,
            "",
            "Szczegóły per przypadek znajdują się w odpowiadającym pliku JSON.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Zbuduj porównanie baseline B0/B1/B2")
    parser.add_argument("--split", required=True)
    for variant in VARIANTS:
        parser.add_argument(f"--{variant.lower()}", required=True, help=f"Raport metryk {variant}")
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    args = parser.parse_args()
    reports = {
        variant: _load(resolve_project_path(getattr(args, variant.lower())))
        for variant in VARIANTS
    }
    summary = build_summary(reports, args.split)
    json_output = resolve_project_path(args.json_output)
    markdown_output = resolve_project_path(args.markdown_output)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_output.write_text(render_markdown(summary), encoding="utf-8")
    print(f"Zapisano podsumowanie: {json_output}")
    print(f"Zapisano tabelę: {markdown_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
