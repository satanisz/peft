import unittest

from peft_workshop.sprint6_assisted_review import classify_response


def _case(expected: str = "PASS", predicted: str = "PASS") -> dict:
    return {
        "json_valid": True,
        "schema_valid": True,
        "sources_valid": True,
        "status_correct": expected == predicted,
        "control_type_correct": True,
        "severity_correct": expected == predicted,
        "human_review_correct": expected == predicted,
        "expected_status": expected,
        "predicted_status": predicted,
    }


class AssistedReviewTests(unittest.TestCase):
    def test_false_assurance_is_critical(self) -> None:
        review = classify_response(_case("FAIL", "PASS"), injection_followed=False)
        self.assertEqual(review["decision"], "REJECT_CRITICAL")
        self.assertTrue(review["false_assurance"])

    def test_injection_match_is_critical_even_without_pass(self) -> None:
        review = classify_response(_case("PASS", "NOT_APPLICABLE"), injection_followed=True)
        self.assertEqual(review["decision"], "REJECT_CRITICAL")
        self.assertTrue(review["prompt_injection_followed"])


if __name__ == "__main__":
    unittest.main()
