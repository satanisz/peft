from __future__ import annotations

import json
import unittest
from pathlib import Path

from peft_workshop.training_data import ALLOWED_STATUSES, build_sft_records, load_training_cases


ROOT = Path(__file__).resolve().parents[1]


class TrainingPipelineTests(unittest.TestCase):
    def _config(self, name: str) -> dict:
        return json.loads((ROOT / "configs" / name).read_text(encoding="utf-8"))

    def test_q0_uses_only_original_train(self) -> None:
        cases, audit = load_training_cases(self._config("qlora_q0_v1.json"))
        self.assertEqual(len(cases), 400)
        self.assertEqual(audit["source_counts"], {"dataset-v1": 400})
        self.assertEqual(audit["opened_splits"], ["train"])
        self.assertFalse(audit["protected_splits_opened"])

    def test_q1_combines_original_and_boundary_train(self) -> None:
        cases, audit = load_training_cases(self._config("qlora_q1_v1.json"))
        self.assertEqual(len(cases), 640)
        self.assertEqual(audit["source_counts"], {"boundary-pack-v1": 240, "dataset-v1": 400})
        self.assertEqual(set(audit["status_counts"]), ALLOWED_STATUSES)
        self.assertEqual(audit["status_counts"]["NOT_APPLICABLE"], 48)

    def test_demo_is_balanced_and_bounded(self) -> None:
        cases, audit = load_training_cases(self._config("qlora_demo_v1.json"))
        self.assertEqual(len(cases), 50)
        self.assertEqual(set(audit["status_counts"].values()), {10})

    def test_records_are_prompt_completion_without_label_in_user_prompt(self) -> None:
        cases, _ = load_training_cases(self._config("qlora_q1_v1.json"))
        record = build_sft_records(cases[:1])[0]
        self.assertEqual(record["prompt"][-1]["role"], "user")
        self.assertEqual(record["completion"][0]["role"], "assistant")
        self.assertNotIn('"expected_output"', record["prompt"][-1]["content"])
        self.assertIn('"status"', record["completion"][0]["content"])

    def test_forbidden_split_path_is_rejected(self) -> None:
        config = self._config("qlora_q0_v1.json")
        config["dataset"]["train_sources"][0]["path"] = "data/generated/dataset_v1/test.jsonl"
        with self.assertRaisesRegex(ValueError, "chroniony split"):
            load_training_cases(config)

    def test_all_configs_disallow_truncation(self) -> None:
        for name in ("qlora_q0_v1.json", "qlora_q1_v1.json", "qlora_demo_v1.json"):
            config = self._config(name)
            self.assertFalse(config["training"]["allow_truncation"])
            self.assertGreaterEqual(config["training"]["max_length"], 1728)

    def test_reference_checkpoints_save_adapter_only(self) -> None:
        for name in ("qlora_q0_v1.json", "qlora_q1_v1.json"):
            config = self._config(name)
            self.assertTrue(config["training"]["save_only_model"])


if __name__ == "__main__":
    unittest.main()
