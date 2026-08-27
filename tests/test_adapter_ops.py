from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from peft_workshop.adapter_ops import inspect_adapter


class AdapterOpsTests(unittest.TestCase):
    def test_inspection_checks_base_model_and_hashes_files(self) -> None:
        config = {"id": "QX", "model": {"id": "example/base"}}
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir)
            (path / "adapter_config.json").write_text(
                json.dumps(
                    {
                        "base_model_name_or_path": "example/base",
                        "peft_type": "LORA",
                        "r": 8,
                        "lora_alpha": 16,
                        "target_modules": ["q_proj"],
                    }
                ),
                encoding="utf-8",
            )
            (path / "adapter_model.safetensors").write_bytes(b"synthetic-test")
            report = inspect_adapter(config, path)
        self.assertTrue(report["base_model_compatible"])
        self.assertEqual(report["rank"], 8)
        self.assertEqual(len(report["files"][0]["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
