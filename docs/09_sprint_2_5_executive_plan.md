# Executive plan Sprintu 2.5 — Label Boundary Hardening

## 1. Decyzja wykonawcza

Przed treningiem LoRA/QLoRA wprowadzamy dwudniowy Sprint 2.5. Jego celem jest
usunięcie niejednoznaczności między `PASS`, `WARN`, `FAIL`,
`INSUFFICIENT_DATA` i `NOT_APPLICABLE` oraz zbudowanie osobnego, audytowalnego
pakietu przypadków granicznych.

Nie zmieniamy zamrożonych artefaktów `dataset-v1.0.0` ani
`baseline-v1.0.0`. Nowe dane będą wersjonowanym rozszerzeniem, dzięki czemu
wyniki Sprintu 2 pozostaną odtwarzalne, a wpływ nowych danych będzie można
zmierzyć osobno.

## 2. Uzasadnienie biznesowe i eksperymentalne

Obecny baseline rozwiązał problem formatu, ale nie problem decyzji:

- B2 osiąga 100% zgodności ze schematem, lecz tylko 72% status accuracy i
  macro-F1 0,529,
- recall `WARN` wynosi 28,6% (2 z 7 przypadków validation),
- `NOT_APPLICABLE` nie został rozpoznany ani razu; obecne wsparcie validation
  wynosi tylko 1 przypadek,
- wszystkie 8 przykładów `NOT_APPLICABLE` w train dotyczy kontroli
  `DISCLOSURE`, więc model może uczyć się skrótu „typ kontroli → status”,
- demonstracje B2 dla analizowanych przypadków nie pokrywają etykiet `WARN`
  ani `NOT_APPLICABLE`, dlatego B2 nie jest jeszcze label-complete few-shot
  baseline'em,
- błędy `WARN` są rozproszone m.in. między `CURRENCY`, `DIRECTION`,
  `DISCLOSURE`, `EVIDENCE`, `INSUFFICIENT_DATA`, `UNIT` i `VARIANCE`.

Bez tej korekty trening QLoRA mógłby poprawić średnią metrykę przez utrwalenie
błędnej polityki etykiet. W banku skutkiem byłaby nadmierna eskalacja do
`FAIL`, koszt ręcznej obsługi alertów albo błędne uznanie kontroli za
nieobowiązującą.

## 3. Cel, rezultat i zakres

### Cel

Zamrozić jednoznaczną politykę statusów i zbudować zbiór, który pozwala
odróżnić trzy najważniejsze granice decyzyjne:

1. `PASS` ↔ `WARN`,
2. `WARN` ↔ `FAIL`,
3. `NOT_APPLICABLE` ↔ `INSUFFICIENT_DATA`.

### Rezultat

Po Sprincie 2.5 projekt ma posiadać:

- politykę etykiet z regułami rozstrzygania konfliktów,
- macierz stosowalności kontroli,
- wersjonowany `boundary-pack-v1.0.0`,
- label-complete baseline B3,
- metryki granic decyzyjnych i kosztów błędów,
- decyzję, czy można przejść do treningu adaptera.

### Poza zakresem

- modyfikowanie lub zastępowanie `dataset-v1.0.0`,
- trening adaptera,
- użycie zamrożonego `test` albo `challenge` do strojenia,
- deklarowanie gotowości produkcyjnej,
- odwzorowanie pełnej polityki konkretnego banku bez udziału właściciela
  procesu i compliance.

## 4. Polityka statusów

Status jest wybierany w podanej kolejności. Pierwsza spełniona reguła kończy
klasyfikację:

1. **`NOT_APPLICABLE`** — kontrola nie dotyczy obiektu, okresu lub zdarzenia;
   brak danych nie jest powodem tej decyzji.
2. **`INSUFFICIENT_DATA`** — kontrola ma zastosowanie, lecz brakuje materiału
   niezbędnego do wydania osądu albo źródła są nierozstrzygalnie sprzeczne.
3. **`FAIL`** — istnieje potwierdzone, istotne naruszenie reguły kontrolnej.
4. **`WARN`** — kontrola ma zastosowanie, a przypadek wymaga uwagi lub
   wyjaśnienia, lecz dowody nie uzasadniają `FAIL`; obejmuje m.in. częściową
   niezgodność, nieistotne odchylenie, niejednoznaczność i słabe dowody.
5. **`PASS`** — wymaganie jest spełnione, a materiał jest wystarczający.

Reguły wiążące:

- brak dowodu nie jest dowodem naruszenia,
- „nie dotyczy” opisuje zakres kontroli, nie jakość dostarczonych danych,
- `WARN` nie może być używany jako dowolna klasa „niepewna”,
- istotność, próg i wymagane źródła muszą być jawne w przypadku,
- każda etykieta musi mieć krótkie uzasadnienie oraz oczekiwane
  `human_review_required`.

Ta polityka jest dydaktycznym kontraktem projektu. Przed użyciem w realnym
banku wymaga mapowania do polityk organizacji i zatwierdzenia przez właścicieli
kontroli.

## 5. Projekt pakietu danych

### Wielkość i skład

`boundary-pack-v1.0.0` będzie zawierał 540 syntetycznych przypadków w 270
minimalnych parach. W parze zmienia się jedna przesłanka decyzyjna, a pozostały
kontekst pozostaje możliwie stały.

| Split | Pary PASS/WARN | Pary WARN/FAIL | Pary N/A/INSUFFICIENT | Rekordy |
|---|---:|---:|---:|---:|
| train | 40 | 40 | 40 | 240 |
| development | 10 | 10 | 10 | 60 |
| validation | 15 | 15 | 30 | 120 |
| test | 15 | 15 | 30 | 120 |
| **Razem** | **80** | **80** | **110** | **540** |

Docelowe wsparcie statusów:

| Split | PASS | WARN | FAIL | INSUFFICIENT_DATA | NOT_APPLICABLE |
|---|---:|---:|---:|---:|---:|
| train | 40 | 80 | 40 | 40 | 40 |
| development | 10 | 20 | 10 | 10 | 10 |
| validation | 15 | 30 | 15 | 30 | 30 |
| test | 15 | 30 | 15 | 30 | 30 |

### Reguły konstrukcji

- rodzina pary trafia tylko do jednego splitu,
- split jest wykonywany grupowo przed generowaniem wariantów tekstowych,
- `NOT_APPLICABLE` obejmuje co najmniej 4 typy kontroli dopuszczone przez
  macierz stosowalności,
- `WARN` obejmuje co najmniej 6 typów kontroli,
- warianty różnią się nazwami, liczbami i sformułowaniami, ale nie mogą ujawniać
  etykiety w tekście,
- identyfikatory źródeł muszą istnieć, a wartości liczbowe muszą być zgodne z
  oczekiwanym wynikiem kontroli,
- dane pozostają w pełni syntetyczne, bez PII i tajemnicy bankowej,
- `test` zostaje zamrożony przed uruchomieniem B3 i treningiem adapterów.

Rozkład celowo nie odzwierciedla częstości produkcyjnych. Jest to benchmark
diagnostyczny do nauki granic; wyniki operacyjne wymagają osobnego testu na
realistycznych priorytetach klas.

## 6. Baseline B3 — status-aware, label-complete

B3 zachowuje model, rewizję, dekodowanie i schemat odpowiedzi z B1/B2. Zmienia
wyłącznie prompt:

- zawiera skróconą hierarchię decyzji statusowej,
- zawiera po jednym stałym przykładzie dla każdego z pięciu statusów,
- przykłady są wybierane wyłącznie z train i mają zapisane identyfikatory,
- przykład z tej samej rodziny co oceniany przypadek jest niedozwolony,
- zapisywany jest hash promptu i pełna lista demonstracji,
- prompt jest strojony tylko na `development`, następnie zamrażany,
- po zamrożeniu wykonywana jest jedna formalna ocena na `validation`;
  `test` pozostaje nieotwarty.

Przed pełnym przebiegiem wykonujemy smoke test. Warunki techniczne to brak
obcięcia wejścia i peak VRAM poniżej 11,5 GiB. Jeśli pięć demonstracji nie
spełni limitu, ustalony wariant awaryjny używa tabeli decyzji i trzech krótkich
przykładów: `WARN`, `NOT_APPLICABLE` oraz `INSUFFICIENT_DATA`. Zmiana musi być
podjęta na `development` i opisana w raporcie.

B3 nie ma z góry narzuconego progu jakości. Jego rolą jest stworzenie
najsilniejszego uczciwego baseline'u promptowego; negatywny wynik jest ważnym
rezultatem, o ile protokół został zachowany.

## 7. Metryki i koszt błędu

### Metryki główne

- macro-F1 oraz precision, recall, F1 i support dla każdego statusu,
- accuracy i macro-F1 na samym boundary pack,
- pair accuracy: odsetek par, w których oba rekordy są poprawne,
- flip consistency: odsetek par, w których minimalna zmiana powoduje właściwą
  zmianę statusu,
- recall `WARN`,
- recall `NOT_APPLICABLE`,
- macierz pomyłek `NOT_APPLICABLE` ↔ `INSUFFICIENT_DATA`,
- FAIL false positive rate i false negative rate,
- schema validity oraz poprawność `source_id`.

### Metryki biznesowe

- **unsafe PASS rate** — oczekiwany `WARN`, `FAIL` lub `INSUFFICIENT_DATA`, lecz
  model zwraca `PASS`,
- **unnecessary escalation rate** — oczekiwany `WARN`, `NOT_APPLICABLE` albo
  `INSUFFICIENT_DATA`, lecz model zwraca `FAIL`,
- poprawność `human_review_required`,
- koszt ważony według macierzy: przeoczenie naruszenia, fałszywy alarm,
  niepotrzebna analiza i błędne wyłączenie kontroli.

Macierz kosztu nie będzie udawała danych finansowych konkretnego banku. Do
szkolenia użyjemy jawnych wag porządkowych, a podczas wykładu pokażemy, jak
zastąpić je rzeczywistymi kosztami procesu.

## 8. Plan wykonania — 2 dni robocze

### Dzień 1 rano — kontrakt decyzyjny

- zapisać politykę statusów i reguły rozstrzygania,
- przygotować macierz: typ kontroli × warunek stosowalności × wymagane źródła ×
  próg istotności,
- zdefiniować minimalne pary i taksonomię przyczyn błędów,
- przypisać wagi kosztów biznesowych,
- ręcznie zatwierdzić wzorcowe przypadki dla każdej granicy.

**Punkt kontroli A:** żaden generator ani prompt nie powstaje przed
zatwierdzeniem polityki i wzorców.

### Dzień 1 po południu — pilot danych i B3

- zaimplementować generator i walidatory par,
- utworzyć pilotażową próbkę każdej granicy,
- sprawdzić leakage, duplikaty, źródła, liczby i brak skrótów leksykalnych,
- zbudować B3 i przeprowadzić smoke test na `development`,
- zamrozić wariant promptu, identyfikatory demonstracji i hash.

**Punkt kontroli B:** pilot musi pokazać, że zmiana jednej przesłanki prowadzi
do jednoznacznej zmiany złotej etykiety.

### Dzień 2 rano — pełny boundary pack i review

- wygenerować 540 rekordów i wykonać grupowy split,
- ręcznie przejrzeć 100% przypadków `NOT_APPLICABLE`,
- ręcznie przejrzeć minimum 20% pozostałych przypadków, warstwowo według
  statusu, granicy i typu kontroli,
- naprawić błędy w generatorze, następnie wygenerować cały pakiet od nowa,
- uruchomić kompletną walidację i zamrozić `test`.

**Punkt kontroli C:** poprawki ręczne nie mogą być ukrytymi wyjątkami w
gotowym JSONL; muszą prowadzić do korekty reguły lub szablonu źródłowego.

### Dzień 2 po południu — formalny baseline i freeze

- wykonać B3 na `development`, potwierdzić zamrożenie promptu,
- wykonać pojedynczą formalną ocenę B1/B2/B3 na boundary `validation`,
- zestawić wynik z oryginalnym `validation`, bez łączenia obu populacji w jedną
  nieopisaną średnią,
- opisać błędy, koszty biznesowe i zalecenie dla Sprintu 3,
- zapisać sumy kontrolne, rejestr danych i tag wydania.

## 9. Artefakty

Planowane ścieżki:

- `configs/status_policy_v1.json` — polityka etykiet i macierz kosztu,
- `configs/baseline_b3_v1.json` — zamrożona konfiguracja B3,
- `src/peft_workshop/boundary_dataset.py` — generator par,
- `data/generated/boundary_pack_v1.jsonl` — pełny pakiet,
- `data/splits/boundary_{train,development,validation,test}.jsonl` — splity,
- `data/BOUNDARY_DATASET_CARD.md` — przeznaczenie, rozkład i ograniczenia,
- `data/boundary_registry.json` — wersje, hashe i lineage,
- `results/b3_boundary_validation*` — odpowiedzi i metryki,
- `results/sprint2_5_boundary_audit.json` — review i walidacja,
- `docs/10_sprint_2_5_report.md` — decyzja końcowa i wnioski.

## 10. Bramka M2.5 — Boundary freeze

Sprint zostaje odebrany wyłącznie, gdy:

- polityka pięciu statusów i macierz stosowalności są zatwierdzone,
- powstało dokładnie 540 poprawnych rekordów o zadanym rozkładzie,
- nie ma rodzin współdzielonych między splitami ani wykrytych duplikatów,
- 100% `NOT_APPLICABLE` i minimum 20% pozostałych danych przeszło review,
- review nie wykazuje krytycznego błędu złotej etykiety w zaakceptowanej wersji,
- B3 przeszedł smoke test oraz formalną ocenę na `validation`,
- wszystkie konfiguracje, identyfikatory demonstracji, hashe i wyniki są
  zapisane,
- boundary `test`, oryginalny `test` i `challenge` pozostają nieotwarte.

Po spełnieniu kryteriów tworzymy tag `boundary-pack-v1.0.0`. Jeśli polityka
statusów pozostaje niejednoznaczna lub review wykrywa systemowy błąd, Sprint 3
nie rozpoczyna się; najpierw poprawiamy kontrakt i regenerujemy pakiet.

## 11. Odpowiedzialność i decyzje

- **Prowadzący / właściciel projektu:** zatwierdza politykę statusów, wzorcowe
  przypadki, wagi biznesowe i decyzję M2.5.
- **Implementacja:** generator, walidatory, B3, raporty i odtwarzalność.
- **Przyszły właściciel procesu bankowego:** przed zastosowaniem organizacyjnym
  mapuje statusy, progi i koszty na polityki banku.

Brak zewnętrznego SME nie blokuje materiału warsztatowego, ale musi być jawnie
opisany jako ograniczenie, a nie zastąpiony pozorną autoryzacją domenową.

## 12. Ryzyka i działania ograniczające

| Ryzyko | Wpływ | Ograniczenie |
|---|---|---|
| `WARN` pozostaje klasą resztkową | wysoki | zamknięta definicja, minimalne pary i reason codes |
| Model uczy się typu kontroli zamiast przesłanki | wysoki | N/A w ≥4, WARN w ≥6 typach i test par |
| Oversampling zniekształca realne priory | średni | osobne raportowanie benchmarku diagnostycznego |
| Leakage między parami | wysoki | group split i kontrola podobieństwa |
| Ręczny review jest niespójny | wysoki | rubryka, zapis decyzji i ponowna generacja |
| B3 przekracza pamięć lub kontekst | średni | smoke test i z góry ustalony wariant kompaktowy |
| Sprint rozszerza się w pełny redesign danych | średni | limit 540 rekordów i zamknięte trzy granice |

## 13. Wpływ na dalszy program

Sprint 2.5 dodaje **2 dni robocze**. Nowy łączny szacunek projektu to
**20–26 dni roboczych**, czyli około **4–6 tygodni**. Aby ograniczyć wzrost
zakresu, DoRA, rsLoRA, drugi model bazowy i szeroki sweep ranków przechodzą do
backlogu. Priorytetem pozostają QLoRA oraz ablation danych granicznych.

Sprint 3 rozpocznie się dopiero po M2.5. Adapter będzie porównywany z B1, B2 i
B3 zarówno na oryginalnym validation, jak i boundary validation. Sprint 4
otworzy oba zamrożone testy dopiero po wyborze konfiguracji.
