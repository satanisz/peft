from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from .cases import load_cases
from .paths import project_relative, resolve_project_path
from .prompts import STATUS_AWARE_SYSTEM_PROMPT, build_messages
from .train import load_config


def run_adapter(args: argparse.Namespace) -> Path:
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    except ImportError as error:
        raise SystemExit("Brakuje zależności treningowych. Uruchom: uv sync --extra llm --extra train") from error

    config, _ = load_config(args.config)
    model_config = config["model"]
    quant = config["quantization"]
    adapter_path = resolve_project_path(args.adapter or config["artifacts"]["output_dir"])
    data_path = resolve_project_path(args.data)
    protected_names = {"test", "boundary_test", "challenge"}
    forbidden = protected_names & ({part.lower() for part in data_path.parts} | {data_path.stem.lower()})
    if forbidden:
        raise ValueError(f"Sprint 3 nie otwiera chronionego splitu: {data_path}")
    cases = load_cases(data_path)
    if any(case["split"] not in {"development", "validation"} for case in cases):
        raise ValueError("Inferencja Sprintu 3 przyjmuje wyłącznie development lub validation")
    if args.limit:
        cases = cases[: args.limit]

    compute_dtype = getattr(torch, quant["compute_dtype"])
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type=quant["quant_type"],
        bnb_4bit_use_double_quant=bool(quant["double_quant"]),
        bnb_4bit_compute_dtype=compute_dtype,
    )
    tokenizer = AutoTokenizer.from_pretrained(adapter_path)
    base_model = AutoModelForCausalLM.from_pretrained(
        model_config["id"],
        revision=model_config["revision"],
        quantization_config=bnb_config,
        device_map={"": 0},
        dtype=compute_dtype,
        attn_implementation=model_config.get("attn_implementation", "sdpa"),
    )
    model = PeftModel.from_pretrained(base_model, adapter_path)
    model.eval()
    model.config.use_cache = True
    output = resolve_project_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    prompt_hash = hashlib.sha256(STATUS_AWARE_SYSTEM_PROMPT.encode("utf-8")).hexdigest()
    max_new_tokens = int(args.max_new_tokens or config["evaluation"]["max_new_tokens"])

    if cases and not args.no_warmup:
        warmup = tokenizer.apply_chat_template(
            build_messages(cases[0], prompt_style="status_aware"),
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
            enable_thinking=False,
        ).to(model.device)
        with torch.inference_mode():
            model.generate(**warmup, max_new_tokens=8, do_sample=False, pad_token_id=tokenizer.eos_token_id)
        torch.cuda.synchronize()

    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for index, case in enumerate(cases, start=1):
            inputs = tokenizer.apply_chat_template(
                build_messages(case, prompt_style="status_aware"),
                add_generation_prompt=True,
                return_tensors="pt",
                return_dict=True,
                enable_thinking=False,
            ).to(model.device)
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
            torch.cuda.synchronize()
            latency = time.perf_counter() - started
            new_tokens = generated[0, inputs["input_ids"].shape[1] :]
            record = {
                "case_id": case["case_id"],
                "split": case["split"],
                "model_id": model_config["id"],
                "model_revision": model_config["revision"],
                "adapter_id": config["id"],
                "adapter_path": project_relative(adapter_path),
                "prompt_style": "status_aware_zero_shot",
                "prompt_sha256": prompt_hash,
                "demonstration_count": 0,
                "max_new_tokens": max_new_tokens,
                "do_sample": False,
                "enable_thinking": False,
                "response": tokenizer.decode(new_tokens, skip_special_tokens=True).strip(),
                "latency_s": round(latency, 4),
                "input_tokens": int(inputs["input_ids"].shape[1]),
                "output_tokens": int(new_tokens.shape[0]),
                "truncated": bool(new_tokens.shape[0] >= max_new_tokens and int(new_tokens[-1]) != tokenizer.eos_token_id),
                "tokens_per_second": round(float(new_tokens.shape[0]) / latency, 2),
                "peak_gpu_allocated_gib": round(torch.cuda.max_memory_allocated() / 1024**3, 3),
                "peak_gpu_reserved_gib": round(torch.cuda.max_memory_reserved() / 1024**3, 3),
                "parameter_dtype": str(next(model.parameters()).dtype),
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"[{index}/{len(cases)}] {case['case_id']} — {latency:.2f}s")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Inferencja adaptera QLoRA bez demonstracji few-shot")
    parser.add_argument("--config", required=True)
    parser.add_argument("--adapter")
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--max-new-tokens", type=int)
    parser.add_argument("--no-warmup", action="store_true")
    args = parser.parse_args()
    output = run_adapter(args)
    print(f"Zapisano odpowiedzi: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
