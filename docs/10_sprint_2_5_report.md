# Raport Sprintu 2.5 — Label Boundary Hardening

## Decyzja wykonawcza

Sprint 2.5 jest **warunkowo zaakceptowany do celów warsztatowych**. Powstały
polityka statusów, 540-elementowy boundary pack, rozszerzone metryki oraz
formalne porównanie B1/B2/B3. Nie zmieniono `dataset-v1.0.0` ani
`baseline-v1.0.0`; oryginalne `test` i `challenge` oraz boundary `test`
pozostają nieotwarte. Sprint 3 może rozpocząć się po 21:00.

B3 jest nowym, najsilniejszym baseline'em promptowym dla granic etykiet. Na
boundary validation osiąga macro-F1 0,894 i pair accuracy 81,7%, ale wymaga
średnio 2897 tokenów wejścia oraz 10,54 GiB peak VRAM. Sprint 3 powinien
sprawdzić, czy QLoRA może zbliżyć się do tej jakości przy krótszym wejściu.

Tag `boundary-pack-v1.0.0` zostanie utworzony dopiero po akceptacji polityki
statusów przez właściciela projektu. Obecny pakiet jest zatwierdzony technicznie
wyłącznie jako materiał syntetycznego warsztatu, nie jako polityka bankowa.

## Zakres wykonany

- jawna hierarchia `NOT_APPLICABLE → INSUFFICIENT_DATA → FAIL → WARN → PASS`,
- macierz stosowalności dla 9 rodzajów kontroli,
- porządkowa macierz kosztu pomyłek biznesowych,
- 270 minimalnych par, w których zmienia się dokładnie jedna przesłanka,
- grupowy train/development/validation/test,
- review 100% N/A i warstwowej próbki ponad 20% pozostałych danych,
- B3 z pięcioetykietową hierarchią i trzema trudnymi demonstracjami,
- metryki par, unsafe PASS, nadmiernej eskalacji i kosztu błędu,
- odtwarzalne wyniki B1/B2/B3 na 120 przypadkach validation.

## Boundary pack

| Split | Rekordy | Pary | Status |
|---|---:|---:|---|
| train | 240 | 120 | dostępny dla treningu i demonstracji |
| development | 60 | 30 | użyty do jednej iteracji B3 |
| validation | 120 | 60 | użyty raz po freeze B3 |
| test | 120 | 60 | nieotwarty |
| **Razem** | **540** | **270** | |

| Status | Train | Development | Validation | Test | Razem |
|---|---:|---:|---:|---:|---:|
| PASS | 40 | 10 | 15 | 15 | 80 |
| WARN | 80 | 20 | 30 | 30 | 160 |
| FAIL | 40 | 10 | 15 | 15 | 80 |
| INSUFFICIENT_DATA | 40 | 10 | 30 | 30 | 110 |
| NOT_APPLICABLE | 40 | 10 | 30 | 30 | 110 |

Audyt potwierdza:

- 540/540 poprawnych rekordów,
- 270/270 par z jedną zmienioną przesłanką,
- zero dokładnych duplikatów,
- zero rodzin współdzielonych między splitami,
- `WARN` i `NOT_APPLICABLE` w 9 typach kontroli,
- brak jawnej złotej etykiety w zadaniu lub źródłach,
- review 110/110 N/A oraz 101 innych rekordów,
- zero krytycznych błędów w review implementacyjnym.

SHA-256 pełnego pakietu:
`f064cc2225e2e4175ff95e97672a185a01ee568d7fe44b39546cea72e8d1aec1`.

## B3 — przebieg rozwoju i freeze

Pierwszy wariant z pięcioma pełnymi demonstracjami został odrzucony w smoke
teście: całkowite użycie GPU dochodziło do około 11,6 GiB, a pojedyncza
generacja nie zakończyła się w 180 sekund. Zgodnie z planem zastosowano wariant
kompaktowy:

- hierarchia opisuje wszystkie 5 statusów,
- stałe przykłady obejmują `WARN`, `NOT_APPLICABLE` i `INSUFFICIENT_DATA`,
- przykłady pochodzą z train i nie współdzielą rodziny z celem,
- smoke wersji zamrożonej: 2894 input tokens, 17,62 s, 10,45 GiB, brak
  obcięcia.

Na development wykonano jedną jawną iterację. V0 nadmiernie eskalował sześć
przypadków braku danych do `FAIL`. Dodano regułę, że brak obowiązkowego źródła
sam w sobie nie uzasadnia `FAIL`.

| B3 development | V0 | V1 zamrożona | Zmiana |
|---|---:|---:|---:|
| Status accuracy | 85,0% | 91,7% | +6,7 p.p. |
| Macro-F1 | 0,823 | 0,913 | +0,089 |
| WARN recall | 90,0% | 90,0% | 0 p.p. |
| N/A recall | 100,0% | 100,0% | 0 p.p. |
| INSUFFICIENT_DATA recall | 40,0% | 80,0% | +40 p.p. |
| FAIL FPR | 14,0% | 6,0% | −8 p.p. |

Po tej iteracji prompt, hash i demonstracje zostały zamrożone. Nie wprowadzono
żadnej zmiany na podstawie formalnego validation.

## Formalne wyniki boundary validation

| Wariant | Schemat | Accuracy | Macro-F1 | WARN recall | N/A recall | Brak danych recall | Pair accuracy | FAIL FPR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B1 | 97,5% | 48,3% | 0,479 | 46,7% | 53,3% | 10,0% | 23,3% | 32,4% |
| B2 | 100,0% | 60,8% | 0,606 | 76,7% | 66,7% | 0,0% | 38,3% | 43,8% |
| **B3** | **100,0%** | **90,8%** | **0,894** | **93,3%** | **100,0%** | **76,7%** | **81,7%** | **8,6%** |

B2 poprawia `WARN`, lecz wszystkie 30 przypadków `INSUFFICIENT_DATA` klasyfikuje
jako `FAIL`; dodatkowo eskaluje do `FAIL` 10 z 30 przypadków N/A. Pokazuje to,
że dowolny few-shot nie jest bezpiecznym upper boundem, jeżeli demonstracje nie
odzwierciedlają jawnej polityki decyzji.

B3 popełnia 11 błędów statusu:

- 7 × `INSUFFICIENT_DATA → FAIL`,
- 2 × `PASS → FAIL`,
- 2 × `WARN → PASS`.

Nie przeoczył żadnego `FAIL` i prawidłowo rozpoznał wszystkie 30 przypadków
N/A. Nadal wymaga human-in-the-loop, ponieważ siedem braków danych nadmiernie
eskaluje, a dwa ostrzeżenia przepuszcza jako `PASS`.

## Koszt biznesowy i techniczny

| Wariant | Unsafe PASS | Nadmierna eskalacja | Śr. koszt błędu | Śr. input | p95 | Peak VRAM | Truncated |
|---|---:|---:|---:|---:|---:|---:|---:|
| B1 | 14,7% | 37,8% | 2,24 | 1057 | 16,99 s | 8,09 GiB | 2,5% |
| B2 | 1,3% | 51,1% | 1,61 | 2683 | 31,41 s | 10,35 GiB | 0% |
| B3 | 2,7% | 7,8% | 0,38 | 2897 | 32,39 s | 10,54 GiB | 0% |

Wagi kosztu są porządkowe i służą szkoleniu. Nie reprezentują kwot ani apetytu
na ryzyko konkretnego banku. B3 obniża średni koszt o 76% względem B2, ale
zużywa o około 175% więcej tokenów wejściowych niż B1.

## Bramka M2.5

| Kryterium | Wynik |
|---|---|
| Polityka pięciu statusów i macierz stosowalności | gotowe; sign-off właściciela oczekuje |
| Dokładnie 540 poprawnych rekordów | PASS |
| Brak leakage i duplikatów | PASS |
| Review 100% N/A i ≥20% pozostałych | PASS implementacyjny |
| Brak krytycznego błędu złotej etykiety | PASS w wykonanym review |
| B3 smoke, development i formalne validation | PASS |
| Konfiguracje, demo IDs, hashe i wyniki | PASS |
| Testy i challenge nieotwarte | PASS |

**Status bramki:** `CONDITIONALLY_ACCEPTED_FOR_WORKSHOP` — decyzja z 26
sierpnia 2026. Sprint 3 może rozpocząć się po 21:00.

### Warunki akceptacji

1. Polityka statusów i wagi kosztów są syntetycznymi artefaktami warsztatowymi,
   a nie polityką produkcyjną banku.
2. Dla rzeczywistych danych bankowych pozostaje wymagany human-in-the-loop i
   niezależny review ekspercki.
3. Sprint 3 raportuje osobno `WARN`, `NOT_APPLICABLE`, `INSUFFICIENT_DATA`,
   unsafe `PASS` oraz nadmierną eskalację.
4. Boundary test, oryginalny test i challenge pozostają nieotwarte do Sprintu
   4.
5. Ryzyka jawnie zachowane w rejestrze: 7 przypadków
   `INSUFFICIENT_DATA → FAIL` i 2 przypadki `WARN → PASS` dla B3.

Nie tworzono taga `boundary-pack-v1.0.0`: formalne zamrożenie danych wymaga
odrębnej decyzji przed użyciem poza kontekstem warsztatowym.

## Konsekwencje dla Sprintu 3

1. **Q0** trenujemy wyłącznie na `dataset-v1.0.0`, aby zmierzyć wpływ samego
   adaptera.
2. **Q1** trenujemy na train v1 + boundary train, aby zmierzyć wpływ danych
   granicznych.
3. B3 jest jakościowym baseline'em dla boundary validation; B1 pozostaje
   baseline'em kosztowym.
4. Q1 musi raportować oba validation oddzielnie.
5. Jeśli Q1 nie poprawi granic, najpierw analizujemy sampling i dane, a nie
   szeroki sweep ranków.
6. Boundary test, oryginalny test i challenge otwieramy dopiero w Sprincie 4.

## Główne artefakty

- `configs/status_policy_v1.json`,
- `configs/baseline_b3_v1.json`,
- `data/generated/boundary_pack_v1.jsonl`,
- `data/splits/boundary_*.jsonl`,
- `data/BOUNDARY_DATASET_CARD.md`,
- `data/boundary_registry.json`,
- `results/sprint2_5_boundary_audit.json`,
- `results/boundary_v1_validation_summary.json`,
- `results/boundary_v1_validation_summary.md`,
- `results/b{1,2,3}_boundary_validation*.json*`.
