from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/sprint7/s7_0_s7_1_gate.json"


def read(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> None:
    manifest = read("results/sprint7/baseline_v1_manifest.json")
    analysis = read("results/sprint7/evidence_v1_error_analysis.json")
    exclusions = read("results/sprint7/data_exclusion_registry_v1.json")
    prompt = read("configs/prompt_contract_v3_design.json")
    guard = read("configs/s7_guard_v2_design.json")
    remediation = read("results/sprint7/remediation_design.json")
    checks = {
        "baseline_frozen": manifest.get("decision") == "S7_BASELINE_FROZEN",
        "closure_failed_frozen_read_only": manifest["checks"]["closure_is_failed_frozen_read_only"],
        "closure_hashes_match": manifest["checks"]["all_closure_hashes_match"],
        "adapter_hashes_match": manifest["checks"]["all_present_adapter_hashes_match"],
        "closure_commits_are_ancestors": manifest["checks"]["closure_commits_are_ancestors"],
        "q1_training_excluded_protected_shadow": manifest["checks"]["q1_train_sources_exclude_protected_shadow"],
        "all_870_responses_analyzed": analysis.get("analyzed_response_count") == 870,
        "four_splits_three_seeds_covered": len(analysis.get("split_seed_metrics", [])) == 12,
        "per_case_seed_error_records_present": bool(analysis.get("errors_per_case_and_seed")),
        "legacy_severity_separated": analysis.get("legacy_severity_observation_count", 0) > 0,
        "deterministic_diagnostic_separated": len(analysis.get("diagnostic_control_findings", [])) == 3,
        "q2_train_exclusions_recorded": len(exclusions.get("forbidden_for_q2_train", [])) >= 7,
        "v2_evidence_exclusions_recorded": len(exclusions.get("forbidden_for_v2_evidence", [])) >= 11,
        "prompt_v3_design_frozen_for_implementation": prompt.get("status") == "FROZEN_FOR_S7_2_IMPLEMENTATION_NOT_FOR_EVIDENCE",
        "guard_v2_design_frozen_for_implementation": guard.get("status") == "FROZEN_FOR_S7_2_IMPLEMENTATION_NOT_FOR_EVIDENCE",
        "guard_has_no_gold_runtime_input": "expected_output" in guard.get("runtime_forbidden_inputs", []),
        "guard_has_no_silent_correction": guard.get("mode") == "block_and_route_to_human_no_silent_correction",
        "remediation_design_approved": remediation.get("decision") == "S7_REMEDIATION_DESIGN_APPROVED",
        "no_evidence_v2_created": not (ROOT / "data/evidence_v2").exists(),
        "no_q2_adapter_created": not (ROOT / "artifacts/adapters/q2-v0.1").exists()
    }
    decision = "S7_REMEDIATION_DESIGN_APPROVED" if all(checks.values()) else "S7_0_1_HOLD"
    payload = {
        "id": "S7-0-1-GATE",
        "version": "1.0.0",
        "checks": checks,
        "decision": decision,
        "next_allowed_action": "DESIGN_S7_2_TRAIN_DEV_V2" if decision == "S7_REMEDIATION_DESIGN_APPROVED" else "REVIEW_FAILED_CHECKS",
        "prohibited_actions": [
            "rerun Evidence v1",
            "retune on Evidence v1 or shadow v1",
            "create or open Evidence v2",
            "start Q2 training before S7.2 and S7.3 gates"
        ]
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if decision != "S7_REMEDIATION_DESIGN_APPROVED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
