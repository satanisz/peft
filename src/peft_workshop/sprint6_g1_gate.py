from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .paths import RESULTS_DIR, project_relative, resolve_project_path


def _read(path: str | Path) -> dict[str, Any]:
    return json.loads(resolve_project_path(path).read_text(encoding="utf-8"))


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with resolve_project_path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_g1_report(review_path: str | Path = "data/reviews/shadow_challenge_v1_review.json") -> dict[str, Any]:
    criteria = _read("configs/shadow_review_criteria_v1.json")
    g0 = _read("results/sprint6/g0_preflight.json")
    registry = _read("data/shadow_registry.json")
    audit = _read("results/sprint6/shadow_authoring_audit.json")
    assisted = _read("data/reviews/shadow_challenge_v1_assisted_review.json")
    review = _read(review_path)

    cases = registry.get("cases", [])
    human_cases = review.get("cases", [])
    summary = review.get("summary", {})
    authoring_checks = audit.get("checks", {})
    mechanical: dict[str, bool] = {
        "g0_pass": g0.get("decision") == "S6_G0_PASS",
        "g0_records_protected_closed": g0.get("protected_content_read") is False,
        "dataset_hash_matches_registry": _sha256(registry["dataset_path"]) == registry.get("dataset_sha256"),
        "source_pack_hash_matches_registry": _sha256(registry["source_pack_path"]) == registry.get("source_pack_sha256"),
        "dataset_hash_matches_human_review": review.get("dataset_sha256") == registry.get("dataset_sha256"),
        "source_hash_matches_human_review": review.get("source_pack_sha256") == registry.get("source_pack_sha256"),
        "exactly_50_cases": len(cases) == criteria["required_case_count"],
        "all_authoring_checks_pass": bool(authoring_checks) and all(authoring_checks.values()),
        "similarity_limits_pass": audit.get("summary", {}).get("max_sequence_similarity", 1) < criteria["max_sequence_similarity_exclusive"]
        and audit.get("summary", {}).get("max_jaccard_similarity", 1) < criteria["max_jaccard_similarity_exclusive"],
        "assisted_review_complete": assisted.get("reviewed_case_count") == criteria["required_case_count"]
        and assisted.get("assisted_approved_case_count") == criteria["required_approved_case_count"]
        and assisted.get("critical_error_count") == 0,
        "assisted_review_not_misrepresented_as_independent": assisted.get("reviewer_independent_from_authoring") is False,
        "shadow_never_primary_evidence": all(row.get("primary_independent_evidence") is False for row in cases),
        "protected_content_not_read": registry.get("protected_content_read") is False
        and audit.get("protected_content_read") is False,
    }
    human: dict[str, bool] = {
        "human_review_status_approved": review.get("review_status") == criteria["allowed_human_review_status"],
        "human_reviewer_named": bool(review.get("reviewer_name")),
        "human_reviewer_is_sme": review.get("reviewer_role") == "human_sme",
        "human_reviewer_independent": review.get("reviewer_independent_from_authoring") is True,
        "human_review_timestamp_present": bool(review.get("reviewed_at")),
        "human_reviewed_50_cases": summary.get("reviewed_case_count") == criteria["required_case_count"]
        and len(human_cases) == criteria["required_case_count"],
        "human_approved_50_cases": summary.get("approved_case_count") == criteria["required_approved_case_count"]
        and all(row.get("decision") == "APPROVED" for row in human_cases),
        "zero_critical_human_findings": summary.get("critical_error_count") == 0
        and not any(row.get("critical_error") is True for row in human_cases),
        "human_approved_for_shadow_freeze": summary.get("approved_for_shadow_freeze") is True,
    }
    if not all(mechanical.values()):
        decision = "S6_G1_BLOCKED_AUTHORING_OR_INTEGRITY"
        next_action = "CORRECT_AUTHORING_OR_INTEGRITY_WITHOUT_INFERENCE"
    elif not all(human.values()):
        decision = "S6_G1_HOLD_PENDING_HUMAN_SME"
        next_action = "HUMAN_SME_REVIEW_50_CASES"
    else:
        decision = "S6_G1_PASS"
        next_action = "COMMIT_SHADOW_FREEZE_THEN_RUN_S6_G2"
    return {
        "milestone": "S6-G1 Shadow freeze",
        "decision": decision,
        "mechanical_checks": mechanical,
        "human_sme_checks": human,
        "dataset": project_relative(resolve_project_path(registry["dataset_path"])),
        "dataset_sha256": registry.get("dataset_sha256"),
        "source_pack_sha256": registry.get("source_pack_sha256"),
        "case_count": len(cases),
        "protected_splits_opened": False,
        "protected_content_read": False,
        "inference_run": False,
        "automatic_approval": False,
        "next_allowed_action": next_action,
        "scope_notice": "G1 zamraża wyłącznie shadow challenge. Nie zezwala na otwarcie protected evidence; nadal wymagane są G2 i osobna jawna decyzja operatora.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Sprint 6 G1 without reading protected evidence.")
    parser.add_argument("--review", default="data/reviews/shadow_challenge_v1_review.json")
    parser.add_argument("--output", default=str(RESULTS_DIR / "sprint6" / "g1_shadow_freeze.json"))
    args = parser.parse_args()
    report = build_g1_report(args.review)
    output = resolve_project_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["decision"] in {"S6_G1_PASS", "S6_G1_HOLD_PENDING_HUMAN_SME"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
