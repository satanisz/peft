import unittest

from peft_workshop.baseline_report import VARIANTS, render_markdown


class BaselineReportTests(unittest.TestCase):
    def test_markdown_contains_all_variants_and_best_result(self) -> None:
        comparison = {}
        errors = {}
        for index, variant in enumerate(VARIANTS):
            comparison[variant] = {
                "count": 50,
                "json_valid_rate": 1.0,
                "schema_valid_rate": 1.0,
                "status_correct_rate": 0.6 + index / 10,
                "macro_f1": 0.5 + index / 10,
                "sources_valid_rate": 1.0,
                "fail_false_positive_rate": 0.0,
                "p95_latency_s": 2.0,
                "peak_gpu_allocated_gib": 8.0,
            }
            errors[variant] = []
        output = render_markdown(
            {"split": "validation", "comparison": comparison, "error_catalog": errors}
        )
        self.assertIn("| B0 |", output)
        self.assertIn("| B1 |", output)
        self.assertIn("| B2 |", output)
        self.assertIn("uzyskał **B2**", output)


if __name__ == "__main__":
    unittest.main()
