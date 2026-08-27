from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .paths import project_relative, resolve_project_path
from .prompts import STATUS_AWARE_SYSTEM_PROMPT, build_messages


FORBIDDEN_TRAIN_PATH_PARTS = {"test", "challenge", "validation", "development"}
ALLOWED_STATUSES = {
    "PASS",
    "WARN",
    "FAIL",
    "INSUFFICIENT_DATA",
    "NOT_APPLICABLE",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_train_source(source: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = resolve_project_path(source["path"])
    lowered_parts = {part.lower() for part in path.parts} | {path.stem.lower()}
    if lowered_parts & FORBIDDEN_TRAIN_PATH_PARTS:
        raise ValueError(f"Źródło treningowe wskazuje chroniony split: {path}")
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if not cases:
        raise ValueError(f"Puste źródło treningowe: {path}")
    invalid_splits = sorted({case.get("split") for case in cases if case.get("split") != "train"})
    if invalid_splits:
        raise ValueError(f"Źródło {path} zawiera splity inne niż train: {invalid_splits}")
    return cases, {
        "name": source["name"],
        "path": project_relative(path),
        "sha256": _sha256(path),
        "case_count": len(cases),
    }


def _stratified_limit(cases: list[dict[str, Any]], max_cases: int, seed: int) -> list[dict[str, Any]]:
    import random

    pools: dict[str, list[dict[str, Any]]] = {status: [] for status in sorted(ALLOWED_STATUSES)}
    for case in cases:
        pools[case["expected_output"]["status"]].append(case)
    rng = random.Random(seed)
    for pool in pools.values():
        rng.shuffle(pool)
    selected: list[dict[str, Any]] = []
    while len(selected) < max_cases and any(pools.values()):
        for status in sorted(pools):
            if pools[status] and len(selected) < max_cases:
                selected.append(pools[status].pop())
    return selected


def load_training_cases(config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    case_sources: dict[str, str] = {}
    for source in config["dataset"]["train_sources"]:
        source_cases, source_audit = _read_train_source(source)
        sources.append(source_audit)
        for case in source_cases:
            if case["case_id"] in case_sources:
                raise ValueError(f"Zduplikowany case_id w treningu: {case['case_id']}")
            case_sources[case["case_id"]] = source["name"]
            enriched = dict(case)
            enriched["_training_source"] = source["name"]
            cases.append(enriched)

    max_cases = config["dataset"].get("max_cases")
    if max_cases is not None and len(cases) > max_cases:
        selection = config["dataset"].get("selection", "stratified_status")
        if selection != "stratified_status":
            raise ValueError(f"Nieobsługiwana metoda wyboru próbki: {selection}")
        cases = _stratified_limit(cases, int(max_cases), int(config["training"]["seed"]))

    statuses = {case["expected_output"]["status"] for case in cases}
    unknown = statuses - ALLOWED_STATUSES
    if unknown:
        raise ValueError(f"Nieznane statusy treningowe: {sorted(unknown)}")
    if config["dataset"].get("require_all_statuses", True) and statuses != ALLOWED_STATUSES:
        raise ValueError(f"Trening nie pokrywa pięciu statusów: {sorted(statuses)}")

    audit = {
        "variant": config["id"],
        "sources": sources,
        "selected_case_count": len(cases),
        "group_count": len({case["group_id"] for case in cases}),
        "status_counts": dict(sorted(Counter(case["expected_output"]["status"] for case in cases).items())),
        "source_counts": dict(sorted(Counter(case["_training_source"] for case in cases).items())),
        "control_type_counts": dict(sorted(Counter(case["control"]["type"] for case in cases).items())),
        "case_ids_sha256": hashlib.sha256(
            "\n".join(sorted(case["case_id"] for case in cases)).encode("utf-8")
        ).hexdigest(),
        "system_prompt_sha256": hashlib.sha256(STATUS_AWARE_SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
        "opened_splits": ["train"],
        "protected_splits_opened": False,
    }
    return cases, audit


def build_sft_records(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for case in cases:
        clean_case = {key: value for key, value in case.items() if not key.startswith("_")}
        records.append(
            {
                "case_id": clean_case["case_id"],
                "training_source": case.get("_training_source"),
                "status": clean_case["expected_output"]["status"],
                "prompt": build_messages(clean_case, prompt_style="status_aware"),
                "completion": [
                    {
                        "role": "assistant",
                        "content": json.dumps(clean_case["expected_output"], ensure_ascii=False),
                    }
                ],
                "chat_template_kwargs": {"enable_thinking": False},
            }
        )
    return records


def collect_sft_token_stats(
    records: list[dict[str, Any]], tokenizer: Any, max_length: int
) -> dict[str, Any]:
    import statistics

    prompt_lengths: list[int] = []
    total_lengths: list[int] = []
    for record in records:
        prompt_lengths.append(
            len(
                tokenizer.apply_chat_template(
                    record["prompt"],
                    tokenize=True,
                    return_dict=False,
                    add_generation_prompt=True,
                    **record["chat_template_kwargs"],
                )
            )
        )
        total_lengths.append(
            len(
                tokenizer.apply_chat_template(
                    record["prompt"] + record["completion"],
                    tokenize=True,
                    return_dict=False,
                    **record["chat_template_kwargs"],
                )
            )
        )

    def describe(values: list[int]) -> dict[str, float | int]:
        ordered = sorted(values)
        return {
            "min": min(ordered),
            "mean": round(statistics.mean(ordered), 2),
            "p95": ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))],
            "max": max(ordered),
        }

    return {
        "max_length": max_length,
        "prompt_tokens": describe(prompt_lengths),
        "total_tokens": describe(total_lengths),
        "total_tokens_one_epoch": sum(total_lengths),
        "truncated_case_count": sum(length > max_length for length in total_lengths),
        "truncated_case_rate": sum(length > max_length for length in total_lengths) / len(total_lengths),
    }
