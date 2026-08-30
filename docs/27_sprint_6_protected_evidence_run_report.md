# Sprint 6 — protected evidence run: wynik inferencji i monitoringu

## Executive decision

Run został wykonany po jednorazowym, jawnym potwierdzeniu operatora i zgodnie z zamrożonym kontraktem. Wszystkie 870 zaplanowanych inferencji zakończyło się technicznie (300 `original_test`, 360 `boundary_test`, 60 `challenge`, 150 `shadow_challenge`). Wynik jakościowy pozostaje:

**`FAILED_EVIDENCE_THRESHOLDS` / `FAILED_SHADOW_THRESHOLDS`**

Nie wykonywano retuningu, zmiany promptu, guardów ani kontrolowanego rerunu. Wynik jest materiałem diagnostycznym i warsztatowym, a nie zgodą produkcyjną.

## Wyniki primary evidence

- `original_test`: macro-F1 średnio **0.9711**, minimum seed **0.9405** — PASS.
- `boundary_test`: macro-F1 **1.0000** dla każdego seeda; wszystkie zamrożone kontrole boundary — PASS.
- `challenge`: status accuracy średnio **0.70** (0.65–0.75), próg średni 0.85; severity correctness średnio **0.6167**, próg 0.85 — FAIL.
- schema i source integrity dla challenge pozostały na poziomie 1.0 — problem dotyczy jakości decyzji, nie formatu ani traceability.

## Wyniki shadow evidence

- 3 × 50 przypadków zostało wykonanych i odseparowanych od treningu.
- macro-F1 średnio **0.8626** (0.8531–0.8750) — PASS względem progu agregatowego.
- schema, severity i source integrity — PASS; unsafe-pass rate **0.0**; zablokowane odpowiedzi nie zostały zaakceptowane.
- `WARN` i `NOT_APPLICABLE` — PASS.
- `INSUFFICIENT_DATA` recall średnio **0.60** (0.50–0.70) — FAIL względem zamrożonego minimum 0.75 dla każdego seeda.
- deterministic mismatch detection — 100%; w dwóch seedach guard wykrył rozbieżności, w tym brak deterministycznej kalkulacji.

## Monitoring i bezpieczeństwo procesu

Runner utworzył osobny artefakt autoryzacji protected split oraz raporty per seed. Approval i kontrakt pozostały niezmienione. Nie stwierdzono technicznego przerwania runu ani użycia shadow danych w treningu. `shadow_manual_response_review.json` ma status `PENDING_HUMAN_REVIEW` (50/50 przypadków, 0/150 odpowiedzi ocenionych), dlatego nie można jeszcze zamknąć manual-review gate.

## Decyzja operacyjna

1. Nie otwierać protected evidence jako `APPROVED` dla jakości modelu.
2. Zachować wyniki jako kontrolowany case: model przechodzi format, źródła i boundary, lecz nie przechodzi trudnych decyzji `challenge` oraz klasy `INSUFFICIENT_DATA` w shadow.
3. Kolejny krok: osobny przegląd Sol/high przyczyn błędów i kryteriów gold; ewentualny rerun wyłącznie po nowej, jawnej decyzji operatora i zmianie wersji artefaktów.

## Artefakty

- `results/sprint4/protected_split_authorization.json`
- `results/sprint4/seed_*_{original_test,boundary_test,challenge}*`
- `results/sprint6/seed_*_shadow_challenge*`
- `results/sprint6/evidence_summary.json`
- `results/sprint6/shadow_manual_response_review.json`
