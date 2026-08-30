"""Close consumed Sprint 6 Evidence v1 as immutable, read-only evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from peft_workshop.paths import RESULTS_DIR, project_relative, resolve_project_path


OWNER_ACCEPTANCE = "results/sprint6/m6_owner_acceptance.json"
CLOSURE_PATH = "results/sprint6/protected_evidence_v1_closure.json"
EXPECTED_STATUS = "CONSUMED_FROZEN_READ_ONLY_FAILED_THRESHOLDS"
EXPECTED_OWNER_DECISION = "OWNER_ACCEPTED_FAILED_EVIDENCE_AS_WORKSHOP_CASE"
EVIDENCE_RUN_COMMIT = "0a4305d8fb5060a8f12d9cccf77519db338502b1"
FINAL_REVIEW_COMMIT = "699fa6b64e03c3a730fac02d3e07eeca49184641"


def _read(path: str | Path) -> dict[str, Any]:
    return json.loads(resolve_project_path(path).read_text(encoding="utf-8"))


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with resolve_project_path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_is_ancestor(commit: str) -> bool:
    return subprocess.call(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=resolve_project_path("."),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ) == 0


def evidence_files() -> list[str]:
    fixed = {
        "results/sprint6/protected_open_approval.json",
        "results/sprint4/protected_split_authorization.json",
        "results/sprint6/evidence_summary.json",
        "results/sprint4/challenge_manual_review.json",
        "results/sprint6/shadow_manual_response_review.json",
        "docs/28_sprint_6_final_evidence_review.md",
        OWNER_ACCEPTANCE,
    }
    primary = {
        project_relative(path)
        for path in resolve_project_path("results/sprint4").glob("seed_202608*_*.json*")
        if any(name in path.name for name in ("original_test", "boundary_test", "challenge"))
    }
    shadow = {
        project_relative(path)
        for path in resolve_project_path("results/sprint6").glob("seed_202608*_shadow_challenge*.json*")
    }
    return sorted(fixed | primary | shadow)


def expected_bindings() -> dict[str, str]:
    paths = evidence_files()
    missing = [path for path in paths if not resolve_project_path(path).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing closure inputs: {missing}")
    return {path: _sha256(path) for path in paths}


def _input_checks() -> dict[str, bool]:
    acceptance = _read(OWNER_ACCEPTANCE)
    statements = acceptance.get("statements", {})
    evidence = _read("results/sprint6/evidence_summary.json")
    approval = _read("results/sprint6/protected_open_approval.json")
    authorization = _read("results/sprint4/protected_split_authorization.json")
    return {
        "owner_decision_matches": acceptance.get("decision") == EXPECTED_OWNER_DECISION,
        "all_owner_statements_accepted": bool(statements) and all(statements.values()),
        "owner_bound_hashes_unchanged": acceptance.get("bound_sha256")
        == {
            path: _sha256(path)
            for path in (
                "results/sprint6/evidence_summary.json",
                "results/sprint4/challenge_manual_review.json",
                "results/sprint6/shadow_manual_response_review.json",
                "docs/28_sprint_6_final_evidence_review.md",
            )
        },
        "protected_open_was_approved": approval.get("decision") == "APPROVED_TO_OPEN_PROTECTED_SPLITS",
        "operator_confirmation_was_explicit": authorization.get("explicit_operator_confirmation") is True,
        "evidence_was_opened": evidence.get("protected_splits_opened") is True,
        "evidence_failed_frozen_thresholds": evidence.get("decision") == "FAILED_EVIDENCE_THRESHOLDS",
        "primary_failed_frozen_thresholds": evidence.get("primary_protected_evidence", {}).get("decision")
        == "FAILED_EVIDENCE_THRESHOLDS",
        "shadow_failed_frozen_thresholds": evidence.get("shadow_risk_directed_evidence", {}).get("decision")
        == "FAILED_SHADOW_THRESHOLDS",
        "no_retuning_after_evidence": evidence.get("retuning_after_evidence") is False,
        "evidence_run_commit_is_ancestor": _git_is_ancestor(EVIDENCE_RUN_COMMIT),
        "final_review_commit_is_ancestor": _git_is_ancestor(FINAL_REVIEW_COMMIT),
    }


def build_closure() -> dict[str, Any]:
    checks = _input_checks()
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise ValueError(f"Evidence v1 cannot be closed; failed checks: {failed}")
    return {
        "id": "S6-PROTECTED-EVIDENCE-V1-CLOSURE",
        "version": "1.0.0",
        "status": EXPECTED_STATUS,
        "closed_at": datetime.now().astimezone().isoformat(),
        "owner_acceptance": EXPECTED_OWNER_DECISION,
        "evidence_decision": "FAILED_EVIDENCE_THRESHOLDS",
        "protected_splits_opened": True,
        "evidence_v1_rerun_allowed": False,
        "retuning_on_evidence_v1_allowed": False,
        "production_approval": False,
        "future_use": "DIAGNOSTIC_AND_REGRESSION_ONLY_NOT_INDEPENDENT_EVIDENCE",
        "evidence_run_commit": EVIDENCE_RUN_COMMIT,
        "final_review_commit": FINAL_REVIEW_COMMIT,
        "checks": checks,
        "bound_sha256": expected_bindings(),
        "next_allowed_action": "BUILD_WORKSHOP_EVIDENCE_PACKAGE_S6_5C",
        "scope_notice": (
            "Closure preserves the failed Evidence v1 result. It is not model approval, "
            "production approval, or authorization for a corrective rerun."
        ),
    }


def validate_closure(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    closure = payload if payload is not None else _read(CLOSURE_PATH)
    input_checks = _input_checks()
    bindings = expected_bindings()
    checks = {
        **input_checks,
        "closure_id_matches": closure.get("id") == "S6-PROTECTED-EVIDENCE-V1-CLOSURE",
        "closure_status_is_failed_read_only": closure.get("status") == EXPECTED_STATUS,
        "closure_decision_matches_failed_summary": closure.get("evidence_decision")
        == "FAILED_EVIDENCE_THRESHOLDS",
        "closure_never_claims_production_approval": closure.get("production_approval") is False,
        "rerun_is_forbidden": closure.get("evidence_v1_rerun_allowed") is False,
        "retuning_is_forbidden": closure.get("retuning_on_evidence_v1_allowed") is False,
        "bound_file_set_exact": set(closure.get("bound_sha256", {})) == set(bindings),
        "all_bound_hashes_match": closure.get("bound_sha256") == bindings,
    }
    return {
        "milestone": "S6.5B Evidence v1 closure",
        "decision": "EVIDENCE_V1_CLOSED_READ_ONLY" if all(checks.values()) else "EVIDENCE_V1_CLOSURE_BLOCKED",
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and validate the immutable Sprint 6 Evidence v1 closure.")
    parser.add_argument("--output", default=str(RESULTS_DIR / "sprint6" / "protected_evidence_v1_closure.json"))
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    output = resolve_project_path(args.output)
    if not args.validate_only:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(build_closure(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = validate_closure(_read(output))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["decision"] == "EVIDENCE_V1_CLOSED_READ_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
