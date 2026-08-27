from __future__ import annotations

import unittest

from peft_workshop.sprint4_2a_analysis import ALLOWED_SEVERITY_DATASETS, build_analysis


class Sprint42AAnalysisTests(unittest.TestCase):
    def test_analysis_never_lists_protected_datasets(self) -> None:
        protected_names = {"test", "boundary_test", "challenge"}
        for path in ALLOWED_SEVERITY_DATASETS:
            parts = set(path.lower().replace("\\", "/").split("/"))
            stem = path.lower().replace("\\", "/").split("/")[-1].split(".")[0]
            self.assertFalse(protected_names & (parts | {stem}))

    def test_analysis_records_known_contract_findings(self) -> None:
        report = build_analysis()
        self.assertFalse(report["protected_splits_opened"])
        self.assertEqual(report["diagnostic_audit"]["count"], 30)
        self.assertEqual(report["diagnostic_audit"]["schema_error_count"], 0)
        rows = {item["path"]: item for item in report["severity_contract"]["datasets"]}
        self.assertEqual(rows["data/generated/dataset_v1/validation.jsonl"]["mismatch_rate"], 0.24)
        self.assertEqual(rows["data/splits/boundary_validation.jsonl"]["mismatch_rate"], 0.0)
        source_errors = [
            error
            for seed in report["q1_validation_findings"]
            for error in seed["boundary"]["source_errors"]
        ]
        self.assertEqual([item["case_id"] for item in source_errors], ["BD-0360"])


if __name__ == "__main__":
    unittest.main()
