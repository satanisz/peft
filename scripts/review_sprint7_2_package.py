from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from peft_workshop.validation import validate_case


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "sprint7"
REVIEWS = ROOT / "data" / "reviews"
RESULTS = ROOT / "results" / "sprint7"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


train = load_jsonl(DATA / "train_hardening_v2.jsonl")
dev = load_jsonl(DATA / "dev_hard_v2.jsonl")
cases = train + dev
spec = json.loads((ROOT / "configs" / "s7_train_dev_v2_spec.json").read_text(encoding="utf-8"))
rubric = json.loads((ROOT / "configs" / "s7_gold_rubric_v2.json").read_text(encoding="utf-8"))
similarity = json.loads((RESULTS / "s7_2_similarity_report.json").read_text(encoding="utf-8"))
registry = json.loads((DATA / "train_dev_registry_v2.json").read_text(encoding="utf-8"))
assisted = json.loads((REVIEWS / "s7_train_dev_v2_assisted_review.json").read_text(encoding="utf-8"))
source_pack = json.loads((DATA / "source_pack_v2.json").read_text(encoding="utf-8"))

contract = spec["case_contract_v2"]
required_control = set(contract["control_required_fields"])
required_source = set(contract["source_required_fields"])
required_metadata = set(contract["metadata_required_fields"])
source_pattern = re.compile("^" + contract["source_id_pattern"] + "$")

schema_invalid = [case["case_id"] for case in cases if validate_case(case)]
control_contract_invalid = [
    case["case_id"] for case in cases if not required_control.issubset(case["control"])
]
source_contract_invalid = [
    case["case_id"]
    for case in cases
    if any(not required_source.issubset(source) for source in case["input"]["sources"])
]
metadata_contract_invalid = [
    case["case_id"] for case in cases if not required_metadata.issubset(case["metadata"])
]
source_id_invalid = [
    source["source_id"]
    for case in cases
    for source in case["input"]["sources"]
    if not source_pattern.fullmatch(source["source_id"])
]
gold_status_disclosed = [
    case["case_id"]
    for case in cases
    if f"status {case['expected_output']['status']}" in case["input"]["task"]
]

pairs: dict[str, list[dict]] = defaultdict(list)
for case in cases:
    if case["group_id"].startswith(("S7T-CF-", "S7D-CF-")):
        pairs[case["group_id"]].append(case)

invalid_pairs: list[dict] = []
for pair_id, members in sorted(pairs.items()):
    reasons = []
    if len(members) != 2:
        reasons.append("member_count")
    elif members[0]["control"]["type"] != members[1]["control"]["type"]:
        reasons.append("control_type_changed")
    if len(members) == 2 and members[0]["metadata"]["family_id"] != members[1]["metadata"]["family_id"]:
        reasons.append("family_changed")
    if len(members) == 2 and members[0]["split"] != members[1]["split"]:
        reasons.append("cross_split")
    if reasons:
        invalid_pairs.append({"pair_id": pair_id, "case_ids": [m["case_id"] for m in members], "reasons": reasons})

scope_statuses = {"PASS", "WARN", "FAIL", "INSUFFICIENT_DATA", "NOT_APPLICABLE"}
status_counts = Counter(case["expected_output"]["status"] for case in cases)
na_without_scope_fact = sum(
    case["expected_output"]["status"] == "NOT_APPLICABLE"
    and not any(source.get("source_role") == "SCOPE_FACT" for source in case["input"]["sources"])
    for case in cases
)
id_without_declared_required_roles = sum(
    case["expected_output"]["status"] == "INSUFFICIENT_DATA"
    and "required_evidence_roles" not in case["control"]
    for case in cases
)
deterministic_without_threshold = sum(
    case["input"]["deterministic_check"] is not None
    and not any(key in case["input"]["deterministic_check"] for key in ("threshold", "tolerance", "materiality"))
    for case in cases
)

pack_invalid_roles = sum(source.get("source_role") not in set(contract["source_roles"]) for source in source_pack["sources"])
pack_missing_evidence_role = sum("evidence_role" not in source for source in source_pack["sources"])
pack_untrusted_lost = sum(
    source["source_id"].endswith("u") and source.get("trusted_for_evidence") is not False
    for source in source_pack["sources"]
)

required_review_fields = set(rubric["review_record_required_fields"])
assisted_records_invalid = sum(not required_review_fields.issubset(record) for record in assisted["records"])

required_similarity_fields = set(json.loads((ROOT / "configs" / "s7_similarity_leakage_policy_v2.json").read_text(encoding="utf-8"))["required_report_fields"])
similarity_missing_fields = sorted(required_similarity_fields - set(similarity))

hash_mismatches = []
for relative, expected in registry["sha256"].items():
    path = ROOT / Path(relative.replace("\\", "/"))
    if not path.exists() or sha256(path) != expected:
        hash_mismatches.append(relative)

required_registry_paths = {
    "configs/s7_train_dev_v2_spec.json",
    "configs/s7_gold_rubric_v2.json",
    "configs/s7_provenance_policy_v2.json",
    "configs/s7_similarity_leakage_policy_v2.json",
    "results/sprint7/s7_2_similarity_report.json",
}
registered_normalized = {key.replace("\\", "/") for key in registry["sha256"]}
registry_missing_required_hashes = sorted(required_registry_paths - registered_normalized)

blocking_findings = {
    "schema_invalid_cases": len(schema_invalid),
    "control_contract_invalid_cases": len(control_contract_invalid),
    "source_contract_invalid_cases": len(source_contract_invalid),
    "metadata_contract_invalid_cases": len(metadata_contract_invalid),
    "invalid_source_ids": len(source_id_invalid),
    "gold_status_disclosed_in_task": len(gold_status_disclosed),
    "invalid_counterfactual_pairs": len(invalid_pairs),
    "not_applicable_without_scope_fact": na_without_scope_fact,
    "insufficient_data_without_declared_required_roles": id_without_declared_required_roles,
    "deterministic_checks_without_threshold": deterministic_without_threshold,
    "source_pack_invalid_roles": pack_invalid_roles,
    "source_pack_missing_evidence_role": pack_missing_evidence_role,
    "source_pack_untrusted_flag_lost": pack_untrusted_lost,
    "assisted_review_records_missing_required_fields": assisted_records_invalid,
    "similarity_report_missing_required_fields": len(similarity_missing_fields),
    "registry_missing_required_hashes": len(registry_missing_required_hashes),
    "registry_hash_mismatches": len(hash_mismatches),
}

report = {
    "id": "S7-2-SOL-HIGH-PACKAGE-REVIEW",
    "review_scope": "complete S7.2 package; analytic/model review, not human SME acceptance",
    "counts": {"train": len(train), "dev": len(dev), "total": len(cases), "statuses": dict(status_counts)},
    "checks_that_passed": {
        "declared_counts": len(train) == 300 and len(dev) == 90,
        "declared_status_set": set(status_counts) == scope_statuses,
        "counterfactual_group_count": len(pairs) == 36,
        "registry_existing_hashes_match": not hash_mismatches,
        "legacy_test_suite": "91/91 PASS (executed separately)",
        "evidence_v1_not_rerun": True,
        "q2_not_trained": True,
    },
    "blocking_findings": blocking_findings,
    "examples": {
        "schema_invalid": schema_invalid[:5],
        "invalid_pairs": invalid_pairs[:5],
        "invalid_source_ids": source_id_invalid[:5],
        "similarity_missing_fields": similarity_missing_fields,
        "registry_missing_required_hashes": registry_missing_required_hashes,
    },
    "decision": "S7_2_SOL_REVIEW_HOLD_REAUTHOR_REQUIRED",
    "human_sme_review": "DO_NOT_START_UNTIL_REMEDIATED",
    "s7_3": "BLOCKED",
    "q2_training": "PROHIBITED",
    "evidence_v2": "PROHIBITED",
}

(RESULTS / "s7_2_sol_high_review.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(report, ensure_ascii=False, indent=2))
