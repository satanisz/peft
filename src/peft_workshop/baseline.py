from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from .cases import DEFAULT_OUTPUT, load_cases
from .paths import CONFIG_DIR, RESULTS_DIR, resolve_project_path
from .prompts import (
    NAIVE_SYSTEM_PROMPT,
    STATUS_AWARE_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_messages,
    select_demonstrations,
    select_status_demonstrations,
)


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
    variant = args.variant
    if args.mode:
        variant = "B2" if args.mode == "few-shot" else "B1"
    model_id = args.model or config["model_id"]
    max_new_tokens = args.max_new_tokens or config["max_new_tokens"]
    prompt_style = "naive" if variant == "B0" else "status_aware" if variant == "B3" else "full"
    system_prompt = (
        NAIVE_SYSTEM_PROMPT
        if variant == "B0"
        else STATUS_AWARE_SYSTEM_PROMPT
        if variant == "B3"
        else SYSTEM_PROMPT
    )
    prompt_sha256 = hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()
    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=config["revision"])
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        revision=config["revision"],
        device_map="auto",
        dtype="auto",
    )
    model.eval()
    is_cuda = torch.cuda.is_available() and str(model.device).startswith("cuda")

    all_cases = load_cases(resolve_project_path(args.data))
    demonstration_cases = (
        load_cases(resolve_project_path(args.demonstration_data))
        if args.demonstration_data
        else all_cases
    )
    selected = [case for case in all_cases if args.split == "all" or case["split"] == args.split]
    if args.limit:
        selected = selected[: args.limit]
    output = resolve_project_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    if selected and not args.no_warmup:
        warmup_case = selected[0]
        warmup_demos = (
            select_demonstrations(warmup_case, all_cases)
            if variant == "B2"
            else select_status_demonstrations(warmup_case, demonstration_cases)
            if variant == "B3"
            else []
        )
        warmup_messages = build_messages(
            warmup_case,
            warmup_demos,
            prompt_style=prompt_style,
        )
        warmup_options: dict[str, Any] = {}
        if "enable_thinking" in config:
            warmup_options["enable_thinking"] = config["enable_thinking"]
        warmup_inputs = tokenizer.apply_chat_template(
            warmup_messages,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
            **warmup_options,
        ).to(model.device)
        with torch.inference_mode():
            model.generate(
                **warmup_inputs,
                max_new_tokens=8,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        if is_cuda:
            torch.cuda.synchronize()

    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for index, case in enumerate(selected, start=1):
            demos = (
                select_demonstrations(case, all_cases)
                if variant == "B2"
                else select_status_demonstrations(case, demonstration_cases)
                if variant == "B3"
                else []
            )
            messages = build_messages(
                case,
                demos,
                prompt_style=prompt_style,
            )
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
            if is_cuda:
                torch.cuda.reset_peak_memory_stats()
                torch.cuda.synchronize()
            started = time.perf_counter()
            with torch.inference_mode():
                generated = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                )
            if is_cuda:
                torch.cuda.synchronize()
            latency = time.perf_counter() - started
            new_tokens = generated[0, inputs["input_ids"].shape[1]:]
            response = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
            record = {
                "case_id": case["case_id"],
                "split": case["split"],
                "model_id": model_id,
                "model_revision": config["revision"],
                "profile": args.profile,
                "baseline_variant": variant,
                "prompt_style": prompt_style,
                "prompt_sha256": prompt_sha256,
                "demonstration_count": len(demos),
                "demonstration_case_ids": [demo["case_id"] for demo in demos],
                "max_new_tokens": max_new_tokens,
                "do_sample": False,
                "enable_thinking": config.get("enable_thinking"),
                "response": response,
                "latency_s": round(latency, 4),
                "input_tokens": int(inputs["input_ids"].shape[1]),
                "output_tokens": int(new_tokens.shape[0]),
                "truncated": bool(
                    new_tokens.shape[0] >= max_new_tokens
                    and int(new_tokens[-1].item()) != tokenizer.eos_token_id
                ),
                "tokens_per_second": round(float(new_tokens.shape[0]) / latency, 2),
                "peak_gpu_allocated_gib": round(torch.cuda.max_memory_allocated() / 1024**3, 3) if is_cuda else None,
                "peak_gpu_reserved_gib": round(torch.cuda.max_memory_reserved() / 1024**3, 3) if is_cuda else None,
                "parameter_dtype": str(next(model.parameters()).dtype),
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"[{index}/{len(selected)}] {case['case_id']} — {latency:.2f}s")
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Uruchom baseline zero-shot lub few-shot")
    parser.add_argument("--profile", choices=["smoke", "workshop"], default="smoke")
    parser.add_argument("--model", help="Opcjonalne nadpisanie model_id")
    parser.add_argument("--variant", choices=["B0", "B1", "B2", "B3"], default="B0")
    parser.add_argument("--mode", choices=["zero-shot", "few-shot"], help="Przestarzały alias: zero-shot=B1, few-shot=B2")
    parser.add_argument("--split", choices=["train", "development", "validation", "test", "challenge", "all"], default="test")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--max-new-tokens", type=int)
    parser.add_argument("--no-warmup", action="store_true")
    parser.add_argument("--data", default=str(DEFAULT_OUTPUT))
    parser.add_argument(
        "--demonstration-data",
        help="Dataset train z zamrożonymi demonstracjami B3; domyślnie --data",
    )
    parser.add_argument("--output", default=str(RESULTS_DIR / "baseline.jsonl"))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = run_baseline(args)
    print(f"Zapisano odpowiedzi: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
