from __future__ import annotations

import unittest
from collections import Counter
import json
from pathlib import Path

from peft_workshop.shadow_challenge import build_cases


class ShadowChallengeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases, cls.registry = build_cases()

    def test_exactly_50_balanced_cases(self) -> None:
        self.assertEqual(len(self.cases), 50)
        self.assertEqual(set(Counter(row["expected_output"]["status"] for row in self.cases).values()), {10})
        self.assertEqual(set(Counter(row["risk_family"] for row in self.registry).values()), {10})

    def test_cases_are_manual_shadow_only(self) -> None:
        self.assertTrue(all(row["split"] == "challenge" for row in self.cases))
        self.assertTrue(all(row["metadata"]["generation_method"] == "manual" for row in self.cases))
        self.assertEqual(len({row["metadata"]["family_id"] for row in self.cases}), 50)

    def test_leakage_and_schema_audit_passes_without_protected_read(self) -> None:
        audit = json.loads(Path("results/sprint6/shadow_authoring_audit.json").read_text(encoding="utf-8"))
        self.assertTrue(all(audit["checks"].values()))
        self.assertFalse(audit["protected_content_read"])
        self.assertEqual(audit["summary"]["exact_content_overlap"], 0)


if __name__ == "__main__":
    unittest.main()
