from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.metadata
import json
import subprocess
import time
from pathlib import Path
from typing import Any

from .paths import RESULTS_DIR, project_relative, resolve_project_path
from .training_data import build_sft_records, collect_sft_token_stats, load_training_cases


def load_config(path: str | Path) -> tuple[dict[str, Any], Path]:
    resolved = resolve_project_path(path)
    config = json.loads(resolved.read_text(encoding="utf-8"))
    required = {"id", "model", "dataset", "quantization", "lora", "training", "artifacts"}
    missing = required - set(config)
    if missing:
        raise ValueError(f"Konfiguracja treningu nie zawiera pól: {sorted(missing)}")
    return config, resolved


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, encoding="utf-8"
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for name in ("torch", "transformers", "accelerate", "bitsandbytes", "peft", "trl", "datasets"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def _file_manifest(directory: Path) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for path in sorted(item for item in directory.rglob("*") if item.is_file()):
        files.append(
            {
                "path": str(path.relative_to(directory)),
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return files


def run_training(
    config: dict[str, Any],
    config_path: Path,
    *,
    max_steps_override: int | None = None,
    output_dir_override: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    cases, data_audit = load_training_cases(config)
    records = build_sft_records(cases)
    config_hash = hashlib.sha256(config_path.read_bytes()).hexdigest()
    result: dict[str, Any] = {
        "run_id": config["id"],
        "config_path": project_relative(config_path),
        "config_sha256": config_hash,
        "git_commit_at_start": _git_commit(),
        "dataset_audit": data_audit,
        "packages": _package_versions(),
        "status": "dry_run" if dry_run else "initializing",
    }
    if dry_run:
        return result

    try:
        import torch
        from datasets import Dataset
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, set_seed
        from trl import SFTConfig, SFTTrainer
    except ImportError as error:
        raise SystemExit("Brakuje zależności treningowych. Uruchom: uv sync --extra llm --extra train") from error

    if not torch.cuda.is_available():
        raise RuntimeError("QLoRA wymaga GPU CUDA")
    if not torch.cuda.is_bf16_supported():
        raise RuntimeError("Konfiguracja Sprintu 3 wymaga obsługi BF16")

    seed = int(config["training"]["seed"])
    set_seed(seed)
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    model_config = config["model"]
    quant = config["quantization"]
    tokenizer = AutoTokenizer.from_pretrained(model_config["id"], revision=model_config["revision"])
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    token_stats = collect_sft_token_stats(records, tokenizer, int(config["training"]["max_length"]))
    result["token_stats"] = token_stats
    if token_stats["truncated_case_count"] and not config["training"].get("allow_truncation", False):
        raise ValueError(
            f"Max length obcina {token_stats['truncated_case_count']} przypadków; "
            "zwiększ limit albo jawnie dopuść truncation"
        )
    compute_dtype = getattr(torch, quant["compute_dtype"])
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type=quant["quant_type"],
        bnb_4bit_use_double_quant=bool(quant["double_quant"]),
        bnb_4bit_compute_dtype=compute_dtype,
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_config["id"],
        revision=model_config["revision"],
        quantization_config=bnb_config,
        device_map={"": 0},
        dtype=compute_dtype,
        attn_implementation=model_config.get("attn_implementation", "sdpa"),
    )
    model.config.use_cache = False
    gradient_kwargs = {"use_reentrant": False}
    model = prepare_model_for_kbit_training(
        model,
        use_gradient_checkpointing=bool(config["training"]["gradient_checkpointing"]),
        gradient_checkpointing_kwargs=gradient_kwargs,
    )
    lora = config["lora"]
    peft_config = LoraConfig(
        r=int(lora["rank"]),
        lora_alpha=int(lora["alpha"]),
        lora_dropout=float(lora["dropout"]),
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=lora["target_modules"],
    )
    model = get_peft_model(model, peft_config)
    trainable = sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
    total = sum(parameter.numel() for parameter in model.parameters())
    result["model"] = {
        "id": model_config["id"],
        "revision": model_config["revision"],
        "trainable_parameters": trainable,
        "total_parameters_visible": total,
        "trainable_percent": round(100 * trainable / total, 6),
    }

    output_dir = resolve_project_path(output_dir_override or config["artifacts"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    training = config["training"]
    max_steps = max_steps_override if max_steps_override is not None else int(training.get("max_steps", -1))
    sft_args = SFTConfig(
        output_dir=str(output_dir),
        run_name=config["id"],
        per_device_train_batch_size=int(training["micro_batch_size"]),
        gradient_accumulation_steps=int(training["gradient_accumulation_steps"]),
        num_train_epochs=float(training["epochs"]),
        max_steps=max_steps,
        learning_rate=float(training["learning_rate"]),
        lr_scheduler_type=training["lr_scheduler"],
        warmup_steps=int(training["warmup_steps"]),
        optim=training["optimizer"],
        weight_decay=float(training["weight_decay"]),
        max_grad_norm=float(training["max_grad_norm"]),
        bf16=True,
        tf32=True,
        gradient_checkpointing=bool(training["gradient_checkpointing"]),
        gradient_checkpointing_kwargs=gradient_kwargs,
        use_cache=False,
        logging_strategy="steps",
        logging_steps=int(training["logging_steps"]),
        logging_first_step=True,
        include_num_input_tokens_seen=True,
        eval_strategy="no",
        save_strategy=training["save_strategy"],
        save_steps=int(training.get("save_steps", 100)),
        save_total_limit=int(training["save_total_limit"]),
        save_only_model=bool(training.get("save_only_model", False)),
        report_to="none",
        seed=seed,
        data_seed=seed,
        max_length=int(training["max_length"]),
        packing=bool(training["packing"]),
        completion_only_loss=True,
        assistant_only_loss=False,
        pad_to_multiple_of=8,
        dataset_num_proc=1,
        dataloader_num_workers=0,
        remove_unused_columns=True,
    )
    dataset = Dataset.from_list(records)
    trainer = SFTTrainer(
        model=model,
        args=sft_args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )
    started = time.perf_counter()
    train_output = trainer.train(resume_from_checkpoint=training.get("resume_from_checkpoint"))
    torch.cuda.synchronize()
    runtime = time.perf_counter() - started
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    result.update(
        {
            "status": "completed",
            "training_metrics": train_output.metrics,
            "wall_clock_seconds": round(runtime, 3),
            "peak_gpu_allocated_gib": round(torch.cuda.max_memory_allocated() / 1024**3, 3),
            "peak_gpu_reserved_gib": round(torch.cuda.max_memory_reserved() / 1024**3, 3),
            "effective_batch_size": int(training["micro_batch_size"])
            * int(training["gradient_accumulation_steps"]),
        "max_length": int(training["max_length"]),
            "adapter_dir": project_relative(output_dir),
            "adapter_files": _file_manifest(output_dir),
            "log_history": trainer.state.log_history,
        }
    )
    del trainer, model, dataset
    gc.collect()
    torch.cuda.empty_cache()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Powtarzalny trening LoRA/QLoRA dla warsztatu PEFT")
    parser.add_argument("--config", required=True)
    parser.add_argument("--max-steps", type=int, help="Nadpisanie wyłącznie do kontrolowanego smoke testu")
    parser.add_argument("--output-dir")
    parser.add_argument("--metrics-output")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    config, config_path = load_config(args.config)
    result = run_training(
        config,
        config_path,
        max_steps_override=args.max_steps,
        output_dir_override=args.output_dir,
        dry_run=args.dry_run,
    )
    metrics_path = resolve_project_path(
        args.metrics_output or config["artifacts"].get("metrics_output", RESULTS_DIR / f"{config['id']}_training.json")
    )
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: result.get(key) for key in ("run_id", "status", "training_metrics", "wall_clock_seconds", "peak_gpu_allocated_gib", "adapter_dir")}, ensure_ascii=False, indent=2))
    print(f"Pełny raport: {metrics_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
