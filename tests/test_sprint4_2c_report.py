from __future__ import annotations

import unittest

from peft_workshop.sprint4_2c_report import build_report


class Sprint42CReportTests(unittest.TestCase):
    def test_report_routes_fc209_without_opening_protected_evidence(self) -> None:
        report = build_report()
        self.assertEqual(
            report["demo_decision"],
            "READY_FOR_SPRINT5_DEMO_WITH_PROTECTED_HOLD",
        )
        self.assertEqual(report["protected_evidence_decision"], "HOLD")
        self.assertFalse(report["protected_splits_opened"])
        self.assertTrue(report["checks"]["fc209_blocked_each_seed"])
        self.assertTrue(report["checks"]["blocked_output_never_accepted"])
        self.assertEqual(
            [item["guard"]["blocked_count"] for item in report["seeds"]],
            [1, 1, 1],
        )


if __name__ == "__main__":
    unittest.main()
