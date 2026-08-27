from __future__ import annotations

import argparse
import unittest
from pathlib import Path
from unittest.mock import patch

from peft_workshop.adapter_inference import (
    load_scoped_cases,
    resolve_inference_artifact,
    validate_inference_scope,
)


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

    def test_protected_split_requires_explicit_authorization(self) -> None:
        cases = [{"split": "test"}]

        with self.assertRaisesRegex(ValueError, "jawnego --allow-protected-split"):
            validate_inference_scope(
                Path("data/generated/dataset_v1/test.jsonl"),
                cases,
                allow_protected_split=False,
            )

        validate_inference_scope(
            Path("data/generated/dataset_v1/test.jsonl"),
            cases,
            allow_protected_split=True,
        )

    def test_protected_path_is_rejected_before_cases_are_loaded(self) -> None:
        with patch("peft_workshop.adapter_inference.load_cases") as mocked_load:
            with self.assertRaisesRegex(ValueError, "jawnego --allow-protected-split"):
                load_scoped_cases(
                    Path("data/generated/dataset_v1/challenge.jsonl"),
                    allow_protected_split=False,
                )
            mocked_load.assert_not_called()


if __name__ == "__main__":
    unittest.main()
