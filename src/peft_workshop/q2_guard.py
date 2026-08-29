from __future__ import annotations

import argparse
import json
import math
import operator
from collections import Counter
from pathlib import Path
from typing import Any

from .cases import load_cases
from .paths import CONFIG_DIR, resolve_project_path
from .validation import extract_json_object, validate_output


def _issue(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


_COMPARATORS = {
    "GT": operator.gt,
    "GTE": operator.ge,
    "LT": operator.lt,
    "LTE": operator.le,
    "EQ": operator.eq,
    "NE": operator.ne,
}


def _numeric(value: Any, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} musi być liczbą.")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} musi być liczbą skończoną.")
    return number


def _assess_deterministic_decision(
    case: dict[str, Any], output: dict[str, Any], rule: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Evaluate a versioned numeric rule without consulting expected_output."""
    issues: list[dict[str, str]] = []
    rule_id = str(rule.get("rule_id", "UNNAMED_RULE"))
    deterministic = case["input"].get("deterministic_check")
    try:
        if not isinstance(deterministic, dict):
            raise ValueError("przypadek nie zawiera deterministic_check")
        value_field = str(rule["value_field"])
        if value_field not in {"result", "reported", "check_result"}:
            raise ValueError(f"niedozwolone value_field: {value_field}")
        value = _numeric(
            deterministic.get(value_field),
            label=f"deterministic_check.{value_field}",
        )
        if rule.get("absolute_value", False):
            value = abs(value)
        if "bands" in rule:
            bands = rule["bands"]
            if not isinstance(bands, list) or not bands:
                raise ValueError("bands musi być niepustą listą")
            parsed_bands = [
                (_numeric(item["max_inclusive"], label="bands.max_inclusive"), str(item["status"]))
                for item in bands
            ]
            if parsed_bands != sorted(parsed_bands, key=lambda item: item[0]):
                raise ValueError("bands muszą być uporządkowane rosnąco")
            expected_status = str(rule["default_status"])
            for maximum, band_status in parsed_bands:
                if value <= maximum:
                    expected_status = band_status
                    break
            comparator_name = "BANDS"
            threshold = [maximum for maximum, _ in parsed_bands]
            condition_met = True
        else:
            comparator_name = str(rule["operator"])
            comparator = _COMPARATORS.get(comparator_name)
            if comparator is None:
                raise ValueError(f"niedozwolony operator: {comparator_name}")
            threshold = _numeric(rule["threshold"], label="threshold")
            condition_met = comparator(value, threshold)
            expected_status = str(
                rule["status_if_true"] if condition_met else rule["status_if_false"]
            )
    except (KeyError, ValueError) as error:
        issues.append(
            _issue(
                "INVALID_DETERMINISTIC_DECISION_RULE",
                f"Reguła {rule_id} nie może zostać wykonana: {error}.",
            )
        )
        return {"rule_id": rule_id, "evaluated": False}, issues

    calculation = output.get("calculation")
    output_result = calculation.get("result") if isinstance(calculation, dict) else None
    try:
        output_result_number = _numeric(output_result, label="calculation.result")
        trusted_result_field = str(rule.get("calculation_result_field", "result"))
        if trusted_result_field not in {"result", "reported", "check_result"}:
            raise ValueError(f"niedozwolone calculation_result_field: {trusted_result_field}")
        trusted_result = _numeric(
            deterministic.get(trusted_result_field),
            label=f"deterministic_check.{trusted_result_field}",
        )
        if not math.isclose(
            output_result_number, trusted_result, rel_tol=1e-9, abs_tol=1e-9
        ):
            issues.append(
                _issue(
                    "DETERMINISTIC_RESULT_MISMATCH",
                    f"Reguła {rule_id}: calculation.result={output_result_number:g} nie zgadza się "
                    f"z zaufanym wynikiem {trusted_result:g}.",
                )
            )
    except ValueError as error:
        issues.append(
            _issue(
                "DETERMINISTIC_RESULT_MISMATCH", f"Reguła {rule_id}: {error}"
            )
        )

    actual_status = output.get("status")
    if actual_status != expected_status:
        issues.append(
            _issue(
                "DETERMINISTIC_DECISION_MISMATCH",
                f"Reguła {rule_id}: wartość {value:g}, tryb {comparator_name}, próg {threshold} wymaga statusu "
                f"{expected_status}, otrzymano {actual_status}.",
            )
        )
    return {
        "rule_id": rule_id,
        "evaluated": True,
        "value": value,
        "operator": comparator_name,
        "threshold": threshold,
        "condition_met": condition_met,
        "required_status": expected_status,
        "actual_status": actual_status,
    }, issues


def assess_response(
    case: dict[str, Any],
    response_text: str,
    *,
    enforce_status_severity: bool,
    status_policy: dict[str, Any],
    decision_rule: dict[str, Any] | None = None,
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
            "deterministic_decision": None,
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

    deterministic_decision = None
    if decision_rule is not None:
        deterministic_decision, decision_issues = _assess_deterministic_decision(
            case, output, decision_rule
        )
        issues.extend(decision_issues)

    decision = "PASS_THROUGH" if not issues else "BLOCK_FOR_HUMAN_REVIEW"
    return {
        "decision": decision,
        "issues": issues,
        "allowed_source_ids": sorted(allowed),
        "used_source_ids": sorted(used),
        "unknown_source_ids": sorted(unknown),
        "deterministic_decision": deterministic_decision,
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
    deterministic_rule_count = sum(
        item["guard"].get("deterministic_decision") is not None for item in records
    )
    return {
        "count": count,
        "pass_through_count": decisions["PASS_THROUGH"],
        "blocked_count": decisions["BLOCK_FOR_HUMAN_REVIEW"],
        "pass_through_rate": decisions["PASS_THROUGH"] / count if count else 0.0,
        "blocked_output_accepted_count": blocked_output_accepted_count,
        "deterministic_rule_count": deterministic_rule_count,
        "issue_counts": dict(sorted(issue_codes.items())),
        "policy_notice": "Blocked responses are preserved for audit and are never silently corrected.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Q2 deterministic source and policy guard")
    parser.add_argument("--data", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument(
        "--severity-mode",
        choices=["legacy_report_only", "enforce_status_policy_v1"],
        required=True,
    )
    parser.add_argument(
        "--decision-rules",
        help="Opcjonalny wersjonowany plik reguł decyzji deterministycznych.",
    )
    args = parser.parse_args()

    cases = {item["case_id"]: item for item in load_cases(resolve_project_path(args.data))}
    predictions = load_cases(resolve_project_path(args.predictions))
    policy = json.loads((CONFIG_DIR / "status_policy_v1.json").read_text(encoding="utf-8"))
    decision_rules: dict[str, Any] = {}
    if args.decision_rules:
        rules_config = json.loads(
            resolve_project_path(args.decision_rules).read_text(encoding="utf-8")
        )
        decision_rules = rules_config.get("rules_by_case_id", {})
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
            decision_rule=decision_rules.get(case_id),
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
