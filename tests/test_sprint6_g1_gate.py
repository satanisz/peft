from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from peft_workshop.sprint6_g1_gate import build_g1_report


class Sprint6G1GateTests(unittest.TestCase):
    def test_pending_human_review_holds_gate(self) -> None:
        report = build_g1_report()
        self.assertEqual(report["decision"], "S6_G1_HOLD_PENDING_HUMAN_SME")
        self.assertTrue(all(report["mechanical_checks"].values()))
        self.assertFalse(report["protected_content_read"])

    def test_complete_independent_review_passes(self) -> None:
        source = Path("data/reviews/shadow_challenge_v1_review.json")
        review = json.loads(source.read_text(encoding="utf-8"))
        review.update({"review_status": "APPROVED_FOR_SHADOW_FREEZE", "reviewer_name": "Test SME", "reviewed_at": "2026-08-29T20:00:00+02:00"})
        for row in review["cases"]:
            row["decision"] = "APPROVED"
            row["critical_error"] = False
        review["summary"] = {"reviewed_case_count": 50, "approved_case_count": 50, "critical_error_count": 0, "approved_for_shadow_freeze": True}
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "review.json"
            target.write_text(json.dumps(review), encoding="utf-8")
            with patch("peft_workshop.sprint6_g1_gate.resolve_project_path", side_effect=lambda value: Path(value) if Path(value).is_absolute() else Path(value)):
                report = build_g1_report(target.resolve())
        self.assertEqual(report["decision"], "S6_G1_PASS")
        self.assertTrue(all(report["human_sme_checks"].values()))

    def test_hash_mismatch_blocks(self) -> None:
        review = json.loads(Path("data/reviews/shadow_challenge_v1_review.json").read_text(encoding="utf-8"))
        review["dataset_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "review.json"
            target.write_text(json.dumps(review), encoding="utf-8")
            with patch("peft_workshop.sprint6_g1_gate.resolve_project_path", side_effect=lambda value: Path(value) if Path(value).is_absolute() else Path(value)):
                report = build_g1_report(target.resolve())
        self.assertEqual(report["decision"], "S6_G1_BLOCKED_AUTHORING_OR_INTEGRITY")


if __name__ == "__main__":
    unittest.main()
