from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .validation import extract_json_object, validate_output, validate_prediction_sources


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def score_prediction(case: dict[str, Any], response_text: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "case_id": case["case_id"],
        "json_valid": False,
        "schema_valid": False,
        "sources_valid": False,
        "status_correct": False,
        "control_type_correct": False,
        "severity_correct": False,
        "human_review_correct": False,
        "evidence_precision": 0.0,
        "evidence_recall": 0.0,
        "errors": [],
    }
    try:
        output = extract_json_object(response_text)
    except ValueError as error:
        result["errors"].append(str(error))
        return result

    result["json_valid"] = True
    schema_errors = validate_output(output)
    result["errors"].extend(schema_errors)
    result["schema_valid"] = not schema_errors

    source_errors = validate_prediction_sources(case, output)
    result["errors"].extend(source_errors)
    result["sources_valid"] = not source_errors

    expected = case["expected_output"]
    result["status_correct"] = output.get("status") == expected["status"]
    result["control_type_correct"] = output.get("control_type") == expected["control_type"]
    result["severity_correct"] = output.get("severity") == expected["severity"]
    result["human_review_correct"] = (
        output.get("requires_human_review") == expected["requires_human_review"]
    )

    raw_evidence = output.get("evidence", [])
    predicted_evidence = (
        {item.get("source_id") for item in raw_evidence if isinstance(item, dict)}
        if isinstance(raw_evidence, list)
        else set()
    )
    expected_evidence = {item["source_id"] for item in expected.get("evidence", [])}
    true_positive = len(predicted_evidence & expected_evidence)
    result["evidence_precision"] = _safe_div(true_positive, len(predicted_evidence))
    result["evidence_recall"] = _safe_div(true_positive, len(expected_evidence))
    result["predicted_status"] = output.get("status")
    result["expected_status"] = expected["status"]
    return result


def aggregate_scores(scores: list[dict[str, Any]]) -> dict[str, Any]:
    if not scores:
        return {"count": 0}
    boolean_fields = [
        "json_valid",
        "schema_valid",
        "sources_valid",
        "status_correct",
        "control_type_correct",
        "severity_correct",
        "human_review_correct",
    ]
    aggregate: dict[str, Any] = {"count": len(scores)}
    for field in boolean_fields:
        aggregate[f"{field}_rate"] = sum(bool(item[field]) for item in scores) / len(scores)
    aggregate["mean_evidence_precision"] = sum(item["evidence_precision"] for item in scores) / len(scores)
    aggregate["mean_evidence_recall"] = sum(item["evidence_recall"] for item in scores) / len(scores)
    aggregate["status_confusion"] = dict(
        Counter(
            f"{item.get('expected_status')}->{item.get('predicted_status')}"
            for item in scores
            if item.get("predicted_status") is not None
        )
    )
    labels = ["PASS", "WARN", "FAIL", "INSUFFICIENT_DATA", "NOT_APPLICABLE"]
    per_label: dict[str, dict[str, float | int]] = {}
    f1_values: list[float] = []
    for label in labels:
        true_positive = sum(
            item.get("expected_status") == label and item.get("predicted_status") == label
            for item in scores
        )
        false_positive = sum(
            item.get("expected_status") != label and item.get("predicted_status") == label
            for item in scores
        )
        false_negative = sum(
            item.get("expected_status") == label and item.get("predicted_status") != label
            for item in scores
        )
        support = sum(item.get("expected_status") == label for item in scores)
        precision = _safe_div(true_positive, true_positive + false_positive)
        recall = _safe_div(true_positive, true_positive + false_negative)
        f1 = _safe_div(2 * precision * recall, precision + recall)
        per_label[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }
        if support:
            f1_values.append(f1)
    aggregate["per_status"] = per_label
    aggregate["macro_f1"] = sum(f1_values) / len(f1_values) if f1_values else 0.0
    fail_negatives = sum(item.get("expected_status") != "FAIL" for item in scores)
    aggregate["fail_false_positive_rate"] = _safe_div(
        sum(
            item.get("expected_status") != "FAIL" and item.get("predicted_status") == "FAIL"
            for item in scores
        ),
        fail_negatives,
    )
    fail_positives = sum(item.get("expected_status") == "FAIL" for item in scores)
    aggregate["fail_false_negative_rate"] = _safe_div(
        sum(
            item.get("expected_status") == "FAIL" and item.get("predicted_status") != "FAIL"
            for item in scores
        ),
        fail_positives,
    )
    return aggregate


def aggregate_boundary_scores(
    scores: list[dict[str, Any]], cost_matrix: dict[str, dict[str, int]]
) -> dict[str, Any]:
    if not scores:
        return {"count": 0}
    pairs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for score in scores:
        pairs[score["group_id"]].append(score)
    complete_pairs = [pair for pair in pairs.values() if len(pair) == 2]
    unsafe_cases = [
        item
        for item in scores
        if item.get("expected_status") in {"WARN", "FAIL", "INSUFFICIENT_DATA"}
    ]
    escalation_cases = [
        item
        for item in scores
        if item.get("expected_status") in {"WARN", "NOT_APPLICABLE", "INSUFFICIENT_DATA"}
    ]
    costs = [
        cost_matrix.get(str(item.get("expected_status")), {}).get(
            str(item.get("predicted_status")),
            max(max(row.values()) for row in cost_matrix.values()),
        )
        for item in scores
    ]
    pair_correct = sum(all(item["status_correct"] for item in pair) for pair in complete_pairs)
    return {
        "count": len(scores),
        "pair_count": len(complete_pairs),
        "pair_accuracy": _safe_div(pair_correct, len(complete_pairs)),
        "flip_consistency": _safe_div(pair_correct, len(complete_pairs)),
        "unsafe_pass_rate": _safe_div(
            sum(item.get("predicted_status") == "PASS" for item in unsafe_cases),
            len(unsafe_cases),
        ),
        "unnecessary_escalation_rate": _safe_div(
            sum(item.get("predicted_status") == "FAIL" for item in escalation_cases),
            len(escalation_cases),
        ),
        "mean_business_cost": _safe_div(sum(costs), len(costs)),
        "total_business_cost": sum(costs),
        "applicability_missing_confusion": {
            "NOT_APPLICABLE->INSUFFICIENT_DATA": sum(
                item.get("expected_status") == "NOT_APPLICABLE"
                and item.get("predicted_status") == "INSUFFICIENT_DATA"
                for item in scores
            ),
            "INSUFFICIENT_DATA->NOT_APPLICABLE": sum(
                item.get("expected_status") == "INSUFFICIENT_DATA"
                and item.get("predicted_status") == "NOT_APPLICABLE"
                for item in scores
            ),
        },
    }
