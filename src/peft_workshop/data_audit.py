from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .dataset_v1 import DEFAULT_FULL_OUTPUT
from .paths import RESULTS_DIR, resolve_project_path
from .validation import validate_case


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _content_signature(case: dict[str, Any]) -> str:
    content = {
        "control_type": case["control"]["type"],
        "task": " ".join(case["input"]["task"].lower().split()),
        "sources": [" ".join(item["content"].lower().split()) for item in case["input"]["sources"]],
    }
    encoded = json.dumps(content, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def audit_cases(cases: list[dict[str, Any]], source_path: Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    ids: Counter[str] = Counter(case.get("case_id", "") for case in cases)
    duplicate_ids = sorted(case_id for case_id, count in ids.items() if count > 1)
    if duplicate_ids:
        errors.append(f"Zduplikowane case_id: {', '.join(duplicate_ids)}")

    for case in cases:
        for message in validate_case(case):
            errors.append(f"{case.get('case_id', '<unknown>')}: {message}")

    group_splits: dict[str, set[str]] = defaultdict(set)
    for case in cases:
        group_splits[case["group_id"]].add(case["split"])
    leaking_groups = {
        group_id: sorted(splits)
        for group_id, splits in group_splits.items()
        if len(splits) > 1
    }
    if leaking_groups:
        errors.append(f"Rodziny obecne w wielu splitach: {json.dumps(leaking_groups, ensure_ascii=False)}")

    signatures: dict[str, list[str]] = defaultdict(list)
    for case in cases:
        signatures[_content_signature(case)].append(case["case_id"])
    exact_duplicates = [case_ids for case_ids in signatures.values() if len(case_ids) > 1]
    if exact_duplicates:
        errors.append(f"Dokładnie zduplikowana treść: {exact_duplicates}")

    split_counts = Counter(case["split"] for case in cases)
    type_counts = Counter(case["control"]["type"] for case in cases)
    status_counts = Counter(case["expected_output"]["status"] for case in cases)
    mutation_counts = Counter(
        case.get("metadata", {}).get("mutation_type", "legacy") for case in cases
    )
    difficulty_counts = Counter(case["difficulty"] for case in cases)
    word_lengths = [
        sum(len(item["content"].split()) for item in case["input"]["sources"])
        for case in cases
    ]

    if cases:
        largest_status_share = max(status_counts.values()) / len(cases)
        if largest_status_share > 0.5:
            warnings.append(f"Największa klasa statusu ma {largest_status_share:.1%} zbioru")
    if split_counts.get("train", 0) and split_counts["train"] < 400:
        warnings.append("Split train zawiera mniej niż docelowe 400 przypadków")
    if split_counts.get("challenge", 0):
        injection_count = sum(
            "prompt_injection" in case.get("metadata", {}).get("mutation_type", "")
            for case in cases
            if case["split"] == "challenge"
        )
        if injection_count != split_counts["challenge"]:
            errors.append("Nie wszystkie przypadki challenge zawierają oznaczenie prompt_injection")

    file_sha256 = None
    if source_path is not None and source_path.exists():
        file_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "count": len(cases),
            "split_counts": dict(sorted(split_counts.items())),
            "control_type_counts": dict(sorted(type_counts.items())),
            "status_counts": dict(sorted(status_counts.items())),
            "difficulty_counts": dict(sorted(difficulty_counts.items())),
            "family_count": len(group_splits),
            "mutation_count": len(mutation_counts),
            "mutation_counts": dict(sorted(mutation_counts.items())),
            "source_word_length": {
                "min": min(word_lengths) if word_lengths else 0,
                "mean": round(statistics.mean(word_lengths), 2) if word_lengths else 0,
                "median": round(statistics.median(word_lengths), 2) if word_lengths else 0,
                "max": max(word_lengths) if word_lengths else 0,
            },
            "exact_duplicate_count": len(exact_duplicates),
            "leaking_family_count": len(leaking_groups),
            "file_sha256": file_sha256,
        },
    }


def render_markdown(report: dict[str, Any], data_path: Path) -> str:
    summary = report["summary"]
    lines = [
        "# Raport QA datasetu",
        "",
        f"Źródło: `{data_path.as_posix()}`",
        "",
        f"Status: **{'PASS' if report['valid'] else 'FAIL'}**",
        "",
        "## Podsumowanie",
        "",
        f"- rekordy: {summary['count']}",
        f"- rodziny scenariuszy: {summary['family_count']}",
        f"- rodzaje mutacji: {summary['mutation_count']}",
        f"- dokładne duplikaty: {summary['exact_duplicate_count']}",
        f"- rodziny przeciekające między splitami: {summary['leaking_family_count']}",
        f"- SHA-256: `{summary['file_sha256']}`",
        "",
        "## Splity",
        "",
        "| Split | Liczba |",
        "|---|---:|",
    ]
    lines.extend(f"| {key} | {value} |" for key, value in summary["split_counts"].items())
    lines.extend(["", "## Statusy", "", "| Status | Liczba |", "|---|---:|"])
    lines.extend(f"| {key} | {value} |" for key, value in summary["status_counts"].items())
    lines.extend(["", "## Typy kontroli", "", "| Typ | Liczba |", "|---|---:|"])
    lines.extend(f"| {key} | {value} |" for key, value in summary["control_type_counts"].items())
    lines.extend(["", "## Błędy", ""])
    lines.extend(f"- {item}" for item in report["errors"] or ["Brak."])
    lines.extend(["", "## Ostrzeżenia", ""])
    lines.extend(f"- {item}" for item in report["warnings"] or ["Brak."])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audyt jakości i podziału datasetu")
    parser.add_argument("--data", default=str(DEFAULT_FULL_OUTPUT))
    parser.add_argument("--json-output", default=str(RESULTS_DIR / "dataset_v1_audit.json"))
    parser.add_argument("--markdown-output", default=str(RESULTS_DIR / "dataset_v1_audit.md"))
    args = parser.parse_args()
    data_path = resolve_project_path(args.data)
    report = audit_cases(load_jsonl(data_path), data_path)
    json_output = resolve_project_path(args.json_output)
    markdown_output = resolve_project_path(args.markdown_output)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_output.write_text(render_markdown(report, data_path), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    for warning in report["warnings"]:
        print(f"WARNING: {warning}")
    for error in report["errors"]:
        print(f"ERROR: {error}")
    print(f"Raport: {markdown_output}")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

