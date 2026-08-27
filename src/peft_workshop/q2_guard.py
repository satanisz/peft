from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .cases import load_cases
from .paths import CONFIG_DIR, resolve_project_path
from .validation import extract_json_object, validate_output


def _issue(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def assess_response(
    case: dict[str, Any],
    response_text: str,
    *,
    enforce_status_severity: bool,
    status_policy: dict[str, Any],
) -> dict[str, Any]:
    """Assess a model response without using the case's expected_output."""
    issues: list[dict[str, str]] = []
    try:
        output = extract_json_object(response_text)
    except ValueError as error:
        return {
            "decision": "BLOCK_FOR_HUMAN_REVIEW",
            "issues": [_issue("INVALID_JSON", str(error))],
            "allowed_source_ids": sorted(item["source_id"] for item in case["input"]["sources"]),
            "used_source_ids": [],
            "unknown_source_ids": [],
            "guarded_output": None,
        }

    schema_errors = validate_output(output)
    if schema_errors:
        issues.extend(_issue("SCHEMA_VIOLATION", message) for message in schema_errors)

    allowed = {item["source_id"] for item in case["input"]["sources"]}
    evidence = output.get("evidence")
    used = {
        str(item.get("source_id"))
        for item in evidence
        if isinstance(evidence, list) and isinstance(item, dict) and item.get("source_id")
    } if isinstance(evidence, list) else set()
    unknown = used - allowed
    for source_id in sorted(unknown):
        issues.append(_issue("UNKNOWN_SOURCE_ID", f"Nieznany source_id: {source_id}"))
    if isinstance(evidence, list) and not evidence:
        issues.append(_issue("EMPTY_EVIDENCE", "Odpowiedź nie wskazuje żadnego źródła."))

    status = output.get("status")
    status_contract = status_policy.get("statuses", {}).get(str(status), {})
    if enforce_status_severity and status_contract:
        expected_severity = status_contract.get("severity")
        if output.get("severity") != expected_severity:
            issues.append(
                _issue(
                    "SEVERITY_POLICY_MISMATCH",
                    f"Status {status} wymaga severity {expected_severity}, otrzymano {output.get('severity')}.",
                )
            )
    if status_contract and output.get("requires_human_review") != status_contract.get(
        "requires_human_review"
    ):
        issues.append(
            _issue(
                "HUMAN_REVIEW_POLICY_MISMATCH",
                f"Status {status} ma niespójne requires_human_review.",
            )
        )

    deterministic_input = case["input"].get("deterministic_check") is not None
    calculation = output.get("calculation")
    claims_deterministic = isinstance(calculation, dict) and calculation.get(
        "performed_by"
    ) == "deterministic_control"
    if claims_deterministic and not deterministic_input:
        issues.append(
            _issue(
                "UNTRUSTED_CALCULATION_CLAIM",
                "Model deklaruje deterministic_control bez wyniku kontroli w wejściu.",
            )
        )
    if deterministic_input and not claims_deterministic:
        issues.append(
            _issue(
                "MISSING_DETERMINISTIC_CALCULATION",
                "Wejście zawiera wynik kontroli deterministycznej, ale odpowiedź go nie dokumentuje.",
            )
        )

    decision = "PASS_THROUGH" if not issues else "BLOCK_FOR_HUMAN_REVIEW"
    return {
        "decision": decision,
        "issues": issues,
        "allowed_source_ids": sorted(allowed),
        "used_source_ids": sorted(used),
        "unknown_source_ids": sorted(unknown),
        "guarded_output": output if decision == "PASS_THROUGH" else None,
    }


def build_guard_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    decisions = Counter(item["guard"]["decision"] for item in records)
    issue_codes = Counter(
        issue["code"] for item in records for issue in item["guard"].get("issues", [])
    )
    count = len(records)
    blocked_output_accepted_count = sum(
        item["guard"]["decision"] == "BLOCK_FOR_HUMAN_REVIEW"
        and item["guard"].get("guarded_output") is not None
        for item in records
    )
    return {
        "count": count,
        "pass_through_count": decisions["PASS_THROUGH"],
        "blocked_count": decisions["BLOCK_FOR_HUMAN_REVIEW"],
        "pass_through_rate": decisions["PASS_THROUGH"] / count if count else 0.0,
        "blocked_output_accepted_count": blocked_output_accepted_count,
        "issue_counts": dict(sorted(issue_codes.items())),
        "policy_notice": "Blocked responses are preserved for audit and are never silently corrected.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Q2 deterministic source and policy guard")
    parser.add_argument("--data", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--severity-mode", choices=["legacy_report_only", "enforce_status_policy_v1"], required=True)
    args = parser.parse_args()

    cases = {item["case_id"]: item for item in load_cases(resolve_project_path(args.data))}
    predictions = load_cases(resolve_project_path(args.predictions))
    policy = json.loads((CONFIG_DIR / "status_policy_v1.json").read_text(encoding="utf-8"))
    records = []
    for prediction in predictions:
        case_id = prediction["case_id"]
        if case_id not in cases:
            raise SystemExit(f"Predykcja odwołuje się do nieznanego przypadku: {case_id}")
        guard = assess_response(
            cases[case_id],
            prediction["response"],
            enforce_status_severity=args.severity_mode == "enforce_status_policy_v1",
            status_policy=policy,
        )
        records.append({**prediction, "guard": guard})

    output = resolve_project_path(args.output)
    report_path = resolve_project_path(args.report)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    report = build_guard_report(records)
    report["severity_mode"] = args.severity_mode
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
