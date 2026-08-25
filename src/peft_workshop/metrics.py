from __future__ import annotations

from collections import Counter
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
    return aggregate
