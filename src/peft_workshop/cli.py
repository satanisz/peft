from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from .cases import DEFAULT_OUTPUT, load_cases, write_cases
from .metrics import aggregate_boundary_scores, aggregate_scores, score_prediction
from .paths import CONFIG_DIR, resolve_project_path
from .prompts import build_messages, select_demonstrations, select_status_demonstrations
from .validation import validate_case


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def command_generate(args: argparse.Namespace) -> int:
    output = write_cases(resolve_project_path(args.output))
    print(f"Zapisano 40 przypadków: {output}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    path = resolve_project_path(args.data)
    cases = load_cases(path)
    errors: list[str] = []
    seen_ids: set[str] = set()
    for case in cases:
        if case["case_id"] in seen_ids:
            errors.append(f"{case['case_id']}: zduplikowany identyfikator")
        seen_ids.add(case["case_id"])
        errors.extend(f"{case['case_id']}: {message}" for message in validate_case(case))
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Poprawne przypadki: {len(cases)}")
    print("Splity:", dict(Counter(case["split"] for case in cases)))
    print("Typy kontroli:", dict(Counter(case["control"]["type"] for case in cases)))
    print("Statusy:", dict(Counter(case["expected_output"]["status"] for case in cases)))
    return 0


def command_show_prompt(args: argparse.Namespace) -> int:
    cases = load_cases(resolve_project_path(args.data))
    case = next((item for item in cases if item["case_id"] == args.case_id), None)
    if case is None:
        raise SystemExit(f"Nie znaleziono przypadku {args.case_id}")
    demonstrations = (
        select_demonstrations(case, cases)
        if args.variant == "B2"
        else select_status_demonstrations(case, cases)
        if args.variant == "B3"
        else []
    )
    style = "naive" if args.variant == "B0" else "status_aware" if args.variant == "B3" else "full"
    print(json.dumps(build_messages(case, demonstrations, prompt_style=style), ensure_ascii=False, indent=2))
    return 0


def _runtime_summary(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    def describe(field: str) -> dict[str, float] | None:
        values = [float(item[field]) for item in predictions if item.get(field) is not None]
        if not values:
            return None
        ordered = sorted(values)
        p95_index = min(len(ordered) - 1, int(0.95 * len(ordered)))
        return {
            "mean": round(statistics.mean(values), 4),
            "median": round(statistics.median(values), 4),
            "p95": round(ordered[p95_index], 4),
            "max": round(max(values), 4),
        }
    summary = {
        "latency_s": describe("latency_s"),
        "input_tokens": describe("input_tokens"),
        "output_tokens": describe("output_tokens"),
        "tokens_per_second": describe("tokens_per_second"),
        "peak_gpu_allocated_gib": describe("peak_gpu_allocated_gib"),
        "peak_gpu_reserved_gib": describe("peak_gpu_reserved_gib"),
    }
    summary["truncated_rate"] = (
        sum(bool(item.get("truncated")) for item in predictions) / len(predictions)
        if predictions
        else 0.0
    )
    return summary


def command_evaluate(args: argparse.Namespace) -> int:
    cases = {item["case_id"]: item for item in load_cases(resolve_project_path(args.data))}
    predictions = _read_jsonl(resolve_project_path(args.predictions))
    prediction_ids = [item["case_id"] for item in predictions]
    if len(prediction_ids) != len(set(prediction_ids)):
        raise SystemExit("Plik predykcji zawiera zduplikowane case_id")
    scores = []
    for prediction in predictions:
        case_id = prediction["case_id"]
        if case_id not in cases:
            raise SystemExit(f"Predykcja odwołuje się do nieznanego przypadku {case_id}")
        score = score_prediction(cases[case_id], prediction["response"])
        score["control_type"] = cases[case_id]["control"]["type"]
        score["expected_status"] = cases[case_id]["expected_output"]["status"]
        score["group_id"] = cases[case_id]["group_id"]
        score["boundary_type"] = cases[case_id].get("metadata", {}).get("boundary_type")
        scores.append(score)
    by_control_type = {
        control_type: aggregate_scores([score for score in scores if score["control_type"] == control_type])
        for control_type in sorted({score["control_type"] for score in scores})
    }
    by_expected_status = {
        status: aggregate_scores([score for score in scores if score["expected_status"] == status])
        for status in sorted({score["expected_status"] for score in scores})
    }
    metadata = {
        key: predictions[0].get(key)
        for key in (
            "model_id",
            "model_revision",
            "profile",
            "split",
            "baseline_variant",
            "prompt_style",
            "prompt_sha256",
            "max_new_tokens",
            "do_sample",
            "enable_thinking",
            "parameter_dtype",
        )
    } if predictions else {}
    report = {
        "metadata": metadata,
        "aggregate": aggregate_scores(scores),
        "runtime": _runtime_summary(predictions),
        "by_control_type": by_control_type,
        "by_expected_status": by_expected_status,
        "cases": scores,
    }
    boundary_scores = [score for score in scores if score.get("boundary_type")]
    if boundary_scores:
        policy = json.loads((CONFIG_DIR / "status_policy_v1.json").read_text(encoding="utf-8"))
        report["boundary"] = aggregate_boundary_scores(
            boundary_scores, policy["business_cost_matrix"]
        )
    output = resolve_project_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["aggregate"], ensure_ascii=False, indent=2))
    print(f"Pełny raport: {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Financial Control Copilot — narzędzia warsztatowe")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Wygeneruj deterministyczny zbiór przypadków")
    generate.add_argument("--output", default=str(DEFAULT_OUTPUT))
    generate.set_defaults(func=command_generate)

    validate = subparsers.add_parser("validate-data", help="Sprawdź schemat i spójność przypadków")
    validate.add_argument("--data", default=str(DEFAULT_OUTPUT))
    validate.set_defaults(func=command_validate)

    prompt = subparsers.add_parser("show-prompt", help="Pokaż wiadomości dla wybranego przypadku")
    prompt.add_argument("case_id")
    prompt.add_argument("--variant", choices=["B0", "B1", "B2", "B3"], default="B1")
    prompt.add_argument("--data", default=str(DEFAULT_OUTPUT))
    prompt.set_defaults(func=command_show_prompt)

    evaluate = subparsers.add_parser("evaluate", help="Oceń plik odpowiedzi modelu")
    evaluate.add_argument("predictions")
    evaluate.add_argument("--data", default=str(DEFAULT_OUTPUT))
    evaluate.add_argument("--output", default="results/evaluation.json")
    evaluate.set_defaults(func=command_evaluate)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
