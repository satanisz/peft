from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from peft_workshop.sprint6_open_approval import build_template, validate_approval


class Sprint6OpenApprovalTests(unittest.TestCase):
    def _write(self, payload: dict) -> Path:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "approval.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_pending_template_never_approves(self) -> None:
        report = validate_approval(self._write(build_template()), require_clean_git=False)
        self.assertEqual(report["decision"], "HOLD_INVALID_OR_INCOMPLETE_APPROVAL")
        self.assertFalse(report["protected_content_read"])

    def test_explicit_approval_with_exact_bindings_passes_contract(self) -> None:
        payload = build_template()
        payload.update({
            "decision": "APPROVED_TO_OPEN_PROTECTED_SPLITS",
            "reviewer": "Test Sol/high reviewer",
            "reviewed_at": "2026-08-29T20:30:00+02:00",
            "reviewed_git_commit": __import__("subprocess").check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        })
        with patch("peft_workshop.sprint6_open_approval._git", side_effect=lambda *args: "" if args[0] == "status" else "test-ref"):
            report = validate_approval(self._write(payload), require_clean_git=False)
        self.assertEqual(report["decision"], "APPROVED_CONTRACT_VALID")
        self.assertTrue(all(report["checks"].values()))

    def test_changed_bound_hash_blocks_approval(self) -> None:
        payload = build_template()
        payload.update({
            "decision": "APPROVED_TO_OPEN_PROTECTED_SPLITS",
            "reviewer": "Test Sol/high reviewer",
            "reviewed_at": "2026-08-29T20:30:00+02:00",
            "reviewed_git_commit": __import__("subprocess").check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        })
        first = next(iter(payload["bound_sha256"]))
        payload["bound_sha256"][first] = "0" * 64
        with patch("peft_workshop.sprint6_open_approval._git", side_effect=lambda *args: "" if args[0] == "status" else "test-ref"):
            report = validate_approval(self._write(payload), require_clean_git=False)
        self.assertEqual(report["decision"], "HOLD_INVALID_OR_INCOMPLETE_APPROVAL")
        self.assertFalse(report["checks"]["all_bound_hashes_match"])
