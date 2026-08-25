from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .cases import DEFAULT_OUTPUT, load_cases, write_cases
from .metrics import aggregate_scores, score_prediction
from .paths import resolve_project_path
from .prompts import build_messages, select_demonstrations
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
    demonstrations = select_demonstrations(case, cases) if args.mode == "few-shot" else []
    print(json.dumps(build_messages(case, demonstrations), ensure_ascii=False, indent=2))
    return 0


def command_evaluate(args: argparse.Namespace) -> int:
    cases = {item["case_id"]: item for item in load_cases(resolve_project_path(args.data))}
    predictions = _read_jsonl(resolve_project_path(args.predictions))
    scores = []
    for prediction in predictions:
        case_id = prediction["case_id"]
        if case_id not in cases:
            raise SystemExit(f"Predykcja odwołuje się do nieznanego przypadku {case_id}")
        scores.append(score_prediction(cases[case_id], prediction["response"]))
    report = {"aggregate": aggregate_scores(scores), "cases": scores}
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
    prompt.add_argument("--mode", choices=["zero-shot", "few-shot"], default="zero-shot")
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

