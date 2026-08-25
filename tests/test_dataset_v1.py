import unittest
import hashlib
import json
from collections import Counter, defaultdict

from peft_workshop.data_audit import audit_cases
from peft_workshop.dataset_v1 import build_full, build_pilot
from peft_workshop.paths import DATA_DIR
from peft_workshop.validation import validate_case


class DatasetV1Tests(unittest.TestCase):
    def test_pilot_contains_120_valid_cases(self) -> None:
        cases = build_pilot()
        self.assertEqual(len(cases), 120)
        for case in cases:
            self.assertEqual(validate_case(case), [], case["case_id"])

    def test_full_dataset_has_expected_splits(self) -> None:
        cases = build_full()
        self.assertEqual(len(cases), 620)
        self.assertEqual(
            Counter(case["split"] for case in cases),
            Counter({"train": 400, "development": 50, "validation": 50, "test": 100, "challenge": 20}),
        )

    def test_each_family_is_in_exactly_one_split(self) -> None:
        groups: dict[str, set[str]] = defaultdict(set)
        for case in build_full():
            groups[case["group_id"]].add(case["split"])
        self.assertTrue(all(len(splits) == 1 for splits in groups.values()))

    def test_full_dataset_passes_audit(self) -> None:
        report = audit_cases(build_full())
        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(report["summary"]["exact_duplicate_count"], 0)
        self.assertEqual(report["summary"]["leaking_family_count"], 0)

    def test_frozen_dataset_matches_registry_hash(self) -> None:
        registry = json.loads((DATA_DIR / "dataset_registry.json").read_text(encoding="utf-8"))
        frozen = registry["datasets"][0]
        dataset_path = DATA_DIR.parent / frozen["output"]
        actual = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
        self.assertEqual(actual, frozen["sha256"])


if __name__ == "__main__":
    unittest.main()
