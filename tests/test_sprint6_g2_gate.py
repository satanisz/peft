from __future__ import annotations

import unittest

from peft_workshop.sprint6_g2_gate import build_g2_report


class Sprint6G2GateTests(unittest.TestCase):
    def test_technical_readiness_passes_without_protected_read(self) -> None:
        report = build_g2_report()
        self.assertEqual(report["decision"], "S6_G2_PASS")
        self.assertTrue(all(report["checks"].values()))
        self.assertFalse(report["protected_content_read"])
        self.assertFalse(report["inference_run"])

    def test_failure_rehearsal_has_fallback_for_each_scenario(self) -> None:
        report = build_g2_report()
        scenarios = report["failure_rehearsal"]["scenarios"]
        self.assertEqual(set(scenarios), {"oom", "missing_model", "checkpoint_error", "offline_cache"})
        self.assertTrue(all(item["caught"] and item["fallback"] for item in scenarios.values()))


if __name__ == "__main__":
    unittest.main()
