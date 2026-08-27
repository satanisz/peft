# Sprint 3 — wynik bramki M3

**Decyzja:** `PASS`

| Wariant | Schemat | Macro-F1 | WARN | N/A | Brak danych | Pary | FAIL FPR | Unsafe PASS | Eskalacja | Input |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B3_boundary | 100.0% | 0.894 | 93.3% | 100.0% | 76.7% | 81.7% | 8.6% | 2.7% | 7.8% | 2897 |
| Q0_boundary_validation | 100.0% | 0.786 | 66.7% | 80.0% | 90.0% | 61.7% | 9.5% | 8.0% | 11.1% | 1401 |
| Q1_boundary_validation | 100.0% | 1.000 | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% | 1401 |

Redukcja tokenów Q1 względem B3: 51.6%.

## Bramka

| Kryterium | Wynik |
|---|---|
| q0_training_completed | PASS |
| q1_training_completed | PASS |
| q1_zero_training_truncation | PASS |
| q1_peak_vram_at_most_12_gib | PASS |
| demo_at_most_15_minutes | PASS |
| adapter_reload_schema_valid | PASS |
| schema_valid_at_least_98_percent | PASS |
| boundary_quality_or_token_efficiency | PASS |
| warn_recall_no_regression | PASS |
| not_applicable_recall_at_least_60_percent | PASS |
| fail_false_positive_rate_at_most_15_percent | PASS |
| pass_recall_regression_at_most_5pp | PASS |
| fail_recall_regression_at_most_5pp | PASS |

## Ograniczenia

Wyniki dotyczą danych syntetycznych i nie stanowią polityki produkcyjnej banku; wymagany jest human-in-the-loop.
Oryginalny test, boundary test i challenge pozostają nieotwarte do Sprintu 4.
