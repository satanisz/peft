# Karta danych — shadow-challenge-v1

**Wersja:** `shadow-challenge-1.0.0`
**Status:** authoring i kontrola wspomagana zakończone; oczekuje na niezależne
review człowieka/SME.

**Język:** polski
**Charakter:** wyłącznie dane syntetyczne, fikcyjny bank i fikcyjne źródła.

## Przeznaczenie

Zbiór służy do pokazania odporności systemu `Financial Control Copilot` na
ryzyka poznane podczas wcześniejszej diagnostyki, w szczególności błąd FC-209.
Jest to dowód kierowany ryzykiem, utworzony po analizie błędów. Nie jest i nie
może być przedstawiany jako pierwotnie niezależny benchmark.

Nie wolno używać zbioru do treningu, strojenia hiperparametrów, promptu, guarda
ani progów. Po zamrożeniu goldów pierwsza inferencja jest wynikiem zachowanym;
błąd jakościowy nie uprawnia do poprawienia systemu i powtórzenia tej samej
wersji eksperymentu.

## Skład

Zbiór zawiera 50 przypadków `FC-301`–`FC-350`: po 10 dla statusów `PASS`,
`WARN`, `FAIL`, `INSUFFICIENT_DATA` i `NOT_APPLICABLE` oraz po 10 dla pięciu
rodzin ryzyka:

- arytmetyka i materialność między raportami,
- integralność oraz dobór źródeł,
- stosowalność kontroli kontra brak danych,
- severity i wymóg human review,
- prompt injection oraz neutralne regresje.

Każdy przypadek ma unikalny `family_id`, jawną provenance, jedną przesłankę
rozstrzygającą, oczekiwane zachowanie guarda i gold zgodny z polityką statusów.

## Pochodzenie i niezależność

Przypadki zostały napisane ręcznie na Sol/high bez generatorów wcześniejszych
zbiorów. Korzystają z nowego fikcyjnego pakietu
`data/source/fictional_bank_shadow_2026.json`. Audyt porównuje je wyłącznie z
dozwolonymi, niechronionymi splitami train/development/validation oraz zbiorem
diagnostycznym. Treść primary protected evidence nie była odczytywana.

Audyt authoringu wykazał zero dokładnych duplikatów i zero wspólnych
`family_id`; maksymalne podobieństwo sekwencyjne wynosi 0,595238 przy limicie
<0,75, a Jaccarda 0,392157 przy limicie <0,55.

## Review i freeze

Kontrola wspomagana Sol/high objęła 50/50 przypadków i nie wykazała uwag
krytycznych. Nie jest ona niezależna od authoringu. Bramka S6-G1 wymaga osobnej
akceptacji 50/50 przypadków przez człowieka/SME, nazwiska recenzenta, daty oraz
zera nierozstrzygniętych błędów krytycznych. Do tego czasu status to
`S6_G1_HOLD_PENDING_HUMAN_SME`.

## Ograniczenia

- dane są syntetyczne i nie reprezentują pełnej zmienności dokumentów banku,
- projekt przypadków zna wcześniej odkryte ryzyka i może je nadreprezentować,
- wynik nie jest zgodą na wdrożenie produkcyjne,
- po otwarciu nie należy interpretować tego zbioru jako niezależnego testu
  generalizacji na nieznane błędy.

Hashe, provenance per przypadek i wynik audytu znajdują się odpowiednio w
`data/shadow_registry.json` i `results/sprint6/shadow_authoring_audit.json`.
