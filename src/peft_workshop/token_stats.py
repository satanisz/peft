from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from .data_audit import load_jsonl
from .dataset_v1 import DEFAULT_FULL_OUTPUT
from .paths import CONFIG_DIR, RESULTS_DIR, resolve_project_path
from .prompts import build_messages


def _describe(values: list[int]) -> dict[str, float | int]:
    ordered = sorted(values)
    if not ordered:
        return {"count": 0, "min": 0, "mean": 0, "median": 0, "p95": 0, "max": 0}
    p95_index = min(len(ordered) - 1, int(0.95 * len(ordered)))
    return {
        "count": len(values),
        "min": min(values),
        "mean": round(statistics.mean(values), 2),
        "median": round(statistics.median(values), 2),
        "p95": ordered[p95_index],
        "max": max(values),
    }


def collect_token_stats(cases: list[dict[str, Any]], tokenizer: Any) -> dict[str, Any]:
    prompt_lengths: dict[str, list[int]] = defaultdict(list)
    target_lengths: dict[str, list[int]] = defaultdict(list)
    total_lengths: dict[str, list[int]] = defaultdict(list)
    for case in cases:
        messages = build_messages(case)
        prompt_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        target_text = json.dumps(case["expected_output"], ensure_ascii=False)
        prompt_count = len(tokenizer.encode(prompt_text, add_special_tokens=False))
        target_count = len(tokenizer.encode(target_text, add_special_tokens=False))
        split = case["split"]
        for key in (split, "all"):
            prompt_lengths[key].append(prompt_count)
            target_lengths[key].append(target_count)
            total_lengths[key].append(prompt_count + target_count)
    return {
        key: {
            "prompt_tokens": _describe(prompt_lengths[key]),
            "target_tokens": _describe(target_lengths[key]),
            "total_tokens": _describe(total_lengths[key]),
            "total_training_tokens_one_epoch": sum(total_lengths[key]),
        }
        for key in sorted(total_lengths)
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Policz długości tokenów datasetu")
    parser.add_argument("--data", default=str(DEFAULT_FULL_OUTPUT))
    parser.add_argument("--profile", choices=["smoke", "workshop"], default="smoke")
    parser.add_argument("--output", default=str(RESULTS_DIR / "dataset_v1_token_stats.json"))
    args = parser.parse_args()
    try:
        from transformers import AutoTokenizer
    except ImportError as error:
        raise SystemExit("Brakuje transformers. Uruchom: uv sync --extra llm") from error
    configs = json.loads((CONFIG_DIR / "models.json").read_text(encoding="utf-8"))
    config = configs[args.profile]
    tokenizer = AutoTokenizer.from_pretrained(config["model_id"], revision=config["revision"])
    stats = collect_token_stats(load_jsonl(resolve_project_path(args.data)), tokenizer)
    output = resolve_project_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"Zapisano: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

