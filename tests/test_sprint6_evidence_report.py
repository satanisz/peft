from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from peft_workshop.sprint6_evidence_report import build_shadow_summary


ROOT = Path(__file__).resolve().parents[1]


class Sprint6EvidenceReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.thresholds = json.loads((ROOT / "configs" / "sprint6_evidence_gate_v1.json").read_text(encoding="utf-8"))["shadow_thresholds"]
        cls.cases = [json.loads(line) for line in (ROOT / "data" / "shadow" / "shadow_challenge_v1.jsonl").read_text(encoding="utf-8").splitlines()]

    def _report(self) -> dict:
        rows = [{
            "case_id": case["case_id"], "schema_valid": True, "sources_valid": True,
            "status_correct": True, "severity_correct": True, "human_review_correct": True,
            "predicted_status": case["expected_output"]["status"], "expected_status": case["expected_output"]["status"],
        } for case in self.cases]
        return {
            "aggregate": {
                "count": 50, "macro_f1": 1.0, "schema_valid_rate": 1.0,
                "severity_correct_rate": 1.0, "sources_valid_rate": 1.0,
                "per_status": {status: {"recall": 1.0} for status in ("PASS", "WARN", "FAIL", "INSUFFICIENT_DATA", "NOT_APPLICABLE")},
            },
            "cases": rows,
        }

    def _guarded(self) -> list[dict]:
        return [{"case_id": case["case_id"], "guard": {"decision": "PASS_THROUGH", "issues": [], "guarded_output": case["expected_output"]}} for case in self.cases]

    def test_passing_metrics_still_require_150_response_reviews(self) -> None:
        summary = build_shadow_summary(self.thresholds, [self._report() for _ in range(3)], [self._guarded() for _ in range(3)], None)
        self.assertEqual(summary["decision"], "PENDING_MANUAL_REVIEW")
        self.assertTrue(all(summary["numeric_checks"].values()))

    def test_complete_review_routes_to_sol(self) -> None:
        review = {"reviewed_case_count": 50, "reviewed_response_count": 150, "prompt_injection_followed_count": 0, "critical_error_count": 0, "approved_for_m6_review": True}
        summary = build_shadow_summary(self.thresholds, [self._report() for _ in range(3)], [self._guarded() for _ in range(3)], review)
        self.assertEqual(summary["decision"], "READY_FOR_M6_SOL_REVIEW")

    def test_single_weak_seed_fails_shadow(self) -> None:
        reports = [self._report() for _ in range(3)]
        reports[-1]["aggregate"]["macro_f1"] = 0.70
        summary = build_shadow_summary(self.thresholds, reports, [self._guarded() for _ in range(3)], None)
        self.assertEqual(summary["decision"], "FAILED_SHADOW_THRESHOLDS")
