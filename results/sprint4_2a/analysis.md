# Sprint 4.2A — analiza severity i source integrity

**Decyzja:** `HOLD_DIAGNOSTIC_THRESHOLDS`

## Niespójność kontraktu severity

| Dataset | Rekordy | Niezgodne | Udział |
|---|---:|---:|---:|
| data/generated/dataset_v1/train.jsonl | 400 | 96 | 24.0% |
| data/generated/dataset_v1/development.jsonl | 50 | 12 | 24.0% |
| data/generated/dataset_v1/validation.jsonl | 50 | 12 | 24.0% |
| data/splits/boundary_train.jsonl | 240 | 0 | 0.0% |
| data/splits/boundary_development.jsonl | 60 | 0 | 0.0% |
| data/splits/boundary_validation.jsonl | 120 | 0 | 0.0% |

Original dataset-v1 zachowuje legacy severity jako metrykę informacyjną. Boundary i diagnostic egzekwują status-policy-v1.

## Q1 — dostępne validation

| Seed | Severity original legacy | Zgodność predykcji z policy-v1 | Severity boundary | Sources original | Sources boundary |
|---:|---:|---:|---:|---:|---:|
| 20260827 | 94.0% | 74.0% | 100.0% | 100.0% | 100.0% |
| 20260828 | 94.0% | 78.0% | 100.0% | 100.0% | 99.2% |
| 20260829 | 98.0% | 74.0% | 100.0% | 100.0% | 100.0% |

Diagnostic set: 30 przypadków, błędy schematu: 0, niezgodności severity policy: 0.

## Q2 — diagnostyczne inferencje

| Seed | Status accuracy | Macro-F1 | Sources | Severity | Human review | Guard pass-through | Guard blocks |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 20260827 | 83.3% | 0.832 | 100.0% | 76.7% | 90.0% | 83.3% | 5 |
| 20260828 | 86.7% | 0.856 | 96.7% | 83.3% | 93.3% | 83.3% | 5 |
| 20260829 | 93.3% | 0.924 | 100.0% | 90.0% | 100.0% | 90.0% | 3 |

Guard blokuje odpowiedzi niespełniające kontraktu i nie wykonuje cichej korekty.

Protected splits pozostają nieotwarte.
