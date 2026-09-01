# S7.2 — końcowy review pakietu przez Sol/high

## Decyzja

**`S7_2_SOL_REVIEW_HOLD_REAUTHOR_REQUIRED`**

Pakiet osiąga wymagane liczności, ale nie spełnia zamrożonego kontraktu danych
ani gold rubric. Nie może zostać przekazany do review człowieka/SME, użyty w
S7.3 ani wykorzystany do treningu Q2. Evidence v1 pozostaje niezmienione i nie
zostało uruchomione.

## Co przeszło

- utworzono 300 przypadków train i 90 dev;
- liczności statusów sumują się do zamrożonej macierzy;
- istnieje 36 dwuelementowych grup oznaczonych jako kontrfaktyczne;
- istniejące wpisy SHA-256 w registry zgadzają się z plikami;
- 91 historycznych testów przechodzi;
- nie uruchomiono Q2 ani Evidence v1/v2.

Powyższe wyniki potwierdzają kompletność mechaniczną plików, ale nie ich
przydatność semantyczną.

## Blokery

| Obszar | Wynik | Znaczenie |
|---|---:|---|
| Zgodność z obecnym JSON Schema | 390/390 nieważnych | Schema nie dopuszcza identyfikatorów S7T/S7D i nie została rozszerzona zgodnie z kontraktem v2. |
| Pola kontroli v2 | brak w 390/390 | Brakuje `applicability_rule` i `required_evidence_roles`. |
| Pola źródeł v2 | brak w 390/390 | Brakuje `source_role`, `trusted_for_evidence` i `evidence_role` w danych przekazywanych modelowi. |
| Metadata v2 | brak w 390/390 | Nie zapisano m.in. `authoring_seed`, `risk_stratum`, identyfikatora pary i zmienionej przesłanki. |
| Source ID | 877/877 niezgodnych | Identyfikatory nie spełniają zamrożonego wzorca z separatorem przed rolą źródła. |
| Leakage golda do wejścia | 390/390 | Każdy task jawnie poleca zwrócić oczekiwany status, więc benchmark mierzyłby kopiowanie etykiety. |
| Pary kontrfaktyczne | 36/36 nieważnych | Członkowie zmieniają typ kontroli, rodzinę, encję, liczby i dokument zamiast jednej przesłanki. |
| `NOT_APPLICABLE` | 57/57 bez `SCOPE_FACT` | Status nie jest udowodniony strukturalnym faktem zakresu. |
| `INSUFFICIENT_DATA` | 99/99 bez deklaracji ról | Nie można mechanicznie wykazać, którego wymaganego dowodu brakuje. |
| Kontrole deterministyczne | 44/44 bez progu | Wynik obliczenia nie jest związany z tolerancją/materiality ani statusem. |
| Source pack | 877 błędnych ról | Użyto niedozwolonej roli `PRIMARY`; brak `evidence_role`. |
| Untrusted sources | 97 utraconych flag | Źródła oznaczone sufiksem `u` zostały zapisane jako zaufane. |
| Assisted review | 390/390 niekompletnych rekordów | Review deklaruje PASS bez pól wymaganych przez rubric i bez uzasadnienia. |
| Similarity/leakage | raport niepełny | Scanner nie czyta exclusion registry ani plików zakazanych; sprawdza tylko exact duplicate task+procedure. |
| Registry | brak 5 wymaganych hashy | Nie związano specyfikacji, rubric, polityk ani raportu similarity. |

## Najważniejszy błąd semantyczny

Źródła przypadków nie zawierają wystarczającej przesłanki dla zadanych statusów.
Przykładowo przypadek może mieć status `PASS`, mimo że obliczenie wynosi `-38`
i nie podano żadnego progu. Status jest poprawny wyłącznie dlatego, że został
wpisany wprost do treści zadania. Takie dane nauczyłyby adapter rozpoznawania
etykiety w promptcie, a nie wykonywania kontroli finansowej.

## Ocena dotychczasowych walidatorów

Mechanical gate był fałszywie dodatni. Validator sprawdzał liczność, relację
severity–status i istnienie source ID, ale nie egzekwował pełnego kontraktu v2.
Za parę kontrfaktyczną uznawał dowolną grupę dwóch przypadków. Assisted review
ustawiał `ASSISTED_PASS` bez wykonania kryteriów rubric. Similarity scanner
ustawiał `forbidden_registry_consulted=true`, chociaż nie otwierał registry.

Przechodzące 91 testów dotyczy wcześniejszej części projektu; nie obejmuje
generatora i walidatorów S7.2.

## Wymagany S7.2R

1. Uzgodnić schema v2 z zamrożonym kontraktem, zachowując zgodność outputu.
2. Przepisać generator tak, aby status wynikał wyłącznie z faktów, ról źródeł,
   reguły applicability oraz jawnych progów.
3. Utworzyć 36 prawdziwych par, w których zmienia się dokładnie jedna dozwolona
   przesłanka, a typ kontroli, rodzina i pozostałe fakty są stałe.
4. Zapisać source trust w danych runtime i w source packu bez utraty flag.
5. Dodać testy S7.2 dla całego kontraktu, macierzy, gold rubric i par.
6. Zaimplementować pełny similarity/leakage scan względem exclusion registry,
   z progami Jaccard, sequence match, numeric signature i kolejką manual review.
7. Wykonać rzeczywisty assisted review 390/390 z kompletnym rekordem per case.
8. Zbudować registry wiążące dane, specyfikację, rubric, polityki, raporty i
   szablon review.
9. Dopiero po ponownym Sol/high PASS przekazać pakiet człowiekowi/SME.

Regeneracja musi otrzymać nową wersję danych, np. `s7-train-dev-2.1.0`, aby nie
nadpisywać historii nieudanego pakietu. Nie wolno obniżać progów ani oznaczać
obecnych 390 goldów jako zaakceptowanych.

## Stan dalszych etapów

- human/SME review: `DO_NOT_START_UNTIL_REMEDIATED`;
- `S7_TRAIN_DEV_V2_FROZEN`: nieosiągnięte;
- S7.3: `BLOCKED`;
- Q2/S7.4: `PROHIBITED`;
- Evidence v2: `PROHIBITED`.

Maszynowy wynik review znajduje się w
`results/sprint7/s7_2_sol_high_review.json`.
