# Sprint 4 — bramka przed otwarciem testów

**Decyzja:** `READY_TO_OPEN_PROTECTED_SPLITS`

| Seed | Oryginalny F1 | Boundary F1 | Severity orig. | Sources boundary | WARN | N/A | Pary | FAIL FPR | Unsafe PASS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 20260827 | 1.000 | 1.000 | 94.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| 20260828 | 1.000 | 1.000 | 94.0% | 99.2% | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| 20260829 | 1.000 | 1.000 | 98.0% | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |

| Kryterium | Wynik |
|---|---|
| exactly_three_complete_training_runs | PASS |
| zero_training_truncation | PASS |
| peak_vram_within_budget | PASS |
| original_macro_mean | PASS |
| original_macro_each_seed | PASS |
| boundary_macro_mean | PASS |
| boundary_macro_each_seed | PASS |
| boundary_macro_seed_range | PASS |
| schema_each_seed | PASS |
| severity_each_seed | PASS |
| sources_each_seed | PASS |
| warn_recall_each_seed | PASS |
| not_applicable_recall_each_seed | PASS |
| pair_accuracy_each_seed | PASS |
| fail_fpr_each_seed | PASS |
| unsafe_pass_each_seed | PASS |

Protected splits pozostają nieotwarte. Decyzja READY dotyczy wyłącznie bramki automatycznej; obowiązuje także osobny review analityczny i jawne potwierdzenie operatora.
