from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from peft_workshop.sprint4_preflight import _training_contract, build_preflight


ROOT = Path(__file__).resolve().parents[1]


class Sprint4PreflightTests(unittest.TestCase):
    def test_frozen_matrix_is_ready_when_git_clean_check_is_disabled(self) -> None:
        result = build_preflight(require_clean_git=False)

        self.assertEqual(result["decision"], "READY_FOR_TRAINING")
        self.assertFalse(result["protected_splits_opened"])
        self.assertEqual([item["action"] for item in result["run_queue"]], ["reuse", "train", "train"])

    def test_seed_is_the_only_training_contract_difference(self) -> None:
        first = json.loads((ROOT / "configs" / "qlora_q1_v1.json").read_text(encoding="utf-8"))
        second = json.loads(
            (ROOT / "configs" / "qlora_q1_seed_20260828_v1.json").read_text(encoding="utf-8")
        )

        self.assertNotEqual(first["training"]["seed"], second["training"]["seed"])
        self.assertEqual(_training_contract(first), _training_contract(second))

    def test_hyperparameter_change_is_detected(self) -> None:
        first = json.loads((ROOT / "configs" / "qlora_q1_v1.json").read_text(encoding="utf-8"))
        changed = copy.deepcopy(first)
        changed["lora"]["rank"] = 8

        self.assertNotEqual(_training_contract(first), _training_contract(changed))


if __name__ == "__main__":
    unittest.main()
