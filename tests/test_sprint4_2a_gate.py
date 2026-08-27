from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from peft_workshop.sprint4_2a_gate import build_gate


ROOT = Path(__file__).resolve().parents[1]


class Sprint42AGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads((ROOT / "configs" / "q2_source_guard_v1.json").read_text(encoding="utf-8"))
        cls.base_metrics = {
            "aggregate": {
                "count": 30,
                "schema_valid_rate": 1.0,
                "macro_f1": 0.9,
                "sources_valid_rate": 1.0,
                "severity_correct_rate": 0.95,
            }
        }
        cls.guard = {"blocked_output_accepted_count": 0}
        cls.review = json.loads((ROOT / "data" / "reviews" / "diagnostic_set_v1_review.json").read_text(encoding="utf-8"))

    def test_pending_review_takes_precedence_over_missing_results(self) -> None:
        gate = build_gate(self.config, None, None, self.review)
        self.assertEqual(gate["decision"], "HOLD_PENDING_INDEPENDENT_REVIEW")

    def test_numeric_success_still_requires_independent_review(self) -> None:
        gate = build_gate(self.config, [copy.deepcopy(self.base_metrics) for _ in range(3)], [copy.deepcopy(self.guard) for _ in range(3)], self.review)
        self.assertEqual(gate["decision"], "HOLD_PENDING_INDEPENDENT_REVIEW")

    def test_complete_review_routes_to_sol_high_not_auto_approval(self) -> None:
        review = copy.deepcopy(self.review)
        review["reviewer_independent_from_authoring"] = True
        review["summary"] = {
            "reviewed_case_count": 30,
            "approved_case_count": 30,
            "critical_error_count": 0,
            "prompt_injection_followed_count": 0,
            "approved_for_q2_validation": True,
        }
        gate = build_gate(self.config, [copy.deepcopy(self.base_metrics) for _ in range(3)], [copy.deepcopy(self.guard) for _ in range(3)], review)
        self.assertEqual(gate["decision"], "READY_FOR_SOL_HIGH_APPROVAL_REVIEW")
        self.assertFalse(gate["automatic_approval"])


if __name__ == "__main__":
    unittest.main()
