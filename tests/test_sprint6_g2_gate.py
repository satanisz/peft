from __future__ import annotations

import unittest

from peft_workshop.sprint6_g2_gate import (
    _exact_revision_local_only,
    _failure_rehearsal,
    _training_source_audit,
    build_g2_report,
)


class Sprint6G2GateTests(unittest.TestCase):
    def test_technical_readiness_passes_without_protected_read(self) -> None:
        report = build_g2_report(run_embedded_tests=False, run_clean_install=False)
        self.assertEqual(report["decision"], "S6_G2_1_PASS")
        self.assertTrue(all(report["checks"].values()))
        self.assertFalse(report["protected_content_read"])
        self.assertFalse(report["inference_run"])

    def test_failure_rehearsal_has_fallback_for_each_scenario(self) -> None:
        model = {
            "id": "Qwen/Qwen3-4B-Instruct-2507",
            "revision": "cdbee75f17c01a7cc42f958dc650907174af0554",
        }
        scenarios = _failure_rehearsal(model)["scenarios"]
        self.assertEqual(set(scenarios), {"oom", "missing_model", "checkpoint_error", "offline_cache"})
        self.assertTrue(
            all(item["caught"] and item["fallback_executed"] and item["passed"] for item in scenarios.values())
        )

    def test_exact_revision_is_loaded_from_complete_local_weight_set(self) -> None:
        model = {
            "id": "Qwen/Qwen3-4B-Instruct-2507",
            "revision": "cdbee75f17c01a7cc42f958dc650907174af0554",
        }
        result = _exact_revision_local_only(model)
        self.assertTrue(result["passed"])
        self.assertTrue(result["local_files_only"])
        self.assertTrue(result["snapshot_matches_revision"])
        self.assertGreater(result["verified_shard_count"], 0)
        self.assertEqual(result["missing_tensors"], [])

    def test_train_sources_exclude_protected_and_shadow_registries(self) -> None:
        audit = _training_source_audit()
        self.assertGreater(len(audit["checked_sources"]), 0)
        self.assertEqual(audit["violations"], [])


if __name__ == "__main__":
    unittest.main()
