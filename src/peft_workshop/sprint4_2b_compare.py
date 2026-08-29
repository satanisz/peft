from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .paths import RESULTS_DIR, resolve_project_path


EXCLUDED_FROM_DIRECT_AB = {"FC-209"}
INJECTION_CASES = {"FC-221", "FC-222", "FC-223", "FC-224", "FC-225"}


def _read(path: str | Path) -> dict[str, Any]:
    return json.loads(resolve_project_path(path).read_text(encoding="utf-8"))


def _rate(cases: list[dict[str, Any]], field: str) -> float:
    return sum(bool(item[field]) for item in cases) / len(cases) if cases else 0.0


def build_comparison() -> dict[str, Any]:
    matrix = _read("configs/sprint4_matrix_v1.json")
    thresholds = _read("configs/q2_source_guard_v1.json")["diagnostic_thresholds"]
    rows = []
    missing = []
    for seed in matrix["seeds"]:
        baseline_path = resolve_project_path(f"results/sprint4_2a/{seed['name']}_diagnostic_metrics.json")
        treatment_path = resolve_project_path(f"results/sprint4_2b/{seed['name']}_diagnostic_v2_metrics.json")
        guard_path = resolve_project_path(f"results/sprint4_2b/{seed['name']}_diagnostic_v2_guard_report.json")
        if not baseline_path.exists() or not treatment_path.exists() or not guard_path.exists():
            missing.append(seed["name"])
            continue
        baseline = _read(baseline_path)
        treatment = _read(treatment_path)
        guard = _read(guard_path)
        baseline_29 = [item for item in baseline["cases"] if item["case_id"] not in EXCLUDED_FROM_DIRECT_AB]
        treatment_29 = [item for item in treatment["cases"] if item["case_id"] not in EXCLUDED_FROM_DIRECT_AB]
        injection = [item for item in treatment["cases"] if item["case_id"] in INJECTION_CASES]
        fc209 = next(item for item in treatment["cases"] if item["case_id"] == "FC-209")
        rows.append(
            {
                "name": seed["name"],
                "seed": seed["seed"],
                "baseline": baseline["aggregate"],
                "treatment": treatment["aggregate"],
                "comparable_29": {
                    "baseline_status_correct_rate": _rate(baseline_29, "status_correct"),
                    "treatment_status_correct_rate": _rate(treatment_29, "status_correct"),
                    "status_delta": _rate(treatment_29, "status_correct") - _rate(baseline_29, "status_correct"),
                    "baseline_severity_correct_rate": _rate(baseline_29, "severity_correct"),
                    "treatment_severity_correct_rate": _rate(treatment_29, "severity_correct"),
                    "severity_delta": _rate(treatment_29, "severity_correct") - _rate(baseline_29, "severity_correct"),
                },
                "fc209_correct_after_clarification": bool(fc209["status_correct"]),
                "injection_suite_passed": len(injection) == 5
                and all(item["status_correct"] and item["sources_valid"] for item in injection),
                "guard": guard,
            }
        )

    checks: dict[str, bool] = {"three_treatment_reports_present": len(rows) == 3 and not missing}
    if checks["three_treatment_reports_present"]:
        checks.update(
            {
                "case_count_each_seed": all(item["treatment"]["count"] == thresholds["case_count"] for item in rows),
                "macro_f1_each_seed": min(item["treatment"]["macro_f1"] for item in rows) >= thresholds["status_macro_f1_min"],
                "sources_each_seed": min(item["treatment"]["sources_valid_rate"] for item in rows) >= thresholds["sources_valid_rate_min"],
                "severity_each_seed": min(item["treatment"]["severity_correct_rate"] for item in rows) >= thresholds["severity_valid_rate_min"],
                "guard_never_accepts_blocked_output": all(item["guard"]["blocked_output_accepted_count"] <= thresholds["guard_blocked_output_accepted_max"] for item in rows),
                "prompt_injection_suite_each_seed": all(item["injection_suite_passed"] for item in rows),
                "fc209_each_seed": all(item["fc209_correct_after_clarification"] for item in rows),
            }
        )
    if not checks["three_treatment_reports_present"]:
        decision = "HOLD_MISSING_PROMPT_V2_RESULTS"
    elif all(checks.values()):
        decision = "READY_FOR_SOL_HIGH_APPROVAL_REVIEW"
    else:
        decision = "HOLD_PROMPT_V2_THRESHOLDS"
    return {
        "milestone": "Sprint 4.2B prompt-contract ablation",
        "decision": decision,
        "comparison_scope": "29 unchanged cases; FC-209 reported separately after input clarification",
        "missing_treatment_seeds": missing,
        "checks": checks,
        "seeds": rows,
        "protected_splits_opened": False,
        "automatic_approval": False,
    }


def render_markdown(report: dict[str, Any]) -> str:
    rows = []
    for item in report["seeds"]:
        rows.append(
            f"| {item['seed']} | {item['baseline']['macro_f1']:.3f} | {item['treatment']['macro_f1']:.3f} | "
            f"{item['treatment']['sources_valid_rate']:.1%} | {item['treatment']['severity_correct_rate']:.1%} | "
            f"{item['comparable_29']['status_delta']:+.1%} | {item['comparable_29']['severity_delta']:+.1%} | "
            f"{item['guard']['blocked_count']} |"
        )
    return "\n".join(
        [
            "# Sprint 4.2B — prompt contract v1 vs v2",
            "",
            f"**Decyzja:** `{report['decision']}`",
            "",
            "Bezpośrednie A/B obejmuje 29 niezmienionych przypadków. FC-209 jest raportowany osobno po doprecyzowaniu wejścia.",
            "",
            "| Seed | Macro-F1 v1 | Macro-F1 v2 | Sources v2 | Severity v2 | Δ status 29 | Δ severity 29 | Guard blocks v2 |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|",
            *rows,
            "",
            "Protected splits pozostają nieotwarte.",
        ]
    ) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Porównanie diagnostyczne prompt contract v1/v2")
    parser.add_argument("--output", default=str(RESULTS_DIR / "sprint4_2b" / "comparison.json"))
    parser.add_argument("--markdown", default=str(RESULTS_DIR / "sprint4_2b" / "comparison.md"))
    parser.add_argument("--gate", default=str(RESULTS_DIR / "sprint4_2b" / "gate.json"))
    args = parser.parse_args()
    report = build_comparison()
    output = resolve_project_path(args.output)
    markdown = resolve_project_path(args.markdown)
    gate = resolve_project_path(args.gate)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown.write_text(render_markdown(report), encoding="utf-8")
    gate.write_text(
        json.dumps(
            {
                "milestone": report["milestone"],
                "decision": report["decision"],
                "checks": report["checks"],
                "protected_splits_opened": False,
                "automatic_approval": False,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"decision": report["decision"], "checks": report["checks"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
