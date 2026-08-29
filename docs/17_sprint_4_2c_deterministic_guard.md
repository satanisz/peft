# Sprint 4.2C — deterministic decision containment

## Decyzja wykonawcza

Sprint 4.2B pozostaje uczciwym wynikiem `HOLD_PROMPT_V2_THRESHOLDS`.
Nie zmieniamy złotych odpowiedzi, nie obniżamy progów i nie wykonujemy kolejnego
prompt-only rerunu. Sprint 4.2C dodaje warstwę bezpieczeństwa do demonstracji,
ale nie zmienia metryk predykcyjnych modelu i nie otwiera protected evidence.

## Problem

W FC-209 każdy seed poprawnie zapisał obliczenie `2418 - 2391 = 27`, po czym
błędnie uznał, że 27 mln PLN nie przekracza progu 5 mln PLN. Obecny Q2 guard
potwierdzał obecność obliczenia, schemat, status-policy i identyfikatory źródeł,
ale nie wiązał wyniku liczbowego z decyzją statusową.

## Rozwiązanie

Wersjonowana reguła `CROSS-REPORT-MATERIAL-DIFFERENCE-V1`:

- odczytuje wyłącznie `input.deterministic_check.result`,
- stosuje jawne porównanie `abs(result) > 5`,
- wymaga `FAIL`, gdy warunek jest spełniony, i `PASS` w przeciwnym przypadku,
- nie odczytuje `expected_output`,
- nie poprawia statusu ani narracji modelu,
- blokuje sprzeczną odpowiedź i kieruje ją do human review.

Reguła jest zewnętrzna wobec promptu i adaptera. Dzięki temu szkolenie pokazuje
podział odpowiedzialności: LLM interpretuje dokumenty i buduje uzasadnienie,
a kod deterministyczny egzekwuje proste reguły liczbowe.

## Ograniczenie metodologiczne

Regułę zaprojektowano po zobaczeniu błędu diagnostycznego. Może być użyta jako
retrospektywna demonstracja bezpieczeństwa i wzorzec przyszłej architektury, ale
nie jest niezależnym dowodem generalizacji. Nie może zmienić protected gate z
`HOLD` na `APPROVED_TO_OPEN_PROTECTED_SPLITS`.

## Uruchomienie

```powershell
.\scripts\run_sprint4_2c_guard.ps1
```

Skrypt ponownie ocenia zapisane predykcje trzech seedów. Nie ładuje modelu, nie
korzysta z GPU i nie wykonuje inferencji.

## Kryterium zakończenia

- dokładnie 30 odpowiedzi ocenionych dla każdego seeda,
- FC-209 zablokowany we wszystkich trzech seedach kodem
  `DETERMINISTIC_DECISION_MISMATCH`,
- żadna zablokowana odpowiedź nie zostaje zaakceptowana ani poprawiona,
- pozostałe 29 przypadków zachowuje poprzednią decyzję guard,
- protected evidence pozostaje zamknięte,
- wynik może otrzymać status `READY_FOR_SPRINT5_DEMO_WITH_PROTECTED_HOLD`.
