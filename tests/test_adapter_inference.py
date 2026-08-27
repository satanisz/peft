from __future__ import annotations

import argparse
import unittest

from peft_workshop.adapter_inference import resolve_inference_artifact


class AdapterInferenceTests(unittest.TestCase):
    def test_merged_model_takes_precedence_over_adapter(self) -> None:
        args = argparse.Namespace(
            adapter="artifacts/adapters/ignored",
            merged_model="artifacts/merged/q1-v0.1-bf16",
        )
        artifact_type, model_source, adapter_path = resolve_inference_artifact(
            args, {"artifacts": {"output_dir": "artifacts/adapters/q1-v0.1"}}
        )

        self.assertEqual(artifact_type, "merged")
        self.assertEqual(model_source.name, "q1-v0.1-bf16")
        self.assertIsNone(adapter_path)

    def test_configured_adapter_is_default(self) -> None:
        args = argparse.Namespace(adapter=None, merged_model=None)
        artifact_type, model_source, adapter_path = resolve_inference_artifact(
            args, {"artifacts": {"output_dir": "artifacts/adapters/q1-v0.1"}}
        )

        self.assertEqual(artifact_type, "adapter")
        self.assertEqual(model_source, adapter_path)


if __name__ == "__main__":
    unittest.main()
