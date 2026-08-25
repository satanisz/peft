from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from .cases import DEFAULT_OUTPUT, load_cases
from .paths import CONFIG_DIR, RESULTS_DIR, resolve_project_path
from .prompts import build_messages, select_demonstrations


def _load_model_config(profile: str) -> dict[str, Any]:
    configs = json.loads((CONFIG_DIR / "models.json").read_text(encoding="utf-8"))
    return configs[profile]


def run_baseline(args: argparse.Namespace) -> Path:
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as error:
        raise SystemExit(
            "Brakuje zależności LLM. Uruchom: uv sync --extra llm"
        ) from error

    config = _load_model_config(args.profile)
    model_id = args.model or config["model_id"]
    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=config["revision"])
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        revision=config["revision"],
        device_map="auto",
        dtype="auto",
    )
    model.eval()

    all_cases = load_cases(resolve_project_path(args.data))
    selected = [case for case in all_cases if args.split == "all" or case["split"] == args.split]
    if args.limit:
        selected = selected[: args.limit]
    output = resolve_project_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for index, case in enumerate(selected, start=1):
            demos = select_demonstrations(case, all_cases) if args.mode == "few-shot" else []
            messages = build_messages(case, demos)
            template_options: dict[str, Any] = {}
            if "enable_thinking" in config:
                template_options["enable_thinking"] = config["enable_thinking"]
            inputs = tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                return_tensors="pt",
                return_dict=True,
                **template_options,
            ).to(model.device)
            started = time.perf_counter()
            with torch.inference_mode():
                generated = model.generate(
                    **inputs,
                    max_new_tokens=args.max_new_tokens or config["max_new_tokens"],
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                )
            latency = time.perf_counter() - started
            new_tokens = generated[0, inputs["input_ids"].shape[1]:]
            response = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
            record = {
                "case_id": case["case_id"],
                "model_id": model_id,
                "mode": args.mode,
                "response": response,
                "latency_s": round(latency, 4),
                "input_tokens": int(inputs["input_ids"].shape[1]),
                "output_tokens": int(new_tokens.shape[0]),
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"[{index}/{len(selected)}] {case['case_id']} — {latency:.2f}s")
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Uruchom baseline zero-shot lub few-shot")
    parser.add_argument("--profile", choices=["smoke", "workshop"], default="smoke")
    parser.add_argument("--model", help="Opcjonalne nadpisanie model_id")
    parser.add_argument("--mode", choices=["zero-shot", "few-shot"], default="zero-shot")
    parser.add_argument("--split", choices=["train", "development", "validation", "test", "challenge", "all"], default="test")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--max-new-tokens", type=int)
    parser.add_argument("--data", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--output", default=str(RESULTS_DIR / "baseline.jsonl"))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = run_baseline(args)
    print(f"Zapisano odpowiedzi: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
