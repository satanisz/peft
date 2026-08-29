from __future__ import annotations

import unittest

from peft_workshop.sprint6_preflight import _notebook_contract, _pptx_contract, build_preflight


class Sprint6PreflightTests(unittest.TestCase):
    def test_deck_and_notebook_contracts_are_frozen(self) -> None:
        self.assertEqual(
            _pptx_contract("materials/PEFT_LoRA_QLoRA_w_banku_workshop.pptx"),
            {"slides": 53, "notes": 53, "notes_with_sources": 53},
        )
        notebooks = _notebook_contract()
        self.assertEqual(notebooks["count"], 3)
        self.assertGreater(notebooks["compiled_code_cells"], 0)

    def test_development_preflight_never_opens_protected_content(self) -> None:
        result = build_preflight(
            require_clean_git=False,
            run_tests=False,
            verify_content_freeze=False,
            verify_adapter_files=False,
        )

        self.assertFalse(result["protected_content_read"])
        self.assertEqual(result["protected_result_paths_found"], [])
        self.assertTrue(result["checks"]["s6_gate_is_hold"])
        self.assertTrue(result["checks"]["challenge_severity_is_enforced"])


if __name__ == "__main__":
    unittest.main()
