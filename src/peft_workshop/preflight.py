from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import sys
from pathlib import Path
from typing import Any

from .paths import RESULTS_DIR, resolve_project_path


def collect_environment() -> dict[str, Any]:
    report: dict[str, Any] = {
        "python": sys.version,
        "platform": platform.platform(),
        "packages": {},
        "cuda": {"available": False},
    }
    for package in (
        "torch",
        "transformers",
        "accelerate",
        "jsonschema",
        "bitsandbytes",
        "peft",
        "trl",
        "datasets",
    ):
        try:
            report["packages"][package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            report["packages"][package] = None

    try:
        import torch
    except ImportError:
        return report

    report["cuda"] = {
        "available": torch.cuda.is_available(),
        "torch_cuda_version": torch.version.cuda,
    }
    if torch.cuda.is_available():
        properties = torch.cuda.get_device_properties(0)
        report["cuda"].update(
            {
                "device_name": properties.name,
                "compute_capability": f"{properties.major}.{properties.minor}",
                "total_memory_gib": round(properties.total_memory / 1024**3, 2),
            }
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Zapisz informacje o środowisku eksperymentu")
    parser.add_argument("--output", default=str(RESULTS_DIR / "environment.json"))
    args = parser.parse_args()
    report = collect_environment()
    output = resolve_project_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Zapisano: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

