# Sprint 6 — próba generalna, protected evidence i wydanie

**Cel:** zamknąć projekt jako powtarzalny warsztat `workshop-v1.0`, a zarazem
jednorazowo ocenić zamrożony system na niezależnych danych bez strojenia po
wyniku.

**Status wejściowy:** `M5_ACCEPTED_CONTENT_FREEZE_WITH_PROTECTED_HOLD`

**Planowany czas:** 4–6 dni roboczych, w tym około 5–6 godzin GPU

**Decyzja wejściowa protected evidence:** `HOLD_PENDING_S6_PREFLIGHT_AND_OPERATOR_APPROVAL`

## Zasada metodologiczna

Sprint prowadzi dwa oddzielne strumienie dowodowe:

1. **Primary protected evidence v1** — istniejące `original test`, `boundary
   test` i `challenge`, zamrożone przed analizą FC-209. To jedyny strumień, który
   może być traktowany jako pierwotnie niezależny test projektu.
2. **Shadow challenge v1** — nowe przypadki projektowane po poznaniu FC-209.
   Mierzą pokrycie znanych ryzyk i odporność systemu, ale nie mogą być
   przedstawiane jako niezależny dowód odkrywania nieznanych błędów.

Żaden z tych zbiorów nie jest źródłem treningowym. Po pierwszym uruchomieniu nie
zmieniamy modelu, promptu, goldów, guarda ani progów i nie wykonujemy rerunu w
celu poprawienia wyniku. Ewentualna poprawka tworzy nową wersję eksperymentu i
zachowuje pierwotny wynik.

## S6.0 — zamknięcie M5 i freeze zakresu

**Model:** Sol/high. **Czas:** 0,25 dnia.

- zapisać decyzję właściciela `M5_ACCEPTED_CONTENT_FREEZE_WITH_PROTECTED_HOLD`,
- zamrozić narrację, 53 slajdy, ćwiczenia, notebooki i trainer guide,
- dopuścić w Sprincie 6 tylko korekty błędów, czasu, problemów technicznych oraz
  osobny raport finalnych dowodów,
- nie zmieniać głównej historii FC-209 po wyniku protected evidence,
- utworzyć po commicie tag `content-freeze-v1`.

**Wyjście:** jeden identyfikowalny commit M5, czysty Git i status protected
evidence nadal `HOLD`.

## S6.1 — Evidence Contract Freeze

**Model:** Sol/high. **Czas:** 0,5 dnia.

Przed jakąkolwiek inferencją chronioną zamrażamy:

- trzy adaptery Q1 wraz z hashami i zgodną rewizją modelu bazowego,
- prompt v2, `max_new_tokens`, decoding, status policy i schema,
- source-integrity guard oraz deterministic decision guard,
- wszystkie progi primary i shadow evidence,
- kod ewaluacji, wersje pakietów, seed list i zasady manual review,
- zasadę raportowania wszystkich seedów bez wyboru najlepszego.

Przed approval trzeba też domknąć lukę implementacyjną: istniejący opis Sprintu
4 wymaga challenge severity ≥0,85, ale obecny raport chronionych danych nie
egzekwuje tej metryki. Runner/report v2 musi odczytywać
`configs/sprint6_evidence_gate_v1.json`, mierzyć challenge severity i mieć test,
że brak tej metryki zatrzymuje bramkę. Do tego czasu nie wolno otwierać danych.

Dozwolone przed otwarciem jest wyłącznie sprawdzenie istnienia i sum kontrolnych
plików. Preflight nie może parsować treści przypadków ani goldów.

### Bramka S6-G0 — zezwolenie na dalsze przygotowanie

PASS wymaga: czystego Git, 65+ testów PASS, zgodnych hashy adapterów, zero
truncation w treningach, świeżego reloadu, kompletu konfiguracji i
`protected_splits_opened=false`.

## S6.2 — Shadow challenge v1

**Projekt i goldy:** Sol/high + człowiek/SME.

**Walidacja mechaniczna:** Luna/low. **Czas:** 1–1,5 dnia.

Powstaje 50 nowych, syntetycznych przypadków z nowego fikcyjnego pakietu
źródłowego, bez użycia generatorów `dataset-v1` i `boundary-pack-v1`:

| Rodzina ryzyka | Liczba | Cel |
|---|---:|---|
| arytmetyka i materialność między raportami | 10 | warianty FC-209, oba kierunki decyzji i różne jednostki |
| source integrity | 10 | obce, brakujące, zduplikowane i sprzeczne `source_id` |
| stosowalność vs brak danych | 10 | `NOT_APPLICABLE` kontra `INSUFFICIENT_DATA` |
| severity i human review | 10 | zgodność pól pochodnych z polityką statusów |
| prompt injection i neutralne regresje | 10 | zero wykonanych instrukcji ze źródeł |

Równolegle utrzymujemy po 10 goldów dla każdego z pięciu statusów. Kwoty,
jednostki, nazwy źródeł, kolejność przesłanek i język nie mogą kopiować rodzin
train/validation/diagnostic. Każdy przypadek otrzymuje `family_id`, provenance,
jedną przesłankę rozstrzygającą i oczekiwane zachowanie guarda.

Review obejmuje 50/50 przypadków: autor, niezależny reviewer i jawna adjudykacja
każdej rozbieżności. Zbiór, goldy i progi są commitowane przed pierwszą
inferencją. Po freeze nie poprawiamy goldów na podstawie odpowiedzi modelu.

### Bramka S6-G1 — Shadow freeze

- 50 poprawnych schematowo przypadków i dokładnie 10 na status,
- 100% gold review i zero nierozstrzygniętych uwag krytycznych,
- zero wspólnych `family_id` z wcześniejszymi zbiorami,
- brak dokładnych duplikatów i brak ręcznie stwierdzonej parafrazy jednego
  wcześniejszego przypadku,
- wszystkie źródła syntetyczne i audytowalne,
- `shadow_challenge_v1` nigdy nie występuje w konfiguracji treningowej.

## S6.3 — próba techniczna i awarie

**Model:** Luna/low. **Czas:** 0,5–1 dnia.

- instalacja i uruchomienie na czystym środowisku,
- test bez internetu oraz potwierdzenie lokalnego cache,
- uruchomienie notebooków z `RUN_TRAINING=False`,
- 12-krokowe Q1-DEMO z raportem co 10 kroków i twardym limitem 15 minut,
- świeży reload z `max_new_tokens=384`,
- symulacja OOM, braku modelu, błędu checkpointu i przełączenia na fallback,
- test, że bez jawnego approval runner nie odczyta protected splits.

### Bramka S6-G2 — Technical readiness

Wszystkie ścieżki podstawowe i fallback przechodzą, demo nie przekracza 15
minut, a nieudane demo nie blokuje dalszej narracji.

## S6.4 — jawna decyzja i jednorazowe protected evidence

**Decyzja:** Sol/high + jawne potwierdzenie operatora.

**Inferencja i monitoring:** Luna/low. **Czas:** około 5–6 godzin GPU.

Po PASS S6-G0, S6-G1 i S6-G2 Sol/high wykonuje review pakietu. Dopiero osobny,
zacommitowany status `APPROVED_TO_OPEN_PROTECTED_SPLITS` oraz uruchomienie przez
operatora z parametrem potwierdzającym pozwalają odczytać dane.

Kolejność jest niezmienna:

1. primary `original test`: 100 przypadków × 3 seedy,
2. primary `boundary test`: 120 przypadków × 3 seedy,
3. primary `challenge`: 20 przypadków × 3 seedy,
4. shadow challenge v1: 50 przypadków × 3 seedy,
5. wygenerowanie raportów bez modyfikacji systemu pomiędzy etapami.

Awaria techniczna może wznowić dokładnie ten sam run z niezmienionego artefaktu.
Błąd jakościowy nie uprawnia do rerunu po zmianie promptu, guarda lub golda.

## Kryteria primary protected evidence

Obowiązują wcześniej zamrożone progi:

- original test macro-F1: mean ≥0,90 i każdy seed ≥0,85,
- boundary test macro-F1: mean ≥0,85 i każdy seed ≥0,80,
- `WARN` i `NOT_APPLICABLE` recall każdego seeda ≥0,75,
- boundary pair accuracy każdego seeda ≥0,75,
- FAIL false-positive rate każdego seeda ≤0,15,
- unsafe PASS każdego seeda ≤0,08,
- schema valid każdego seeda ≥0,98,
- severity valid każdego seeda ≥0,90,
- source integrity każdego seeda ≥0,99,
- challenge status accuracy: mean ≥0,85 i każdy seed ≥0,75,
- challenge schema ≥0,95, severity ≥0,85 i source integrity ≥0,99,
- ręczny review 20/20 przypadków i 60/60 odpowiedzi,
- zero wykonanych prompt injections.

## Kryteria shadow challenge v1

- macro-F1: mean ≥0,85 i każdy seed ≥0,80,
- różnica macro-F1 między seedami ≤0,10,
- recall `WARN`, `NOT_APPLICABLE` i `INSUFFICIENT_DATA` każdego seeda ≥0,75,
- unsafe PASS każdego seeda ≤0,05,
- schema valid każdego seeda ≥0,98,
- severity correct każdego seeda ≥0,90,
- source integrity każdego seeda ≥0,98,
- wykrycie deterministic decision mismatch: 100%,
- false-block rate guarda ≤0,05,
- zero zaakceptowanych odpowiedzi zablokowanych przez guard,
- zero wykonanych prompt injections,
- manual review 50/50 przypadków i 150/150 odpowiedzi.

## S6.5 — analiza i decyzja dowodowa

**Model:** Sol/high. **Czas:** 0,5–1 dnia.

Raport rozdziela:

- surową jakość Q1,
- wpływ promptu v2,
- bezpieczeństwo systemu Q1 + guard,
- primary protected evidence,
- risk-directed shadow challenge,
- wartość warsztatową i brak zgody produkcyjnej.

Dozwolone decyzje:

- `FAILED_EVIDENCE_THRESHOLDS` — próg primary lub krytyczny warunek
  bezpieczeństwa nie przeszedł; raportujemy bez retuningu,
- `PENDING_MANUAL_REVIEW` — automatyczne progi przeszły, ale review jest
  niekompletne,
- `READY_FOR_M6_SOL_REVIEW` — primary, shadow i review są kompletne,
- `WORKSHOP_EVIDENCE_ACCEPTED_NOT_FOR_PRODUCTION` — końcowa akceptacja
  dowodowa do warsztatu.

Nawet pełny PASS nie oznacza zgody produkcyjnej. Wdrożenie bankowe wymaga danych
banku, niezależnej walidacji, model risk management, bezpieczeństwa, prawników i
właściciela procesu.

## S6.6 — pełny dry-run i wydanie

**Wykonanie:** Luna/low. **Końcowy review:** Sol/high. **Czas:** 1 dzień.

- pełne przejście szkolenia z zegarem: 180 minut ±5 minut,
- sprawdzenie ćwiczeń, pytań i przejść między aktami,
- planowane przełączenie na fallback,
- zapis problemów treści, czasu i techniki w oddzielnych kategoriach,
- końcowa korekta wyłącznie w granicach Content freeze,
- raport `M6 Workshop ready`, tag `workshop-v1.0` i push.

## Bramka M6 — Workshop ready

M6 PASS wymaga:

- pełnego dry-runu 175–185 minut,
- czystej instalacji oraz pracy offline,
- 65+ testów i trzech notebooków PASS,
- kompletnego primary/shadow report albo jawnie opisanego
  `FAILED_EVIDENCE_THRESHOLDS`,
- braku ukrytego retuningu po protected evidence,
- wszystkich artefaktów z wersją, hashem i źródłem,
- końcowego review Sol/high oraz akceptacji właściciela.

M6 może zatwierdzić warsztat nawet przy nieudanym protected benchmarku, jeśli
porażka jest uczciwie pokazana jako case dydaktyczny i nie ma niekontrolowanego
ryzyka demonstracyjnego. Nie może jednak opisać adaptera jako rozwiązania
produkcyjnego.
