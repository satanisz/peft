from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .cases import load_cases
from .paths import RESULTS_DIR, resolve_project_path


def _read(path: str | Path) -> dict[str, Any]:
    return json.loads(resolve_project_path(path).read_text(encoding="utf-8"))


def build_report() -> dict[str, Any]:
    matrix = _read("configs/sprint4_matrix_v1.json")
    rules = _read("configs/deterministic_decision_rules_v1.json")
    prompt_gate = _read("results/sprint4_2b/gate.json")
    rows = []
    missing = []
    for seed in matrix["seeds"]:
        report_path = resolve_project_path(
            f"results/sprint4_2c/{seed['name']}_decision_guard_report.json"
        )
        records_path = resolve_project_path(
            f"results/sprint4_2c/{seed['name']}_decision_guarded.jsonl"
        )
        if not report_path.exists() or not records_path.exists():
            missing.append(seed["name"])
            continue
        guard_report = _read(report_path)
        records = load_cases(records_path)
        fc209 = next(item for item in records if item["case_id"] == "FC-209")
        other_records = [item for item in records if item["case_id"] != "FC-209"]
        issue_codes = {
            issue["code"] for issue in fc209["guard"].get("issues", [])
        }
        rows.append(
            {
                "name": seed["name"],
                "seed": seed["seed"],
                "guard": guard_report,
                "fc209": {
                    "decision": fc209["guard"]["decision"],
                    "issue_codes": sorted(issue_codes),
                    "deterministic_decision": fc209["guard"].get(
                        "deterministic_decision"
                    ),
                    "silently_corrected": fc209["guard"].get("guarded_output")
                    is not None,
                },
                "all_other_cases_pass_through": all(
                    item["guard"]["decision"] == "PASS_THROUGH"
                    for item in other_records
                ),
            }
        )

    checks: dict[str, bool] = {
        "three_guard_reports_present": len(rows) == 3 and not missing,
        "retrospective_rule_cannot_authorize_protected": not rules["governance"][
            "may_authorize_protected_evidence"
        ],
    }
    if checks["three_guard_reports_present"]:
        checks.update(
            {
                "case_count_each_seed": all(
                    item["guard"]["count"] == 30 for item in rows
                ),
                "one_deterministic_rule_each_seed": all(
                    item["guard"]["deterministic_rule_count"] == 1
                    for item in rows
                ),
                "fc209_blocked_each_seed": all(
                    item["fc209"]["decision"] == "BLOCK_FOR_HUMAN_REVIEW"
                    and "DETERMINISTIC_DECISION_MISMATCH"
                    in item["fc209"]["issue_codes"]
                    for item in rows
                ),
                "blocked_output_never_accepted": all(
                    item["guard"]["blocked_output_accepted_count"] == 0
                    and not item["fc209"]["silently_corrected"]
                    for item in rows
                ),
                "all_other_cases_pass_through": all(
                    item["all_other_cases_pass_through"] for item in rows
                ),
                "exactly_one_block_each_seed": all(
                    item["guard"]["blocked_count"] == 1 for item in rows
                ),
            }
        )

    demo_ready = all(checks.values())
    return {
        "milestone": "Sprint 4.2C deterministic decision containment",
        "demo_decision": (
            "READY_FOR_SPRINT5_DEMO_WITH_PROTECTED_HOLD"
            if demo_ready
            else "HOLD_GUARD_VALIDATION"
        ),
        "protected_evidence_decision": "HOLD",
        "prompt_v2_gate_decision": prompt_gate["decision"],
        "interpretation": (
            "Guard operationally contains FC-209 but does not improve model metrics "
            "and cannot retroactively authorize protected evidence."
        ),
        "missing_seeds": missing,
        "checks": checks,
        "seeds": rows,
        "protected_splits_opened": False,
        "automatic_approval": False,
    }


def render_markdown(report: dict[str, Any]) -> str:
    rows = []
    for item in report["seeds"]:
        decision = item["fc209"]["deterministic_decision"]
        rows.append(
            f"| {item['seed']} | {item['guard']['pass_through_count']}/30 | "
            f"{item['guard']['blocked_count']} | {decision['value']:g} "
            f"{decision['operator']} {decision['threshold']:g} | "
            f"{decision['actual_status']} → blokada ({decision['required_status']}) |"
        )
    return "\n".join(
        [
            "# Sprint 4.2C — deterministic decision containment",
            "",
            f"**Decyzja demonstracyjna:** `{report['demo_decision']}`",
            "",
            f"**Protected evidence:** `{report['protected_evidence_decision']}`",
            "",
            "Guard nie poprawia odpowiedzi. Sprzeczny wynik zachowuje do audytu i kieruje do człowieka.",
            "",
            "| Seed | Pass-through | Blokady | Reguła FC-209 | Wynik |",
            "|---:|---:|---:|---:|---|",
            *rows,
            "",
            "Regułę utworzono po analizie diagnostycznej. Jest materiałem warsztatowym i nie stanowi niezależnego dowodu generalizacji.",
            "Protected splits pozostają nieotwarte.",
        ]
    ) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Raport Sprintu 4.2C")
    parser.add_argument(
        "--output", default=str(RESULTS_DIR / "sprint4_2c" / "report.json")
    )
    parser.add_argument(
        "--markdown", default=str(RESULTS_DIR / "sprint4_2c" / "report.md")
    )
    parser.add_argument(
        "--gate", default=str(RESULTS_DIR / "sprint4_2c" / "gate.json")
    )
    args = parser.parse_args()
    report = build_report()
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
                "demo_decision": report["demo_decision"],
                "protected_evidence_decision": report[
                    "protected_evidence_decision"
                ],
                "checks": report["checks"],
                "protected_splits_opened": False,
                "automatic_approval": False,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "demo_decision": report["demo_decision"],
                "protected_evidence_decision": report[
                    "protected_evidence_decision"
                ],
                "checks": report["checks"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
