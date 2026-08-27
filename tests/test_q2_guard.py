from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from peft_workshop.q2_guard import assess_response, build_guard_report


ROOT = Path(__file__).resolve().parents[1]


class Q2GuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads(
            (ROOT / "configs" / "status_policy_v1.json").read_text(encoding="utf-8")
        )
        cls.case = json.loads(
            (ROOT / "data" / "diagnostic" / "diagnostic_set_v1.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()[0]
        )
        cls.output = copy.deepcopy(cls.case["expected_output"])

    def _assess(self, output: dict, *, enforce: bool = True) -> dict:
        return assess_response(
            self.case,
            json.dumps(output, ensure_ascii=False),
            enforce_status_severity=enforce,
            status_policy=self.policy,
        )

    def test_valid_response_passes_through(self) -> None:
        result = self._assess(self.output)
        self.assertEqual(result["decision"], "PASS_THROUGH")
        self.assertEqual(result["guarded_output"], self.output)

    def test_unknown_source_is_blocked_without_guessing(self) -> None:
        output = copy.deepcopy(self.output)
        output["evidence"][0]["source_id"] = "diag.999.fabricated"
        result = self._assess(output)
        self.assertEqual(result["decision"], "BLOCK_FOR_HUMAN_REVIEW")
        self.assertIsNone(result["guarded_output"])
        self.assertEqual(result["unknown_source_ids"], ["diag.999.fabricated"])

    def test_severity_policy_can_be_enforced_or_reported_as_legacy(self) -> None:
        output = copy.deepcopy(self.output)
        output["severity"] = "MEDIUM"
        enforced = self._assess(output, enforce=True)
        legacy = self._assess(output, enforce=False)
        self.assertEqual(enforced["decision"], "BLOCK_FOR_HUMAN_REVIEW")
        self.assertEqual(legacy["decision"], "PASS_THROUGH")

    def test_untrusted_deterministic_claim_is_blocked(self) -> None:
        case = copy.deepcopy(self.case)
        case["input"]["deterministic_check"] = None
        result = assess_response(
            case,
            json.dumps(self.output, ensure_ascii=False),
            enforce_status_severity=True,
            status_policy=self.policy,
        )
        self.assertEqual(result["decision"], "BLOCK_FOR_HUMAN_REVIEW")
        self.assertIn(
            "UNTRUSTED_CALCULATION_CLAIM",
            {item["code"] for item in result["issues"]},
        )

    def test_report_counts_blocks(self) -> None:
        passed = {"guard": self._assess(self.output)}
        blocked_output = copy.deepcopy(self.output)
        blocked_output["evidence"][0]["source_id"] = "unknown"
        blocked = {"guard": self._assess(blocked_output)}
        report = build_guard_report([passed, blocked])
        self.assertEqual(report["pass_through_count"], 1)
        self.assertEqual(report["blocked_count"], 1)


if __name__ == "__main__":
    unittest.main()
