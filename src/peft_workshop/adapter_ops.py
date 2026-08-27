from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .paths import project_relative, resolve_project_path
from .train import load_config


def inspect_adapter(config: dict[str, Any], adapter_path: Path) -> dict[str, Any]:
    adapter_config_path = adapter_path / "adapter_config.json"
    if not adapter_config_path.exists():
        raise FileNotFoundError(f"Brak adapter_config.json w {adapter_path}")
    adapter_config = json.loads(adapter_config_path.read_text(encoding="utf-8"))
    expected_base = config["model"]["id"]
    actual_base = adapter_config.get("base_model_name_or_path")
    files = []
    for path in sorted(item for item in adapter_path.iterdir() if item.is_file()):
        files.append(
            {
                "name": path.name,
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return {
        "adapter_id": config["id"],
        "adapter_path": project_relative(adapter_path),
        "expected_base_model": expected_base,
        "actual_base_model": actual_base,
        "base_model_compatible": actual_base == expected_base,
        "peft_type": adapter_config.get("peft_type"),
        "rank": adapter_config.get("r"),
        "alpha": adapter_config.get("lora_alpha"),
        "target_modules": adapter_config.get("target_modules"),
        "files": files,
        "total_bytes": sum(item["bytes"] for item in files),
    }


def merge_adapter(config: dict[str, Any], adapter_path: Path, output_path: Path) -> dict[str, Any]:
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as error:
        raise SystemExit("Brakuje zależności treningowych. Uruchom: uv sync --extra llm --extra train") from error

    if not torch.cuda.is_available():
        raise RuntimeError("Scalanie referencyjne wymaga GPU CUDA")
    model_config = config["model"]
    base = AutoModelForCausalLM.from_pretrained(
        model_config["id"],
        revision=model_config["revision"],
        device_map={"": 0},
        dtype=torch.bfloat16,
        attn_implementation=model_config.get("attn_implementation", "sdpa"),
    )
    peft_model = PeftModel.from_pretrained(base, adapter_path)
    merged = peft_model.merge_and_unload(safe_merge=True)
    output_path.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(output_path, safe_serialization=True, max_shard_size="4GB")
    tokenizer = AutoTokenizer.from_pretrained(adapter_path)
    tokenizer.save_pretrained(output_path)
    config_path = output_path / "config.json"
    return {
        "adapter_id": config["id"],
        "adapter_path": project_relative(adapter_path),
        "merged_path": project_relative(output_path),
        "dtype": "torch.bfloat16",
        "safe_merge": True,
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "total_bytes": sum(path.stat().st_size for path in output_path.rglob("*") if path.is_file()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspekcja i bezpieczne scalanie adapterów Sprintu 3")
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("--config", required=True)
    inspect_parser.add_argument("--adapter")
    inspect_parser.add_argument("--output")
    merge_parser = subparsers.add_parser("merge")
    merge_parser.add_argument("--config", required=True)
    merge_parser.add_argument("--adapter")
    merge_parser.add_argument("--output", required=True)
    merge_parser.add_argument("--manifest")
    args = parser.parse_args()
    config, _ = load_config(args.config)
    adapter_path = resolve_project_path(args.adapter or config["artifacts"]["output_dir"])
    if args.command == "inspect":
        report = inspect_adapter(config, adapter_path)
        if not report["base_model_compatible"]:
            raise RuntimeError("Adapter wskazuje inny model bazowy niż konfiguracja")
        output_arg = args.output
    else:
        output_path = resolve_project_path(args.output)
        report = merge_adapter(config, adapter_path, output_path)
        output_arg = args.manifest
    if output_arg:
        output = resolve_project_path(output_arg)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
