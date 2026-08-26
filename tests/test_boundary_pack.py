import hashlib
import json
import unittest
from collections import Counter, defaultdict

from peft_workshop.boundary_dataset import (
    BOUNDARIES,
    build_boundary_pack,
    build_review_manifest,
    validate_boundary_pack,
)
from peft_workshop.data_audit import audit_cases
from peft_workshop.metrics import aggregate_boundary_scores, score_prediction
from peft_workshop.paths import CONFIG_DIR, DATA_DIR
from peft_workshop.prompts import (
    B3_DEMONSTRATION_CASE_IDS,
    STATUS_AWARE_SYSTEM_PROMPT,
    select_status_demonstrations,
)
from peft_workshop.validation import validate_case


class BoundaryPackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = build_boundary_pack()

    def test_pack_has_exact_contract(self) -> None:
        self.assertEqual(len(self.cases), 540)
        self.assertEqual(validate_boundary_pack(self.cases), [])
        self.assertEqual(
            Counter(case["split"] for case in self.cases),
            Counter({"train": 240, "development": 60, "validation": 120, "test": 120}),
        )
        self.assertEqual(
            Counter(case["expected_output"]["status"] for case in self.cases),
            Counter(
                {
                    "PASS": 80,
                    "WARN": 160,
                    "FAIL": 80,
                    "INSUFFICIENT_DATA": 110,
                    "NOT_APPLICABLE": 110,
                }
            ),
        )

    def test_all_cases_are_schema_valid_and_auditable(self) -> None:
        for case in self.cases:
            self.assertEqual(validate_case(case), [], case["case_id"])
        report = audit_cases(self.cases)
        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(report["summary"]["exact_duplicate_count"], 0)
        self.assertEqual(report["summary"]["leaking_family_count"], 0)

    def test_pairs_change_exactly_one_source_premise(self) -> None:
        groups = defaultdict(list)
        for case in self.cases:
            groups[case["group_id"]].append(case)
        self.assertEqual(len(groups), 270)
        for pair in groups.values():
            self.assertEqual(len(pair), 2)
            boundary = pair[0]["metadata"]["boundary_type"]
            self.assertEqual(
                {case["expected_output"]["status"] for case in pair},
                set(BOUNDARIES[boundary]),
            )
            changed = sum(
                left["content"] != right["content"]
                for left, right in zip(
                    pair[0]["input"]["sources"], pair[1]["input"]["sources"], strict=True
                )
            )
            self.assertEqual(changed, 1)

    def test_review_scope_meets_gate(self) -> None:
        review = build_review_manifest(self.cases)
        self.assertEqual(
            sum(item["expected_status"] == "NOT_APPLICABLE" for item in review),
            110,
        )
        self.assertGreaterEqual(
            sum(item["expected_status"] != "NOT_APPLICABLE" for item in review),
            86,
        )
        self.assertFalse(any(item["critical_error"] for item in review))

    def test_b3_is_label_complete_and_hash_is_frozen(self) -> None:
        target = next(case for case in self.cases if case["split"] == "validation")
        demos = select_status_demonstrations(target, self.cases)
        self.assertEqual(tuple(case["case_id"] for case in demos), B3_DEMONSTRATION_CASE_IDS)
        self.assertEqual(
            {case["expected_output"]["status"] for case in demos},
            {"WARN", "INSUFFICIENT_DATA", "NOT_APPLICABLE"},
        )
        config = json.loads((CONFIG_DIR / "baseline_b3_v1.json").read_text(encoding="utf-8"))
        self.assertEqual(
            hashlib.sha256(STATUS_AWARE_SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
            config["variant"]["system_prompt_sha256"],
        )

    def test_gold_boundary_metrics_are_perfect(self) -> None:
        validation = [case for case in self.cases if case["split"] == "validation"]
        scores = []
        for case in validation:
            score = score_prediction(
                case, json.dumps(case["expected_output"], ensure_ascii=False)
            )
            score["group_id"] = case["group_id"]
            scores.append(score)
        policy = json.loads((CONFIG_DIR / "status_policy_v1.json").read_text(encoding="utf-8"))
        aggregate = aggregate_boundary_scores(scores, policy["business_cost_matrix"])
        self.assertEqual(aggregate["pair_accuracy"], 1.0)
        self.assertEqual(aggregate["mean_business_cost"], 0.0)

    def test_frozen_artifact_matches_registry(self) -> None:
        registry = json.loads((DATA_DIR / "boundary_registry.json").read_text(encoding="utf-8"))
        frozen = registry["datasets"][0]
        path = DATA_DIR.parent / frozen["output"]
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), frozen["sha256"])

    def test_formal_boundary_baseline_artifacts_are_complete(self) -> None:
        results_dir = DATA_DIR.parent / "results"
        expected_ids = {
            case["case_id"] for case in self.cases if case["split"] == "validation"
        }
        self.assertEqual(len(expected_ids), 120)
        for variant in ("B1", "B2", "B3"):
            records = [
                json.loads(line)
                for line in (results_dir / f"{variant.lower()}_boundary_validation.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            self.assertEqual({record["case_id"] for record in records}, expected_ids)
            self.assertTrue(all(record["baseline_variant"] == variant for record in records))
            self.assertTrue(all(record["split"] == "validation" for record in records))
            metrics = json.loads(
                (results_dir / f"{variant.lower()}_boundary_validation_metrics.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(metrics["aggregate"]["count"], 120)
            self.assertEqual(metrics["boundary"]["pair_count"], 60)
        summary = json.loads(
            (results_dir / "boundary_v1_validation_summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual(set(summary["comparison"]), {"B1", "B2", "B3"})
        self.assertEqual(summary["best_macro_f1"], "B3")


if __name__ == "__main__":
    unittest.main()
