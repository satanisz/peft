from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from peft_workshop.sprint3_report import build_summary, render_markdown


ROOT = Path(__file__).resolve().parents[1]


class Sprint3ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.b3 = json.loads(
            (ROOT / "results" / "b3_boundary_validation_metrics.json").read_text(encoding="utf-8")
        )

    def test_efficiency_alternative_can_pass_m3(self) -> None:
        q1 = copy.deepcopy(self.b3)
        q1["runtime"]["input_tokens"]["mean"] = 1400
        training = {
            "status": "completed",
            "token_stats": {"truncated_case_count": 0},
            "peak_gpu_allocated_gib": 8.0,
            "wall_clock_seconds": 1200,
        }
        demo = {"wall_clock_seconds": 120}
        reload_smoke = {"aggregate": {"schema_valid_rate": 1.0}}
        summary = build_summary(
            self.b3,
            self.b3,
            q1,
            q1,
            training,
            training,
            demo,
            reload_smoke,
            self.b3,
        )
        self.assertEqual(summary["decision"], "PASS")
        self.assertGreater(summary["efficiency"]["q1_input_token_reduction_vs_b3"], 0.30)
        self.assertIn("Oryginalny test", render_markdown(summary))

    def test_warn_regression_fails_m3(self) -> None:
        q1 = copy.deepcopy(self.b3)
        q1["runtime"]["input_tokens"]["mean"] = 1400
        q1["aggregate"]["per_status"]["WARN"]["recall"] = 0.5
        training = {
            "status": "completed",
            "token_stats": {"truncated_case_count": 0},
            "peak_gpu_allocated_gib": 8.0,
            "wall_clock_seconds": 1200,
        }
        summary = build_summary(
            self.b3,
            self.b3,
            q1,
            q1,
            training,
            training,
            {"wall_clock_seconds": 120},
            {"aggregate": {"schema_valid_rate": 1.0}},
            self.b3,
        )
        self.assertEqual(summary["decision"], "FAIL_REVIEW_Q1B")
        self.assertFalse(summary["checks"]["warn_recall_no_regression"])


if __name__ == "__main__":
    unittest.main()
