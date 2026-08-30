from __future__ import annotations

import unittest

from peft_workshop.sprint6_evidence_closure import build_closure, validate_closure


class Sprint6EvidenceClosureTests(unittest.TestCase):
    def test_current_failed_evidence_closes_read_only(self) -> None:
        report = validate_closure(build_closure())
        self.assertEqual(report["decision"], "EVIDENCE_V1_CLOSED_READ_ONLY")
        self.assertTrue(all(report["checks"].values()))

    def test_failed_summary_cannot_be_relabelled_pass(self) -> None:
        closure = build_closure()
        closure["status"] = "PASS"
        closure["evidence_decision"] = "PASS"
        report = validate_closure(closure)
        self.assertEqual(report["decision"], "EVIDENCE_V1_CLOSURE_BLOCKED")
        self.assertFalse(report["checks"]["closure_status_is_failed_read_only"])
        self.assertFalse(report["checks"]["closure_decision_matches_failed_summary"])


if __name__ == "__main__":
    unittest.main()
