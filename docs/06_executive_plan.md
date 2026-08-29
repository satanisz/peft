# Executive plan — PEFT/LoRA/QLoRA dla kontroli finansowej

## 1. Cel projektu

Celem jest przygotowanie kompletnego, trzygodzinnego szkolenia technicznego o
Parameter-Efficient Fine-Tuning, opartego na działającym przypadku bankowym
`Financial Control Copilot`.

Szkolenie ma łączyć trzy perspektywy:

- **techniczną** — LoRA, QLoRA, dane, trening, pamięć GPU i inferencja,
- **eksperymentalną** — uczciwe baseline'y, benchmarki i analiza błędów,
- **biznesową** — zastosowania, ograniczenia i ryzyko wdrożenia w banku.

Projekt kończy się nie tylko prezentacją, ale powtarzalnym pakietem: danymi,
kodem, adapterem, wynikami, notebookami, slajdami i scenariuszem prowadzącego.

## 2. Stan początkowy

Na dzień 26 sierpnia 2026 gotowe są:

- specyfikacja szkolenia i głównego przypadku,
- fikcyjne sprawozdanie banku,
- 40 przypadków diagnostycznych dla 10 rodzajów kontroli,
- schemat odpowiedzi, walidator i metryki,
- baseline zero-shot i few-shot na modelu smoke 0.6B,
- działające środowisko z RTX 5070 Ti 12 GB i CUDA 12.8,
- testy automatyczne oraz instrukcja uruchomienia.

Sprinty 1 i 2 są ukończone, a `dataset-v1.0.0` i `baseline-v1.0.0` zamrożone.
Baseline 4B ujawnił słabe granice `WARN` i `NOT_APPLICABLE`, dlatego przed
QLoRA wprowadzamy Sprint 2.5. Największa część pozostałej pracy dotyczy
utwardzenia etykiet, QLoRA, pełnego benchmarku i materiałów dydaktycznych.

## 3. Oczekiwane rezultaty biznesowe

Po zakończeniu projektu:

1. uczestnicy potrafią ocenić, kiedy bank powinien użyć promptingu, RAG, PEFT
   albo kontroli deterministycznej,
2. prowadzący może wykonać rzeczywisty trening QLoRA i wyjaśnić jego mechanikę
   na poziomie zaawansowanym,
3. każda prezentowana przewaga adaptera jest poparta powtarzalnym pomiarem,
4. przypadek bankowy pokazuje wartość i granice LLM bez sugerowania autonomicznej
   decyzji kontrolnej,
5. demonstracja działa bez internetu i ma gotowy wariant awaryjny.

## 4. Model realizacji

Plan zakłada siedem etapów wykonawczych, w tym bramkowy Sprint 2.5. Czas podano
w dniach roboczych przy skoncentrowanej pracy nad projektem. Łączny horyzont to
około **4–6 tygodni**, czyli **20–26 dni roboczych**. Treningi mogą działać
poza czasem aktywnej pracy.

Każdy sprint kończy się bramką decyzyjną. Nie przechodzimy dalej wyłącznie na
podstawie spadającego lossu — wymagane są określone artefakty i pomiary.

## Sprint 1 — dane warsztatowe

**Czas:** 3–4 dni  
**Cel:** stworzyć wiarygodny i kontrolowany zbiór do SFT.

**Status:** ukończony 26 sierpnia 2026 — `dataset-v1.0.0`, M1 Data freeze.

### Zakres

- generator wariantów liczbowych, okresów, walut i jednostek,
- warianty językowe i parafrazy po polsku,
- zbalansowanie `PASS/WARN/FAIL/INSUFFICIENT_DATA/NOT_APPLICABLE`,
- trudne negatywy, brakujące dane i prompt injection,
- rozbudowa do 400–700 przykładów treningowych,
- grupowy podział train/validation/test/challenge,
- wykrywanie duplikatów i podobnych mutacji,
- karta danych i rejestr pochodzenia.

### Rezultaty

- dataset w formacie JSONL,
- raport rozkładu klas, typów kontroli i długości przykładów,
- walidator leakage i duplikatów,
- karta danych opisująca syntetyczność, ograniczenia i przeznaczenie.

### Kryteria odbioru

- 100% rekordów przechodzi walidację schematu,
- żadna rodzina mutacji nie występuje równocześnie w train i test,
- test i challenge pozostają zamrożone przed treningiem,
- rozkład etykiet nie tworzy oczywistego biasu do `PASS`,
- ręczny przegląd próbki nie wykazuje błędnych złotych odpowiedzi.

### Bramka M1 — Data freeze

Zamrażamy wersję `dataset-v1` i dopiero wtedy uruchamiamy docelowe baseline'y.

## Sprint 2 — docelowy baseline 4B

**Czas:** 2–3 dni  
**Cel:** ustalić punkt odniesienia przed fine-tuningiem.

**Status:** ukończony 26 sierpnia 2026 — `baseline-v1.0.0`, M2 Baseline freeze.

### Zakres

- uruchomienie przypiętej rewizji Qwen3-4B-Instruct,
- B0: zero-shot,
- B1: dopracowany prompt,
- B2: few-shot,
- test różnych długości kontekstu i trybu generacji,
- pomiar VRAM, tokenów, latencji i poprawności odpowiedzi,
- katalog typowych błędów modelu bazowego.

### Rezultaty

- zamrożony prompt bazowy,
- tabela B0/B1/B2,
- raport błędów jakościowych,
- oszacowanie czasu treningu na podstawie rzeczywistej tokenizacji.

### Kryteria odbioru

- ten sam model, dane i ustawienia dekodowania w każdym wariancie,
- osobne wyniki dla formatu, decyzji, dowodów i human review,
- brak strojenia promptu na splicie testowym,
- zapisane wersje modelu, bibliotek i sprzętu.

### Bramka M2 — Baseline freeze

Baseline i prompt stają się niezmiennym punktem odniesienia dla adapterów.

## Sprint 2.5 — Label Boundary Hardening

**Czas:** 2 dni

**Cel:** zdefiniować i zmierzyć granice między statusami przed treningiem.

**Status:** warunkowo zaakceptowany 26 sierpnia 2026 do celów warsztatowych;
Sprint 3 rozpoczynamy po 21:00. Przed wykorzystaniem poza warsztatem wymagany
jest niezależny sign-off ekspercki.

### Zakres

- polityka statusów i macierz stosowalności kontroli,
- trzy rodziny minimalnych par: `PASS/WARN`, `WARN/FAIL` oraz
  `NOT_APPLICABLE/INSUFFICIENT_DATA`,
- osobny `boundary-pack-v1.0.0` z 540 rekordami,
- B3: label-complete baseline z hierarchią decyzji,
- ręczny review 100% `NOT_APPLICABLE` i minimum 20% pozostałych danych,
- metryki granic, kosztów błędów i spójności par.

### Rezultaty

- zamrożona polityka pięciu statusów,
- boundary train/development/validation/test bez leakage,
- raport B1/B2/B3 na boundary validation,
- rekomendacja danych i metryk dla adaptera.

### Kryteria odbioru

- dokładnie 540 poprawnych rekordów i zadany rozkład klas,
- `NOT_APPLICABLE` występuje w co najmniej 4 typach kontroli, a `WARN` w 6,
- żadna rodzina par nie jest współdzielona między splitami,
- B3 ma zapisany prompt, demo IDs, hash i formalny wynik validation,
- boundary test, oryginalny test i challenge pozostają nieotwarte.

### Bramka M2.5 — Boundary freeze

Polityka statusów, dane graniczne i B3 stają się wersjonowanym kontraktem dla
adapterów. Szczegółowy zakres zawiera
[`09_sprint_2_5_executive_plan.md`](09_sprint_2_5_executive_plan.md).

**Decyzja właściciela:** warunkowa akceptacja do kontynuacji projektu. Polityka
i wagi kosztu pozostają artefaktami syntetycznymi do warsztatu; użycie dla
rzeczywistych danych bankowych wymaga review eksperckiego. Sprint 3 raportuje
osobno wyniki `WARN`, `NOT_APPLICABLE`, `INSUFFICIENT_DATA`, unsafe `PASS` i
nadzmierną eskalację. Boundary test, oryginalny test i challenge pozostają
nieotwarte do Sprintu 4.

## Sprint 3 — LoRA i QLoRA

**Czas:** 3–4 dni  
**Cel:** uzyskać pierwszy powtarzalny adapter i działającą demonstrację.

### Zakres

- instalacja i preflight PEFT, TRL, datasets i bitsandbytes,
- test kwantyzacji NF4 na GPU 12 GB,
- pipeline tokenizacji i chat template,
- LoRA BF16, jeśli pozwoli pamięć,
- Q0: QLoRA 4-bit trenowane tylko na `dataset-v1.0.0` jako kontrola wpływu
  nowych danych,
- Q1: QLoRA 4-bit trenowane na train v1 oraz boundary train jako główna
  konfiguracja,
- Q1b: sampling zorientowany na granice tylko wtedy, gdy Q1 nie spełnia bramki,
- checkpointing, logowanie lossu i pomiar VRAM,
- zapis, ładowanie, przełączanie i scalanie adaptera,
- krótki trening demonstracyjny oraz pełny trening referencyjny.

### Rezultaty

- konfiguracje treningowe w repozytorium,
- adapter kandydujący `qlora-v0.1`,
- log treningu i metryki techniczne,
- notebook lub skrypt treningowy end-to-end,
- adapter awaryjny do demonstracji.

### Kryteria odbioru

- trening można odtworzyć z jednej konfiguracji,
- proces mieści się w 12 GB VRAM bez niestabilnego offloadu,
- checkpoint można ponownie załadować i wykorzystać do inferencji,
- wersja pokazowa treningu mieści się w 10–15 minutach,
- nie oceniamy jakości na danych treningowych,
- wybór konfiguracji wykorzystuje oryginalny i boundary validation; oba testy
  pozostają zamknięte.

### Bramka M3 — Adapter candidate

Adapter przechodzi do pełnej oceny tylko wtedy, gdy działa technicznie i wobec
najlepszego z B1/B2/B3:

- poprawia boundary macro-F1 o co najmniej 0,05 albo pozostaje w granicy 0,02
  przy redukcji input tokens o co najmniej 30%,
- nie obniża recall `WARN`, a celem kierunkowym jest co najmniej 60%,
- osiąga recall `NOT_APPLICABLE` co najmniej 60% przy wsparciu 30 przypadków,
- utrzymuje FAIL FPR nie wyżej niż 15%,
- nie pogarsza recall `PASS` ani `FAIL` o więcej niż 5 punktów procentowych.

Jeżeli bramka nie zostanie spełniona, najpierw analizujemy politykę i dobór
danych. Nie rozpoczynamy szerokiego sweepu hiperparametrów w celu znalezienia
pojedynczego korzystnego wyniku.

### Wynik Sprintu 3 — 27 sierpnia 2026

Status: **ukończony, M3 PASS**. Q1 osiągnął boundary macro-F1 1,000 i 100%
poprawności minimalnych par przy redukcji średniego inputu o 51,6% względem B3.
Q0 potwierdził, że sam standardowy train nie uczy bezpiecznie granic etykiet:
boundary macro-F1 0,786 oraz WARN recall 66,7%. Model scalony BF16 został
zapisany i ponownie załadowany w kontrolowanym smoke teście.

Decyzja dotyczy adapter candidate do Sprintu 4. Testy i challenge pozostają
zamknięte, wynik pochodzi z jednego seeda i nie stanowi zgody produkcyjnej.
Szczegóły: [`12_sprint_3_report.md`](12_sprint_3_report.md).

## Sprint 4 — benchmark i eksperymenty zaawansowane

**Czas:** 3–5 dni, w tym około 8–10 godzin GPU
**Cel:** potwierdzić stabilność Q1 między seedami i zbudować zamknięty evidence
package bez strojenia na test.

**Status po review 28 sierpnia 2026:** replikacja trzech seedów ukończona;
protected evidence w stanie `CONDITIONAL_HOLD`. Przed otwarciem testów wymagany
jest Sprint 4.2A: diagnostic set poza szablonami, Q2/source integrity guard,
analiza severity i ponowna decyzja Sol/high.

Stan po Sprintach 4.2A–4.2C: 30 ręcznych przypadków przeszło niezależny review
i inferencję dla trzech seedów. Prompt v2 ustabilizował pola pochodne i source
integrity, lecz nie usunął stabilnego błędu liczbowego FC-209. Wersjonowany
deterministic decision guard blokuje ten błąd bez cichego poprawiania. Wynik ma
status `READY_FOR_SPRINT5_DEMO_WITH_PROTECTED_HOLD`; protected evidence pozostaje
zamknięte, ponieważ regułę dodano retrospektywnie po analizie diagnostic.

### Zakres

- wykorzystanie wyniku M3 jako pierwszego z trzech seedów Q1,
- trening wyłącznie dwóch brakujących seedów Q1,
- automatyczna bramka stabilności przed otwarciem testów,
- jednorazowe otwarcie original test, boundary test i challenge,
- Q2: QLoRA + kontrole deterministyczne,
- ręczny diagnostic set poza szablonami generatora,
- Q3 jako demonstracja do Sprintu 5, jeśli Q2 nie ujawni wcześniej luki,
- L1 BF16, rank i target modules jako opcjonalne ablations po evidence package,
- testy adversarial, regresyjne i braku danych,
- analiza false positives i false negatives,
- katalog najlepszych oraz najgorszych odpowiedzi.

### Rezultaty

- główna macierz B3/Q0/Q1-3seeds/Q2 oraz jawny backlog L1/Q1b/Q3,
- wykresy jakości, czasu, VRAM i rozmiaru adaptera,
- raport analizy błędów,
- rekomendacja architektury dla przypadku bankowego.

### Kryteria odbioru

- wyniki główne raportują średnią i rozrzut między seedami,
- severity i poprawność `source_id` są osobnymi kryteriami bramkowymi,
- false positive rate jest raportowany oddzielnie,
- `INSUFFICIENT_DATA` i przypadki wysokiego ryzyka mają osobne metryki,
- `WARN`, `NOT_APPLICABLE`, pair accuracy i koszty biznesowe mają osobne
  metryki,
- oryginalny test, boundary test i challenge są raportowane oddzielnie,
- nie ukrywamy regresji ani wariantów, które nie poprawiły jakości,
- wszystkie liczby na przyszłych slajdach prowadzą do zapisanego artefaktu.

### Bramka M4 — Evidence package

Zamrażamy wyniki, konfiguracje i przykłady używane w materiałach szkoleniowych.
M4 wymaga trzech seedów bez selekcji najlepszego, oddzielnych testów, ręcznego
review challenge i diagnostic setu poza szablonami. Szczegółowy, obowiązujący
plan: [`13_sprint_4_executive_plan.md`](13_sprint_4_executive_plan.md). Review
przed protected evidence: [`14_sprint_4_analytical_review.md`](14_sprint_4_analytical_review.md).

## Sprint 5 — materiały szkoleniowe

**Czas:** 4–5 dni  
**Cel:** zamienić eksperyment w profesjonalne szkolenie.

**Status 29 sierpnia 2026:** ukończona warstwa projektowa Sol/high: narracja
180 minut, 53 slajdy, notatki prowadzącego z blokami źródeł, trzy ćwiczenia i
scenariusz demonstracji z twardym limitem 15 minut. M5 pozostaje otwarta do
dry-runu Luna/low, sprawdzenia reloadu i domknięcia pozostałych materiałów
pomocniczych.

### Zakres

- 45–55 slajdów,
- notatki prowadzącego na poziomie zaawansowanym,
- notebooki: baseline, dane, LoRA, QLoRA, ewaluacja i adapter operations,
- diagramy LoRA, QLoRA i architektury bankowej,
- ściąga parametrów i troubleshooting,
- katalog zastosowań PEFT w banku,
- moduł o taksonomii etykiet, alert fatigue i data-centric fine-tuningu,
- pytania uczestników i sugerowane odpowiedzi,
- materiał po szkoleniu i ćwiczenia rozszerzające.

### Rezultaty

- komplet materiałów uczestnika,
- kompletny trainer guide,
- gotowa narracja demonstracji,
- wyniki i wykresy pochodzące z naszego benchmarku.

### Kryteria odbioru

- materiał odpowiada agendzie 180 minut,
- każda demonstracja ma rezultat oczekiwany i wariant awaryjny,
- rozdzielamy wyniki publikacji od wyników własnych,
- zastosowania biznesowe zawierają ograniczenia i wymagany nadzór człowieka,
- prowadzący ma odpowiedzi na pytania o pamięć, rank, kwantyzację i benchmark.

### Bramka M5 — Content freeze

Po tej bramce zmieniamy już tylko błędy, czas prezentacji i problemy techniczne.

## Sprint 6 — próba generalna i wydanie

**Czas:** 2–3 dni  
**Cel:** przygotować wersję możliwą do bezpiecznego przeprowadzenia.

### Zakres

- instalacja projektu od zera,
- pełna próba 180 minut,
- pomiar czasu każdego modułu,
- praca bez internetu,
- symulacja awarii treningu i braku modelu,
- próba demonstracji przypadku granicznego i ścieżki eskalacji alertu,
- sprawdzenie adaptera awaryjnego,
- końcowa korekta materiałów,
- utworzenie tagu wydania.

### Rezultaty

- pakiet `workshop-v1.0`,
- lista kontrolna prowadzącego,
- lokalna kopia modelu, danych, adaptera i wyników,
- potwierdzony plan czasowy.

### Kryteria odbioru

- pełna próba mieści się w 180 minutach z tolerancją 5 minut,
- wszystkie testy i notebooki przechodzą na czystym środowisku,
- szkolenie można przeprowadzić bez dostępu do sieci,
- awaria treningu nie blokuje benchmarku ani dalszej narracji,
- wszystkie prezentowane artefakty mają wersję i sumę kontrolną.

### Bramka M6 — Workshop ready

Projekt otrzymuje tag `workshop-v1.0` i jest gotowy do użycia.

## 5. Harmonogram wykonawczy

| Sprint | Czas | Kamień milowy | Udział programu |
|---|---:|---|---:|
| 1. Dane | 3–4 dni | M1 Data freeze | 15% |
| 2. Baseline 4B | 2–3 dni | M2 Baseline freeze | 10% |
| 2.5. Granice etykiet | 2 dni | M2.5 Boundary freeze | 10% |
| 3. LoRA/QLoRA | 3–4 dni | M3 Adapter candidate | 20% |
| 4. Benchmark | 4–5 dni | M4 Evidence package | 20% |
| 5. Materiały | 4–5 dni | M5 Content freeze | 15% |
| 6. Próba i wydanie | 2–3 dni | M6 Workshop ready | 10% |

Szacunek zakłada około 10–18 godzin wykorzystania GPU dla treningów głównych i
eksperymentów. Szeroki sweep oraz metody opcjonalne pozostają poza ścieżką
krytyczną.

## 6. Kluczowe wskaźniki projektu

### Jakość rozwiązania

- schema validity co najmniej 98% dla kandydata,
- poprawa boundary macro-F1 o co najmniej 0,05 względem najlepszego z B1/B2/B3
  albo wynik w granicy 0,02 przy redukcji input tokens o co najmniej 30%,
- recall `WARN` bez regresji względem najlepszego baseline'u i cel co najmniej
  60%,
- recall `NOT_APPLICABLE` co najmniej 60% przy wsparciu 30 przypadków,
- raportowany false positive rate,
- osobny wynik dla `WARN`, `NOT_APPLICABLE`, `INSUFFICIENT_DATA` i par,
- brak nieistniejących `source_id` w zaakceptowanej konfiguracji,
- odporność na przygotowany zestaw prompt injection.

Progi jakości zostaną potwierdzone po baseline 4B. Nie traktujemy ich jako
obietnicy wyniku, lecz jako kryteria pozwalające zdecydować, czy adapter nadaje
się do demonstracji.

### Gotowość szkoleniowa

- 180 minut potwierdzone podczas próby,
- trening pokazowy maksymalnie 15 minut,
- 100% demonstracji ma wariant awaryjny,
- komplet slajdów, notebooków i notatek prowadzącego,
- uruchomienie na czystym środowisku bez ręcznych poprawek.

## 7. Ryzyka i działania ograniczające

| Ryzyko | Wpływ | Ograniczenie |
|---|---|---|
| Syntetyczne dane są zbyt proste | wysoki | trudne negatywy, ręczny review, test kombinacji błędów |
| Leakage między train i test | wysoki | grupowy split, identyfikatory rodzin, kontrola podobieństwa |
| QLoRA nie mieści się w 12 GB | wysoki | krótsze sekwencje, batch 1, checkpointing, NF4 |
| Adapter uczy biasu do FAIL lub PASS | wysoki | boundary pack, koszt błędu i macierz pomyłek |
| N/A jest skrótem dla typu DISCLOSURE | wysoki | przypadki N/A w co najmniej 4 typach kontroli |
| WARN pozostaje klasą resztkową | wysoki | zamknięta polityka, reason codes i minimalne pary |
| Benchmark diagnostyczny zniekształca priory produkcyjne | średni | osobne raportowanie i jawne ograniczenie |
| Dobry JSON maskuje złą decyzję | wysoki | osobne metryki struktury i treści |
| Training demo trwa zbyt długo | średni | krótki dataset demonstracyjny i gotowy adapter |
| Brak internetu na sali | wysoki | lokalny cache wszystkich artefaktów |
| Zmiana bibliotek lub modelu | średni | lockfile, przypięte rewizje i tag wydania |
| Rozrost zakresu metod PEFT | średni | LoRA/QLoRA jako rdzeń; DoRA/IA3 tylko rozszerzenie |
| Błędna interpretacja biznesowa | wysoki | human-in-the-loop i wyraźne granice systemu |

## 8. Zarządzanie zakresem

### Must have

- dataset i jego dokumentacja,
- baseline 4B oraz label-complete B3,
- polityka statusów i boundary pack,
- działający QLoRA,
- benchmark B0/B1/B2/B3/Q0/Q1/Q2,
- notebook demonstracyjny,
- slajdy i trainer guide,
- próba generalna oraz adapter awaryjny.

### Should have

- LoRA BF16,
- Q3 z kontekstem procedury,
- trzy seedy,
- testy adversarial i regresyjne,
- analiza ranku `8/16`, modułów docelowych oraz wpływu boundary data.

### Could have

- DoRA, rsLoRA i szeroki sweep ranków,
- większy dataset 1500–3000 przykładów,
- dashboard wyników,
- porównanie drugiej rodziny modeli,
- automatyczna ocena odpowiedzi przez dodatkowy model.

Elementy `Could have` nie mogą zagrozić terminowi wersji `workshop-v1.0`.

## 9. Strategia Git

- `main` zawsze zawiera wersję działającą i możliwą do odtworzenia,
- praca odbywa się na krótkich gałęziach `feature/...`, `experiment/...` i
  `docs/...`,
- małe wyniki JSON, konfiguracje i syntetyczne dane są wersjonowane,
- modele, checkpointy, adaptery i sekrety nie trafiają do zwykłego Git,
- ciężkie artefakty będą przechowywane jako release assets albo przez Git LFS,
- proponowane tagi: `dataset-v1.0.0`, `baseline-v1.0.0`,
  `boundary-pack-v1.0.0`, `baseline-v1.1.0`, `adapter-v0.1`,
  `content-freeze-v1`, `workshop-v1.0`,
- komunikaty commitów używają formy `feat:`, `fix:`, `docs:`, `test:`,
  `experiment:` i `chore:`.

## 10. Następna decyzja wykonawcza

Rozpoczynamy Sprint 2.5 od zatwierdzenia polityki statusów i wzorcowych par.
Sprint 3 może rozpocząć się dopiero po M2.5 Boundary freeze. Główny kandydat
QLoRA będzie następnie oceniany względem B1, B2 i B3 na dwóch osobno
raportowanych zbiorach validation.
