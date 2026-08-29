from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from peft_workshop.sprint4_evidence_report import build_evidence_summary


ROOT = Path(__file__).resolve().parents[1]


class Sprint4EvidenceReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.matrix = json.loads(
            (ROOT / "configs" / "sprint4_matrix_v1.json").read_text(encoding="utf-8")
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

    def _reports(self, report: dict) -> list[dict]:
        return [copy.deepcopy(report) for _ in range(3)]

    def test_numeric_success_still_requires_manual_review(self) -> None:
        summary = build_evidence_summary(
            self.matrix,
            self._reports(self.original),
            self._reports(self.boundary),
            self._reports(self.original),
            None,
        )

        self.assertEqual(summary["decision"], "PENDING_MANUAL_REVIEW")

    def test_approved_review_routes_to_sol_not_automatic_pass(self) -> None:
        summary = build_evidence_summary(
            self.matrix,
            self._reports(self.original),
            self._reports(self.boundary),
            self._reports(self.original),
            {
                "reviewed_case_count": 20,
                "reviewed_response_count": 60,
                "prompt_injection_followed_count": 0,
                "critical_error_count": 0,
                "approved_for_m4_review": True,
            },
        )

        self.assertEqual(summary["decision"], "READY_FOR_M4_SOL_REVIEW")

    def test_weak_boundary_evidence_fails(self) -> None:
        weak = copy.deepcopy(self.boundary)
        weak["aggregate"]["macro_f1"] = 0.5
        summary = build_evidence_summary(
            self.matrix,
            self._reports(self.original),
            [copy.deepcopy(self.boundary), copy.deepcopy(self.boundary), weak],
            self._reports(self.original),
            None,
        )

        self.assertEqual(summary["decision"], "FAILED_EVIDENCE_THRESHOLDS")

    def test_invalid_source_integrity_fails_evidence(self) -> None:
        invalid_sources = copy.deepcopy(self.boundary)
        invalid_sources["aggregate"]["sources_valid_rate"] = 0.98
        summary = build_evidence_summary(
            self.matrix,
            self._reports(self.original),
            [copy.deepcopy(self.boundary), copy.deepcopy(self.boundary), invalid_sources],
            self._reports(self.original),
            None,
        )

        self.assertEqual(summary["decision"], "FAILED_EVIDENCE_THRESHOLDS")
        self.assertFalse(summary["numeric_checks"]["evidence_sources_each_seed"])

    def test_weak_challenge_severity_fails_evidence(self) -> None:
        weak_challenge = copy.deepcopy(self.original)
        weak_challenge["aggregate"]["severity_correct_rate"] = 0.80
        summary = build_evidence_summary(
            self.matrix,
            self._reports(self.original),
            self._reports(self.boundary),
            [copy.deepcopy(self.original), copy.deepcopy(self.original), weak_challenge],
            None,
        )

        self.assertEqual(summary["decision"], "FAILED_EVIDENCE_THRESHOLDS")
        self.assertFalse(summary["numeric_checks"]["challenge_severity_each_seed"])


if __name__ == "__main__":
    unittest.main()
