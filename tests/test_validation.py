import json
import unittest

from peft_workshop.cases import build_cases
from peft_workshop.metrics import aggregate_scores, score_prediction
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


if __name__ == "__main__":
    unittest.main()
