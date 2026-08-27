from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from peft_workshop.sprint4_report import build_pretest_summary, render_markdown


ROOT = Path(__file__).resolve().parents[1]


class Sprint4ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.matrix = json.loads(
            (ROOT / "configs" / "sprint4_matrix_v1.json").read_text(encoding="utf-8")
        )
        cls.training = json.loads(
            (ROOT / "results" / "sprint3" / "q1_training_metrics.json").read_text(encoding="utf-8")
        )
        cls.original = json.loads(
            (ROOT / "results" / "sprint3" / "q1_original_validation_metrics.json").read_text(
                encoding="utf-8"
            )
        )
        cls.boundary = json.loads(
            (ROOT / "results" / "sprint3" / "q1_boundary_validation_metrics.json").read_text(
                encoding="utf-8"
            )
        )

    def test_three_stable_seeds_open_pretest_gate(self) -> None:
        summary = build_pretest_summary(
            self.matrix,
            [copy.deepcopy(self.training) for _ in range(3)],
            [copy.deepcopy(self.original) for _ in range(3)],
            [copy.deepcopy(self.boundary) for _ in range(3)],
        )

        self.assertEqual(summary["decision"], "READY_TO_OPEN_PROTECTED_SPLITS")
        self.assertFalse(summary["protected_splits_opened"])
        self.assertTrue(summary["automated_gate_only"])
        self.assertIn("review analityczny", render_markdown(summary))

    def test_weak_warn_seed_stops_before_test(self) -> None:
        weak = copy.deepcopy(self.boundary)
        weak["aggregate"]["per_status"]["WARN"]["recall"] = 0.5
        summary = build_pretest_summary(
            self.matrix,
            [copy.deepcopy(self.training) for _ in range(3)],
            [copy.deepcopy(self.original) for _ in range(3)],
            [copy.deepcopy(self.boundary), copy.deepcopy(self.boundary), weak],
        )

        self.assertEqual(summary["decision"], "STOP_AND_RETURN_TO_SOL_HIGH")
        self.assertFalse(summary["checks"]["warn_recall_each_seed"])

    def test_invalid_sources_stop_before_test(self) -> None:
        invalid_sources = copy.deepcopy(self.boundary)
        invalid_sources["aggregate"]["sources_valid_rate"] = 0.98
        summary = build_pretest_summary(
            self.matrix,
            [copy.deepcopy(self.training) for _ in range(3)],
            [copy.deepcopy(self.original) for _ in range(3)],
            [copy.deepcopy(self.boundary), copy.deepcopy(self.boundary), invalid_sources],
        )

        self.assertEqual(summary["decision"], "STOP_AND_RETURN_TO_SOL_HIGH")
        self.assertFalse(summary["checks"]["sources_each_seed"])

    def test_weak_severity_stops_before_test(self) -> None:
        weak_severity = copy.deepcopy(self.original)
        weak_severity["aggregate"]["severity_correct_rate"] = 0.89
        summary = build_pretest_summary(
            self.matrix,
            [copy.deepcopy(self.training) for _ in range(3)],
            [copy.deepcopy(self.original), copy.deepcopy(self.original), weak_severity],
            [copy.deepcopy(self.boundary) for _ in range(3)],
        )

        self.assertEqual(summary["decision"], "STOP_AND_RETURN_TO_SOL_HIGH")
        self.assertFalse(summary["checks"]["severity_each_seed"])


if __name__ == "__main__":
    unittest.main()
