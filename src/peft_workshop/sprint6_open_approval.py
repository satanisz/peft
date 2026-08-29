from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from .paths import RESULTS_DIR, project_relative, resolve_project_path


CONTRACT_PATH = "configs/sprint6_protected_open_contract_v1.json"
DEFAULT_APPROVAL = "results/sprint6/protected_open_approval.json"


def _read(path: str | Path) -> dict[str, Any]:
    return json.loads(resolve_project_path(path).read_text(encoding="utf-8"))


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with resolve_project_path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(*args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], text=True, encoding="utf-8", stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def expected_bindings() -> dict[str, str]:
    contract = _read(CONTRACT_PATH)
    return {path: _sha256(path) for path in contract["bind_files"]}


def build_template() -> dict[str, Any]:
    return {
        "contract_id": _read(CONTRACT_PATH)["id"],
        "decision": "HOLD_PENDING_SOL_HIGH_REVIEW_AND_OPERATOR_CONFIRMATION",
        "reviewer": None,
        "reviewer_model": "gpt-5.6-sol/high",
        "reviewed_at": None,
        "reviewed_git_commit": None,
        "protected_splits_opened": False,
        "operator_confirmation_required": True,
        "bound_sha256": expected_bindings(),
        "review_notes": "Wypełnić dopiero po PASS poprawionego G2.1 i osobnym review Sol/high.",
    }


def validate_approval(
    approval_path: str | Path = DEFAULT_APPROVAL, *, require_clean_git: bool = True
) -> dict[str, Any]:
    contract = _read(CONTRACT_PATH)
    path = resolve_project_path(approval_path)
    approval = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    expected = expected_bindings()
    gate_checks = {
        gate_path: _read(gate_path).get("decision") == decision
        for gate_path, decision in contract["required_gate_decisions"].items()
    }
    tags = {tag: _git("rev-list", "-n", "1", tag) for tag in contract["required_tags"]}
    reviewed_commit = approval.get("reviewed_git_commit")
    reviewed_commit_is_ancestor = bool(reviewed_commit) and subprocess.call(
        ["git", "merge-base", "--is-ancestor", str(reviewed_commit), "HEAD"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ) == 0
    git_status = _git("status", "--porcelain") or ""
    checks = {
        "approval_file_exists": path.exists(),
        "contract_id_matches": approval.get("contract_id") == contract["id"],
        "decision_is_explicit_approval": approval.get("decision") == contract["required_decision"],
        "reviewer_is_named": bool(approval.get("reviewer")),
        "reviewer_model_is_sol_high": approval.get("reviewer_model") == "gpt-5.6-sol/high",
        "review_timestamp_present": bool(approval.get("reviewed_at")),
        "reviewed_commit_is_ancestor": reviewed_commit_is_ancestor,
        "protected_closed_at_approval": approval.get("protected_splits_opened") is False,
        "operator_confirmation_still_required": approval.get("operator_confirmation_required") is True,
        "all_gate_decisions_pass": all(gate_checks.values()),
        "all_required_tags_exist": all(tags.values()),
        "bound_file_set_exact": set(approval.get("bound_sha256", {})) == set(expected),
        "all_bound_hashes_match": approval.get("bound_sha256") == expected,
        "git_worktree_clean": not git_status if require_clean_git else True,
    }
    decision = "APPROVED_CONTRACT_VALID" if all(checks.values()) else "HOLD_INVALID_OR_INCOMPLETE_APPROVAL"
    return {
        "milestone": "S6 protected-open approval validation",
        "decision": decision,
        "checks": checks,
        "gate_checks": gate_checks,
        "required_tags": tags,
        "approval_path": project_relative(path),
        "current_git_commit": _git("rev-parse", "HEAD"),
        "protected_content_read": False,
        "operator_confirmation_consumed": False,
        "next_allowed_action": "OPERATOR_CONFIRM_ONE_TIME_RUN" if decision == "APPROVED_CONTRACT_VALID" else "COMPLETE_SOL_HIGH_REVIEW",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or validate a separate Sprint 6 protected-open approval.")
    parser.add_argument("--approval", default=DEFAULT_APPROVAL)
    parser.add_argument("--write-template", action="store_true")
    parser.add_argument("--require-approved", action="store_true")
    parser.add_argument("--no-output", action="store_true")
    parser.add_argument("--output", default=str(RESULTS_DIR / "sprint6" / "protected_open_approval_validation.json"))
    args = parser.parse_args()
    approval_path = resolve_project_path(args.approval)
    if args.write_template:
        approval_path.parent.mkdir(parents=True, exist_ok=True)
        approval_path.write_text(json.dumps(build_template(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = validate_approval(approval_path, require_clean_git=not args.write_template)
    if not args.no_output:
        output = resolve_project_path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if args.require_approved and report["decision"] != "APPROVED_CONTRACT_VALID" else 0


if __name__ == "__main__":
    raise SystemExit(main())
