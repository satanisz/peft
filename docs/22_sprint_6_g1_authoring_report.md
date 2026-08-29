# Sprint 6 — raport authoringu S6-G1 Shadow freeze

**Data:** 29 sierpnia 2026

**Model authoringu i kontroli:** Sol/high

**Decyzja:** `S6_G1_HOLD_PENDING_HUMAN_SME`
**Protected evidence:** zamknięte; zero odczytanej treści i zero inferencji.

## Wynik

Powstało 50 nowych przypadków `shadow-challenge-v1` i osobny fikcyjny pakiet
źródłowy. Zbiór jest równomierny: po 10 przypadków dla każdego z pięciu statusów
oraz po 10 dla każdej rodziny ryzyka. Wszystkie przypadki przeszły schema,
status policy, source-id oraz kontrolę pól `severity` i `requires_human_review`.

Audyt niezależności od dozwolonych wcześniejszych danych wykazał:

- 0 dokładnych duplikatów,
- 0 wspólnych `family_id`,
- maksymalne podobieństwo sekwencyjne 0,595238 przy limicie <0,75,
- maksymalny Jaccard 0,392157 przy limicie <0,55,
- 950 porównanych przypadków z niechronionych splitów,
- brak odczytu primary protected evidence.

Kontrola wspomagana Sol/high objęła 50/50 goldów i nie wskazała błędu
krytycznego. Ponieważ autor i reviewer wspomagany nie są od siebie niezależni,
nie jest to formalna akceptacja SME.

## Artefakty i integralność

- dataset: `data/shadow/shadow_challenge_v1.jsonl`, SHA-256
  `18472606c9043b13e9d89d769ee38005cdce846e022c61096be17a481716cd93`,
- source pack: `data/source/fictional_bank_shadow_2026.json`, SHA-256
  `1014c086f4d55fc12c9aed7d8ae5ccadc8c28a4d47c8313d9f3371727abe0c7c`,
- provenance: `data/shadow_registry.json`,
- assisted review: `data/reviews/shadow_challenge_v1_assisted_review.json`,
- szablon niezależnego review: `data/reviews/shadow_challenge_v1_review.json`,
- wynik bramki: `results/sprint6/g1_shadow_freeze.json`.

## Znaczenie decyzji HOLD

Warstwa mechaniczna G1 jest kompletna. HOLD nie oznacza błędu zbioru; chroni
rozdział ról i uniemożliwia modelowi samodzielne zatwierdzenie własnych goldów.
Następny krok to review 50/50 przypadków przez człowieka/SME. Po wypełnieniu
szablonu ponowne uruchomienie bramki może wydać `S6_G1_PASS`.

Nawet G1 PASS nie otwiera protected evidence. Kolejnym etapem jest S6-G2 na
Luna/low, następnie osobny review Sol/high i jawna decyzja operatora.
