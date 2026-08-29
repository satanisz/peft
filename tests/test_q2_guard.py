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
        cls.fc209 = next(
            json.loads(line)
            for line in (ROOT / "data" / "diagnostic" / "diagnostic_set_v1.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if json.loads(line)["case_id"] == "FC-209"
        )
        cls.fc209_rule = json.loads(
            (ROOT / "configs" / "deterministic_decision_rules_v1.json").read_text(
                encoding="utf-8"
            )
        )["rules_by_case_id"]["FC-209"]
        cls.shadow_cases = {
            row["case_id"]: row
            for row in (
                json.loads(line)
                for line in (ROOT / "data" / "shadow" / "shadow_challenge_v1.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            )
        }
        cls.shadow_rules = json.loads(
            (ROOT / "configs" / "shadow_deterministic_rules_v1.json").read_text(encoding="utf-8")
        )["rules_by_case_id"]

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

    def test_deterministic_decision_rule_blocks_status_contradiction(self) -> None:
        output = copy.deepcopy(self.fc209["expected_output"])
        output["status"] = "PASS"
        output["severity"] = "NONE"
        output["requires_human_review"] = False
        result = assess_response(
            self.fc209,
            json.dumps(output, ensure_ascii=False),
            enforce_status_severity=True,
            status_policy=self.policy,
            decision_rule=self.fc209_rule,
        )
        self.assertEqual(result["decision"], "BLOCK_FOR_HUMAN_REVIEW")
        self.assertIsNone(result["guarded_output"])
        self.assertEqual(
            result["deterministic_decision"]["required_status"], "FAIL"
        )
        self.assertIn(
            "DETERMINISTIC_DECISION_MISMATCH",
            {item["code"] for item in result["issues"]},
        )

    def test_deterministic_decision_rule_passes_consistent_status(self) -> None:
        result = assess_response(
            self.fc209,
            json.dumps(self.fc209["expected_output"], ensure_ascii=False),
            enforce_status_severity=True,
            status_policy=self.policy,
            decision_rule=self.fc209_rule,
        )
        self.assertEqual(result["decision"], "PASS_THROUGH")
        self.assertEqual(result["deterministic_decision"]["required_status"], "FAIL")

    def test_deterministic_decision_rule_blocks_changed_numeric_result(self) -> None:
        output = copy.deepcopy(self.fc209["expected_output"])
        output["calculation"]["result"] = 4
        result = assess_response(
            self.fc209,
            json.dumps(output, ensure_ascii=False),
            enforce_status_severity=True,
            status_policy=self.policy,
            decision_rule=self.fc209_rule,
        )
        self.assertEqual(result["decision"], "BLOCK_FOR_HUMAN_REVIEW")
        self.assertIn(
            "DETERMINISTIC_RESULT_MISMATCH",
            {item["code"] for item in result["issues"]},
        )

    def test_shadow_band_rules_accept_all_frozen_gold_outputs(self) -> None:
        for case_id, rule in self.shadow_rules.items():
            case = self.shadow_cases[case_id]
            with self.subTest(case_id=case_id):
                result = assess_response(
                    case,
                    json.dumps(case["expected_output"], ensure_ascii=False),
                    enforce_status_severity=True,
                    status_policy=self.policy,
                    decision_rule=rule,
                )
                self.assertEqual(result["decision"], "PASS_THROUGH")

    def test_shadow_band_rule_blocks_material_pass(self) -> None:
        case = self.shadow_cases["FC-305"]
        output = copy.deepcopy(case["expected_output"])
        output.update({"status": "PASS", "severity": "NONE", "requires_human_review": False})
        result = assess_response(
            case,
            json.dumps(output, ensure_ascii=False),
            enforce_status_severity=True,
            status_policy=self.policy,
            decision_rule=self.shadow_rules["FC-305"],
        )
        self.assertEqual(result["decision"], "BLOCK_FOR_HUMAN_REVIEW")
        self.assertIn("DETERMINISTIC_DECISION_MISMATCH", {item["code"] for item in result["issues"]})


if __name__ == "__main__":
    unittest.main()
