import unittest

from peft_workshop.cases import build_cases
from peft_workshop.validation import validate_case


class CaseGenerationTests(unittest.TestCase):
    def test_generator_creates_40_unique_valid_cases(self) -> None:
        cases = build_cases()
        self.assertEqual(len(cases), 40)
        self.assertEqual(len({case["case_id"] for case in cases}), 40)
        for case in cases:
            self.assertEqual(validate_case(case), [], case["case_id"])

    def test_each_control_type_has_four_cases(self) -> None:
        counts: dict[str, int] = {}
        for case in build_cases():
            control_type = case["control"]["type"]
            counts[control_type] = counts.get(control_type, 0) + 1
        self.assertEqual(set(counts.values()), {4})
        self.assertEqual(len(counts), 10)


if __name__ == "__main__":
    unittest.main()

