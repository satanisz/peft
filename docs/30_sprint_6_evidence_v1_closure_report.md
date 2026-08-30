# Sprint 6 — raport zamknięcia Protected Evidence v1

## Decyzja

**`EVIDENCE_V1_CLOSED_READ_ONLY`**

Lifecycle Evidence v1:

**`CONSUMED_FROZEN_READ_ONLY_FAILED_THRESHOLDS`**

Benchmark pozostaje nieudany względem zamrożonych progów. Zamknięcie nie zmienia wyniku na PASS i nie oznacza zgody produkcyjnej.

## Akceptacja właściciela S6.5A

Właściciel jawnie zaakceptował, że:

- benchmark nie przeszedł,
- wynik zostanie pokazany uczciwie,
- zostanie wykorzystany jako case dydaktyczny,
- adapter nie będzie przedstawiany jako rozwiązanie produkcyjne,
- Evidence v1 nie zostanie uruchomione ponownie.

Akceptację zapisano oddzielnie od zamrożonego kontraktu i historycznego approval.

## Integralność S6.5B

- 20/20 kontroli closure: PASS,
- 37 artefaktów związanych SHA-256,
- approval otwarcia zachowany bez zmian,
- jawne potwierdzenie operatora potwierdzone,
- `protected_splits_opened=true`,
- `FAILED_EVIDENCE_THRESHOLDS` zachowane,
- brak retuningu po evidence,
- rerun Evidence v1: zabroniony,
- production approval: `false`.

Closure obejmuje approval, autoryzację operatora, wszystkie wyniki per seed, raport zbiorczy, primary/shadow review, końcowy review oraz owner acceptance.

## Reguła dalszego użycia

Evidence v1 może być używane wyłącznie:

- do analizy błędów,
- jako materiał dydaktyczny,
- jako przyszły zbiór diagnostyczny lub regresyjny.

Nie może być ponownie przedstawione jako niezależny test poprawionej wersji modelu. Nowa wersja Q1.1/Q2.1 wymaga osobnego Evidence v2 zamrożonego przed inferencją.

## Następny krok

`BUILD_WORKSHOP_EVIDENCE_PACKAGE_S6_5C` — przygotowanie finalnego appendixu/handoutu i scenariusza prowadzącego na podstawie zamrożonych wyników.

## Artefakty

- `results/sprint6/m6_owner_acceptance.json`
- `results/sprint6/protected_evidence_v1_closure.json`
- `src/peft_workshop/sprint6_evidence_closure.py`
- `tests/test_sprint6_evidence_closure.py`
