# Sprint 4.2A — analiza severity i source integrity

**Decyzja:** `HOLD_PENDING_INDEPENDENT_REVIEW_AND_Q2_DIAGNOSTIC`

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

Protected splits pozostają nieotwarte.
