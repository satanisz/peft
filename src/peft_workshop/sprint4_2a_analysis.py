from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .cases import load_cases
from .paths import CONFIG_DIR, RESULTS_DIR, resolve_project_path
from .validation import extract_json_object, validate_case


ALLOWED_SEVERITY_DATASETS = (
    "data/generated/dataset_v1/train.jsonl",
    "data/generated/dataset_v1/development.jsonl",
    "data/generated/dataset_v1/validation.jsonl",
    "data/splits/boundary_train.jsonl",
    "data/splits/boundary_development.jsonl",
    "data/splits/boundary_validation.jsonl",
)


def _read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(resolve_project_path(path).read_text(encoding="utf-8"))


def analyze_severity_contract(policy: dict[str, Any]) -> list[dict[str, Any]]:
    expected = {name: spec["severity"] for name, spec in policy["statuses"].items()}
    rows = []
    for path in ALLOWED_SEVERITY_DATASETS:
        cases = load_cases(resolve_project_path(path))
        mismatches = [
            case
            for case in cases
            if case["expected_output"]["severity"]
            != expected[case["expected_output"]["status"]]
        ]
        rows.append(
            {
                "path": path,
                "count": len(cases),
                "mismatch_count": len(mismatches),
                "mismatch_rate": len(mismatches) / len(cases) if cases else 0.0,
                "mismatch_patterns": dict(
                    Counter(
                        f"{case['expected_output']['status']}:{case['expected_output']['severity']}"
                        f"->{expected[case['expected_output']['status']]}"
                        for case in mismatches
                    )
                ),
            }
        )
    return rows


def audit_diagnostic_set(policy: dict[str, Any]) -> dict[str, Any]:
    path = resolve_project_path("data/diagnostic/diagnostic_set_v1.jsonl")
    cases = load_cases(path)
    expected = {name: spec["severity"] for name, spec in policy["statuses"].items()}
    errors = [
        f"{case['case_id']}: {message}"
        for case in cases
        for message in validate_case(case)
    ]
    severity_mismatches = [
        case["case_id"]
        for case in cases
        if case["expected_output"]["severity"] != expected[case["expected_output"]["status"]]
    ]
    categories = {
        "numeric_multi_source": sum("FC-201" <= case["case_id"] <= "FC-210" for case in cases),
        "ambiguous_applicability": sum("FC-211" <= case["case_id"] <= "FC-215" for case in cases),
        "missing_data": sum("FC-216" <= case["case_id"] <= "FC-220" for case in cases),
        "prompt_injection": sum("FC-221" <= case["case_id"] <= "FC-225" for case in cases),
        "neutral_out_of_domain": sum("FC-226" <= case["case_id"] <= "FC-230" for case in cases),
    }
    return {
        "path": str(path),
        "count": len(cases),
        "unique_case_ids": len({case["case_id"] for case in cases}) == len(cases),
        "unique_group_ids": len({case["group_id"] for case in cases}) == len(cases),
        "all_manual": all(case.get("metadata", {}).get("generation_method") == "manual" for case in cases),
        "all_validation_scope": all(case.get("split") == "validation" for case in cases),
        "schema_error_count": len(errors),
        "schema_errors": errors,
        "severity_policy_mismatch_count": len(severity_mismatches),
        "severity_policy_mismatch_case_ids": severity_mismatches,
        "categories": categories,
        "status_distribution": dict(Counter(case["expected_output"]["status"] for case in cases)),
    }


def analyze_q1_validation(matrix: dict[str, Any], policy: dict[str, Any]) -> list[dict[str, Any]]:
    canonical_severity = {
        status: spec["severity"] for status, spec in policy["statuses"].items()
    }
    original_gold = {
        case["case_id"]: case
        for case in load_cases(resolve_project_path(matrix["allowed_validation"]["original"]))
    }
    rows = []
    for seed in matrix["seeds"]:
        seed_row: dict[str, Any] = {"name": seed["name"], "seed": seed["seed"]}
        for scope in ("original", "boundary"):
            metrics = _read_json(seed[f"{scope}_validation_metrics"])
            predictions = {
                item["case_id"]: item
                for item in load_cases(resolve_project_path(seed[f"{scope}_validation_output"]))
            }
            severity_errors = []
            policy_compliant_predictions = 0
            parsed_predictions: dict[str, dict[str, Any]] = {}
            for case_id, prediction_record in predictions.items():
                prediction = extract_json_object(prediction_record["response"])
                parsed_predictions[case_id] = prediction
                if prediction.get("severity") == canonical_severity.get(prediction.get("status")):
                    policy_compliant_predictions += 1
            for item in metrics["cases"]:
                if item["severity_correct"]:
                    continue
                prediction = parsed_predictions[item["case_id"]]
                gold = original_gold.get(item["case_id"])
                expected_severity = gold["expected_output"]["severity"] if gold else None
                canonical = canonical_severity.get(item.get("expected_status"))
                severity_errors.append(
                    {
                        "case_id": item["case_id"],
                        "status": item.get("expected_status"),
                        "expected_severity": expected_severity,
                        "predicted_severity": prediction.get("severity"),
                        "canonical_policy_severity": canonical,
                        "gold_matches_policy": expected_severity == canonical if expected_severity else None,
                        "prediction_matches_policy": prediction.get("severity") == canonical,
                    }
                )
            source_errors = [
                {
                    "case_id": item["case_id"],
                    "errors": item.get("errors", []),
                    "evidence_precision": item.get("evidence_precision"),
                    "evidence_recall": item.get("evidence_recall"),
                }
                for item in metrics["cases"]
                if not item["sources_valid"]
            ]
            seed_row[scope] = {
                "severity_correct_rate": metrics["aggregate"]["severity_correct_rate"],
                "predicted_status_policy_compliance_rate": policy_compliant_predictions
                / len(predictions),
                "sources_valid_rate": metrics["aggregate"]["sources_valid_rate"],
                "severity_errors": severity_errors,
                "source_errors": source_errors,
            }
        rows.append(seed_row)
    return rows


def analyze_diagnostic_runs(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for seed in matrix["seeds"]:
        metrics_path = resolve_project_path(f"results/sprint4_2a/{seed['name']}_diagnostic_metrics.json")
        guard_path = resolve_project_path(f"results/sprint4_2a/{seed['name']}_diagnostic_guard_report.json")
        if not metrics_path.exists() or not guard_path.exists():
            continue
        metrics = _read_json(metrics_path)
        guard = _read_json(guard_path)
        rows.append(
            {
                "name": seed["name"],
                "seed": seed["seed"],
                "count": metrics["aggregate"]["count"],
                "macro_f1": metrics["aggregate"]["macro_f1"],
                "status_correct_rate": metrics["aggregate"]["status_correct_rate"],
                "sources_valid_rate": metrics["aggregate"]["sources_valid_rate"],
                "severity_correct_rate": metrics["aggregate"]["severity_correct_rate"],
                "human_review_correct_rate": metrics["aggregate"]["human_review_correct_rate"],
                "guard_pass_through_rate": guard["pass_through_rate"],
                "guard_blocked_count": guard["blocked_count"],
                "guard_blocked_output_accepted_count": guard["blocked_output_accepted_count"],
                "guard_issue_counts": guard["issue_counts"],
                "status_confusion": metrics["aggregate"]["status_confusion"],
            }
        )
    return rows


def build_analysis() -> dict[str, Any]:
    policy = _read_json("configs/status_policy_v1.json")
    matrix = _read_json("configs/sprint4_matrix_v1.json")
    diagnostic_runs = analyze_diagnostic_runs(matrix)
    gate_path = resolve_project_path("results/sprint4_2a/gate.json")
    gate = _read_json(gate_path) if gate_path.exists() else None
    return {
        "milestone": "Sprint 4.2A diagnostic analysis" if diagnostic_runs else "Sprint 4.2A design and contract audit",
        "decision": gate["decision"] if gate else "HOLD_PENDING_INDEPENDENT_REVIEW_AND_Q2_DIAGNOSTIC",
        "protected_splits_opened": False,
        "severity_contract": {
            "legacy_original": "report_only",
            "boundary_and_diagnostic": "enforce_status_policy_v1",
            "datasets": analyze_severity_contract(policy),
        },
        "diagnostic_audit": audit_diagnostic_set(policy),
        "q1_validation_findings": analyze_q1_validation(matrix, policy),
        "diagnostic_runs": diagnostic_runs,
    }


def render_markdown(report: dict[str, Any]) -> str:
    severity_rows = [
        f"| {item['path']} | {item['count']} | {item['mismatch_count']} | {item['mismatch_rate']:.1%} |"
        for item in report["severity_contract"]["datasets"]
    ]
    seed_rows = [
        f"| {item['seed']} | {item['original']['severity_correct_rate']:.1%} | "
        f"{item['original']['predicted_status_policy_compliance_rate']:.1%} | "
        f"{item['boundary']['severity_correct_rate']:.1%} | "
        f"{item['original']['sources_valid_rate']:.1%} | {item['boundary']['sources_valid_rate']:.1%} |"
        for item in report["q1_validation_findings"]
    ]
    return "\n".join(
        [
            "# Sprint 4.2A — analiza severity i source integrity",
            "",
            f"**Decyzja:** `{report['decision']}`",
            "",
            "## Niespójność kontraktu severity",
            "",
            "| Dataset | Rekordy | Niezgodne | Udział |",
            "|---|---:|---:|---:|",
            *severity_rows,
            "",
            "Original dataset-v1 zachowuje legacy severity jako metrykę informacyjną. "
            "Boundary i diagnostic egzekwują status-policy-v1.",
            "",
            "## Q1 — dostępne validation",
            "",
            "| Seed | Severity original legacy | Zgodność predykcji z policy-v1 | Severity boundary | Sources original | Sources boundary |",
            "|---:|---:|---:|---:|---:|---:|",
            *seed_rows,
            "",
            f"Diagnostic set: {report['diagnostic_audit']['count']} przypadków, "
            f"błędy schematu: {report['diagnostic_audit']['schema_error_count']}, "
            f"niezgodności severity policy: {report['diagnostic_audit']['severity_policy_mismatch_count']}.",
            "",
            "## Q2 — diagnostyczne inferencje",
            "",
            "| Seed | Status accuracy | Macro-F1 | Sources | Severity | Human review | Guard pass-through | Guard blocks |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|",
            *[
                f"| {item['seed']} | {item['status_correct_rate']:.1%} | {item['macro_f1']:.3f} | "
                f"{item['sources_valid_rate']:.1%} | {item['severity_correct_rate']:.1%} | "
                f"{item['human_review_correct_rate']:.1%} | {item['guard_pass_through_rate']:.1%} | "
                f"{item['guard_blocked_count']} |"
                for item in report["diagnostic_runs"]
            ],
            "",
            "Guard blokuje odpowiedzi niespełniające kontraktu i nie wykonuje cichej korekty.",
            "",
            "Protected splits pozostają nieotwarte.",
        ]
    ) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Analiza kontraktu Sprintu 4.2A")
    parser.add_argument("--output", default=str(RESULTS_DIR / "sprint4_2a" / "analysis.json"))
    parser.add_argument("--markdown", default=str(RESULTS_DIR / "sprint4_2a" / "analysis.md"))
    args = parser.parse_args()
    report = build_analysis()
    output = resolve_project_path(args.output)
    markdown = resolve_project_path(args.markdown)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"decision": report["decision"], "diagnostic_audit": report["diagnostic_audit"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
