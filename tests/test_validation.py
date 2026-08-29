import hashlib
import json
import unittest

from peft_workshop.cases import build_cases
from peft_workshop.metrics import aggregate_scores, score_prediction
from peft_workshop.paths import CONFIG_DIR
from peft_workshop.prompts import (
    NAIVE_SYSTEM_PROMPT,
    STATUS_AWARE_SYSTEM_PROMPT_V2,
    SYSTEM_PROMPT,
    build_messages,
)
from peft_workshop.validation import extract_json_object


class ValidationTests(unittest.TestCase):
    def test_extract_json_from_code_fence(self) -> None:
        payload = extract_json_object('```json\n{"status":"PASS"}\n```')
        self.assertEqual(payload["status"], "PASS")

    def test_gold_response_scores_perfectly(self) -> None:
        case = build_cases()[0]
        score = score_prediction(case, json.dumps(case["expected_output"], ensure_ascii=False))
        self.assertTrue(score["json_valid"])
        self.assertTrue(score["schema_valid"])
        self.assertTrue(score["sources_valid"])
        self.assertTrue(score["status_correct"])
        self.assertEqual(score["evidence_precision"], 1.0)
        self.assertEqual(score["evidence_recall"], 1.0)

    def test_invalid_text_is_reported(self) -> None:
        score = score_prediction(build_cases()[0], "To nie jest JSON")
        self.assertFalse(score["json_valid"])
        self.assertTrue(score["errors"])

    def test_wrong_evidence_type_does_not_crash(self) -> None:
        case = build_cases()[0]
        payload = dict(case["expected_output"])
        payload["evidence"] = "is.interest"
        score = score_prediction(case, json.dumps(payload, ensure_ascii=False))
        self.assertTrue(score["json_valid"])
        self.assertFalse(score["schema_valid"])
        self.assertFalse(score["sources_valid"])

    def test_aggregate_empty(self) -> None:
        self.assertEqual(aggregate_scores([]), {"count": 0})

    def test_prompt_variants_have_distinct_contracts(self) -> None:
        case = build_cases()[0]
        naive = build_messages(case, prompt_style="naive")
        full = build_messages(case, prompt_style="full")
        self.assertNotIn("Zasady nadrzędne", naive[0]["content"])
        self.assertIn("Zasady nadrzędne", full[0]["content"])
        self.assertNotIn("required_output_contract", naive[-1]["content"])
        self.assertIn("required_output_contract", full[-1]["content"])

    def test_status_aware_v2_freezes_derived_fields_and_source_copying(self) -> None:
        case = build_cases()[0]
        messages = build_messages(case, prompt_style="status_aware_v2")
        contract = messages[0]["content"]
        self.assertEqual(contract, STATUS_AWARE_SYSTEM_PROMPT_V2)
        self.assertIn("FAIL → severity HIGH", contract)
        self.assertIn("nie używaj severity LOW", contract)
        self.assertIn("source_id kopiuj znak w znak", contract)
        self.assertIn("calculation jest obowiązkowe", contract)

    def test_aggregate_reports_macro_f1(self) -> None:
        cases = build_cases()[:2]
        scores = [
            score_prediction(case, json.dumps(case["expected_output"], ensure_ascii=False))
            for case in cases
        ]
        aggregate = aggregate_scores(scores)
        self.assertEqual(aggregate["macro_f1"], 1.0)
        self.assertIn("PASS", aggregate["per_status"])

    def test_frozen_baseline_prompt_hashes_match_code(self) -> None:
        config = json.loads((CONFIG_DIR / "baseline_v1.json").read_text(encoding="utf-8"))
        naive_hash = hashlib.sha256(NAIVE_SYSTEM_PROMPT.encode("utf-8")).hexdigest()
        full_hash = hashlib.sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest()
        self.assertEqual(config["variants"]["B0"]["system_prompt_sha256"], naive_hash)
        self.assertEqual(config["variants"]["B1"]["system_prompt_sha256"], full_hash)
        self.assertEqual(config["variants"]["B2"]["system_prompt_sha256"], full_hash)


if __name__ == "__main__":
    unittest.main()
