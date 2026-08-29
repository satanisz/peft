# Sprint 6 — raport S6-G0 Evidence Contract Freeze

**Data:** 29 sierpnia 2026

**Decyzja:** `S6_G0_PASS`

**Commit walidowany:** `e37e9056206d1c60c32c329ec03924a0ca505e91`

## Wynik

M5 pozostaje zamknięta tagiem `content-freeze-v1`, a kontrakt dowodowy Sprintu
6 został zamrożony. Wszystkie kontrole G0 przeszły. Preflight nie odczytał treści
protected splits ani goldów i nie utworzył autoryzacji do ich otwarcia.

## Najważniejsze potwierdzenia

- materiały są identyczne z tagiem `content-freeze-v1`,
- talia ma 53 slajdy, 53 zestawy notatek i 53 bloki źródeł,
- trzy notebooki są poprawne składniowo,
- 68 testów przeszło,
- wszystkie trzy treningi Q1 są kompletne i mają zero truncation,
- peak GPU każdego seeda pozostaje poniżej 12 GiB,
- konfiguracje treningowe są zgodne z hashami zapisanymi w metrykach,
- trzy adaptery mają zgodny model bazowy, rozmiary i SHA-256,
- wszystkie seedy używają jednego kontraktu promptu,
- primary evidence thresholds są identyczne w matrix i bramce Sprintu 6,
- `challenge severity ≥ 0,85` jest teraz egzekwowane i ma test regresyjny,
- nie istnieją wyniki `original_test`, `boundary_test`, `challenge` ani plik
  autoryzacji protected evidence.

## Zmiana bezpieczeństwa

Runner protected evidence wymaga obecnie łącznie:

1. `S6_G0_PASS`,
2. `S6_G1_PASS`,
3. `S6_G2_PASS`,
4. osobnego commita z `APPROVED_TO_OPEN_PROTECTED_SPLITS`,
5. jawnego parametru potwierdzającego operatora.

Brak któregokolwiek elementu zatrzymuje wykonanie przed odczytem protected
splits.

## Dozwolony następny krok

`AUTHOR_AND_REVIEW_SHADOW_CHALLENGE_V1` — przygotowanie 50 nowych przypadków,
pełny review goldów i wydanie decyzji S6-G1. Protected evidence nadal pozostaje
`HOLD_PENDING_S6_G1_G2_AND_OPERATOR_APPROVAL`.

Pełny raport maszynowy:
[`../results/sprint6/g0_preflight.json`](../results/sprint6/g0_preflight.json).
