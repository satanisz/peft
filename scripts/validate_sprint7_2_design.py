from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/sprint7/s7_2_design_gate.json"
STATUSES = ("PASS", "WARN", "FAIL", "INSUFFICIENT_DATA", "NOT_APPLICABLE")


def read(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def matrix_checks(split: dict) -> dict[str, bool]:
    matrix = split["risk_status_matrix"]
    row_total = sum(sum(row.values()) for row in matrix.values())
    columns = Counter()
    for row in matrix.values():
        columns.update(row)
    return {
        "matrix_total_matches_count": row_total == split["count"],
        "matrix_columns_match_status_counts": all(columns[status] == split["status_counts"][status] for status in STATUSES),
        "all_matrix_cells_non_negative_integers": all(isinstance(value, int) and value >= 0 for row in matrix.values() for value in row.values()),
        "all_statuses_present": all(split["status_counts"][status] > 0 for status in STATUSES),
    }


def main() -> None:
    upstream_gate = read("results/sprint7/s7_0_s7_1_gate.json")
    spec = read("configs/s7_train_dev_v2_spec.json")
    rubric = read("configs/s7_gold_rubric_v2.json")
    provenance = read("configs/s7_provenance_policy_v2.json")
    similarity = read("configs/s7_similarity_leakage_policy_v2.json")
    exclusions = read("results/sprint7/data_exclusion_registry_v1.json")
    train = spec["splits"]["train_hardening_v2"]
    dev = spec["splits"]["dev_hard_v2"]
    train_checks = matrix_checks(train)
    dev_checks = matrix_checks(dev)
    exclusion_hashes_match = all(
        sha256(ROOT / item["path"]) == item["sha256"]
        for key in ("forbidden_for_q2_train", "forbidden_for_v2_evidence")
        for item in exclusions[key]
    )
    planned_outputs_absent = all(not (ROOT / path).exists() for path in spec["planned_outputs"])
    checks = {
        "upstream_remediation_gate_pass": upstream_gate.get("decision") == "S7_REMEDIATION_DESIGN_APPROVED",
        "spec_frozen_for_luna_generation": spec.get("status") == "FROZEN_DESIGN_READY_FOR_LUNA_LOW_GENERATION",
        "train_count_300": train.get("count") == 300,
        "dev_count_90": dev.get("count") == 90,
        "train_matrix_valid": all(train_checks.values()),
        "dev_matrix_valid": all(dev_checks.values()),
        "counterfactual_pairs_36": train.get("counterfactual_pairs") + dev.get("counterfactual_pairs") == 36,
        "counterfactual_pairs_stay_in_split": spec["counterfactual_contract"].get("pair_must_remain_within_one_split") is True,
        "single_premise_pairs": spec["counterfactual_contract"].get("changed_semantic_premise_count") == 1,
        "all_nine_control_types": len(spec["control_coverage"].get("control_types", [])) == 9,
        "stable_existing_output_schema": spec["case_contract_v2"].get("expected_output_schema") == "existing status-aware v2 output schema",
        "structured_source_trust_required": all(field in spec["case_contract_v2"]["source_required_fields"] for field in ("source_role", "trusted_for_evidence", "evidence_role")),
        "gold_rubric_frozen": rubric.get("status") == "FROZEN_DESIGN_READY_FOR_AUTHORING",
        "gold_review_requires_all_390": rubric["review_requirements"].get("human_sme_review") == "390/390 before S7_TRAIN_DEV_V2_FROZEN",
        "model_review_not_sme": rubric["review_requirements"].get("model_assisted_review_counts_as_sme") is False,
        "provenance_policy_frozen": provenance.get("status") == "FROZEN_DESIGN_READY_FOR_AUTHORING",
        "authoring_does_not_load_forbidden_cases": provenance["authoring_phases"][0].get("forbidden_inputs") == "Every path in results/sprint7/data_exclusion_registry_v1.json",
        "similarity_policy_frozen": similarity.get("status") == "FROZEN_DESIGN_READY_FOR_IMPLEMENTATION",
        "similarity_thresholds_are_fixed": similarity["automatic_fail_rules"].get("token_5gram_jaccard_against_forbidden_max_exclusive") == 0.35,
        "exclusion_hashes_unchanged": exclusion_hashes_match,
        "planned_data_not_generated_yet": planned_outputs_absent,
        "no_evidence_v2_created": not (ROOT / "data/evidence_v2").exists(),
        "no_q2_adapter_created": not (ROOT / "artifacts/adapters/q2-v0.1").exists()
    }
    decision = "S7_2_DESIGN_READY_FOR_LUNA_LOW" if all(checks.values()) else "S7_2_DESIGN_HOLD"
    payload = {
        "id": "S7-2-DESIGN-GATE",
        "version": "1.0.0",
        "checks": checks,
        "details": {
            "train_matrix": train_checks,
            "dev_matrix": dev_checks,
            "train_count": train["count"],
            "dev_count": dev["count"],
            "counterfactual_pairs": train["counterfactual_pairs"] + dev["counterfactual_pairs"]
        },
        "decision": decision,
        "next_allowed_action": "LUNA_LOW_GENERATE_AND_VALIDATE_S7_2" if decision == "S7_2_DESIGN_READY_FOR_LUNA_LOW" else "SOL_HIGH_REVIEW_DESIGN_FAILURES",
        "next_stop": "S7_TRAIN_DEV_V2_READY_FOR_SOL_SME_REVIEW",
        "prohibited_actions": [
            "Q2 training",
            "Evidence v2 authoring or inference",
            "Evidence v1 rerun",
            "changing counts, matrices, rubric or similarity thresholds on Luna/low"
        ]
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if decision != "S7_2_DESIGN_READY_FOR_LUNA_LOW":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
