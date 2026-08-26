import hashlib
import json
import unittest

from peft_workshop.cases import load_cases
from peft_workshop.paths import CONFIG_DIR, DATA_DIR, RESULTS_DIR
from peft_workshop.prompts import select_demonstrations


class BaselineArtifactTests(unittest.TestCase):
    def test_frozen_baseline_artifacts_are_complete_and_consistent(self) -> None:
        config = json.loads((CONFIG_DIR / "baseline_v1.json").read_text(encoding="utf-8"))
        dataset_path = DATA_DIR.parent / config["dataset"]["path"]
        self.assertEqual(
            hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
            config["dataset"]["sha256"],
        )
        cases = load_cases(dataset_path)
        for split in ("development", "validation"):
            expected_ids = {case["case_id"] for case in cases if case["split"] == split}
            self.assertEqual(len(expected_ids), 50)
            for variant in ("B0", "B1", "B2"):
                path = RESULTS_DIR / f"{variant.lower()}_4b_{split}.jsonl"
                records = [
                    json.loads(line)
                    for line in path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                self.assertEqual({record["case_id"] for record in records}, expected_ids)
                self.assertTrue(all(record["split"] == split for record in records))
                self.assertTrue(all(record["baseline_variant"] == variant for record in records))
                self.assertTrue(
                    all(record["model_id"] == config["model"]["id"] for record in records)
                )
                self.assertTrue(
                    all(
                        record["model_revision"] == config["model"]["revision"]
                        for record in records
                    )
                )
                self.assertTrue(
                    all(
                        record["prompt_sha256"]
                        == config["variants"][variant]["system_prompt_sha256"]
                        for record in records
                    )
                )
                if variant == "B2":
                    by_id = {case["case_id"]: case for case in cases}
                    self.assertTrue(
                        all(
                            record["demonstration_case_ids"]
                            == [
                                demo["case_id"]
                                for demo in select_demonstrations(by_id[record["case_id"]], cases)
                            ]
                            for record in records
                        )
                    )
                metrics = json.loads(
                    (RESULTS_DIR / f"{variant.lower()}_4b_{split}_metrics.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(metrics["aggregate"]["count"], 50)


if __name__ == "__main__":
    unittest.main()
