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

Stan realizacji całego programu szacujemy na około 25%. Największa część
pozostałej pracy dotyczy danych treningowych, QLoRA, pełnego benchmarku i
materiałów dydaktycznych.

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

Plan zakłada sześć kolejnych sprintów. Czas podano w dniach roboczych przy
skoncentrowanej pracy nad projektem. Łączny horyzont to około **4–5 tygodni**,
czyli **18–24 dni robocze**. Treningi mogą działać poza czasem aktywnej pracy.

Każdy sprint kończy się bramką decyzyjną. Nie przechodzimy dalej wyłącznie na
podstawie spadającego lossu — wymagane są określone artefakty i pomiary.

## Sprint 1 — dane warsztatowe

**Czas:** 3–4 dni  
**Cel:** stworzyć wiarygodny i kontrolowany zbiór do SFT.

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

## Sprint 3 — LoRA i QLoRA

**Czas:** 3–4 dni  
**Cel:** uzyskać pierwszy powtarzalny adapter i działającą demonstrację.

### Zakres

- instalacja i preflight PEFT, TRL, datasets i bitsandbytes,
- test kwantyzacji NF4 na GPU 12 GB,
- pipeline tokenizacji i chat template,
- LoRA BF16, jeśli pozwoli pamięć,
- QLoRA 4-bit jako główna konfiguracja,
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
- nie oceniamy jakości na danych treningowych.

### Bramka M3 — Adapter candidate

Adapter przechodzi do pełnej oceny tylko wtedy, gdy działa technicznie i poprawia
co najmniej część metryk walidacyjnych względem B1.

## Sprint 4 — benchmark i eksperymenty zaawansowane

**Czas:** 4–5 dni  
**Cel:** udowodnić, gdzie QLoRA pomaga, a gdzie nie wystarcza.

### Zakres

- L1: LoRA BF16,
- Q1: QLoRA,
- Q2: QLoRA + kontrole deterministyczne,
- Q3: QLoRA + kontrole + procedura w kontekście,
- trzy seedy dla głównych konfiguracji,
- ablations: rank, `alpha`, attention-only vs `all-linear`,
- opcjonalnie rsLoRA i DoRA,
- testy adversarial, regresyjne i braku danych,
- analiza false positives i false negatives,
- katalog najlepszych oraz najgorszych odpowiedzi.

### Rezultaty

- końcowa macierz porównawcza B0–Q3,
- wykresy jakości, czasu, VRAM i rozmiaru adaptera,
- raport analizy błędów,
- rekomendacja architektury dla przypadku bankowego.

### Kryteria odbioru

- wyniki główne raportują średnią i rozrzut między seedami,
- false positive rate jest raportowany oddzielnie,
- `INSUFFICIENT_DATA` i przypadki wysokiego ryzyka mają osobne metryki,
- nie ukrywamy regresji ani wariantów, które nie poprawiły jakości,
- wszystkie liczby na przyszłych slajdach prowadzą do zapisanego artefaktu.

### Bramka M4 — Evidence package

Zamrażamy wyniki, konfiguracje i przykłady używane w materiałach szkoleniowych.

## Sprint 5 — materiały szkoleniowe

**Czas:** 4–5 dni  
**Cel:** zamienić eksperyment w profesjonalne szkolenie.

### Zakres

- 45–55 slajdów,
- notatki prowadzącego na poziomie zaawansowanym,
- notebooki: baseline, dane, LoRA, QLoRA, ewaluacja i adapter operations,
- diagramy LoRA, QLoRA i architektury bankowej,
- ściąga parametrów i troubleshooting,
- katalog zastosowań PEFT w banku,
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

| Sprint | Czas | Kamień milowy | Udział w pozostałej pracy |
|---|---:|---|---:|
| 1. Dane | 3–4 dni | M1 Data freeze | 20% |
| 2. Baseline 4B | 2–3 dni | M2 Baseline freeze | 10% |
| 3. LoRA/QLoRA | 3–4 dni | M3 Adapter candidate | 20% |
| 4. Benchmark | 4–5 dni | M4 Evidence package | 20% |
| 5. Materiały | 4–5 dni | M5 Content freeze | 20% |
| 6. Próba i wydanie | 2–3 dni | M6 Workshop ready | 10% |

Szacunek zakłada około 8–15 godzin wykorzystania GPU dla treningów głównych i
eksperymentów. Czas może wzrosnąć, jeżeli wykonamy szeroki sweep hiperparametrów
albo zwiększymy zbiór powyżej 700 przykładów.

## 6. Kluczowe wskaźniki projektu

### Jakość rozwiązania

- schema validity co najmniej 95%,
- poprawa macro-F1 względem najlepszego baseline'u promptowego,
- raportowany false positive rate,
- osobny wynik dla `INSUFFICIENT_DATA`,
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
| Adapter uczy biasu do FAIL lub PASS | wysoki | balans klas i analiza macierzy pomyłek |
| Dobry JSON maskuje złą decyzję | wysoki | osobne metryki struktury i treści |
| Training demo trwa zbyt długo | średni | krótki dataset demonstracyjny i gotowy adapter |
| Brak internetu na sali | wysoki | lokalny cache wszystkich artefaktów |
| Zmiana bibliotek lub modelu | średni | lockfile, przypięte rewizje i tag wydania |
| Rozrost zakresu metod PEFT | średni | LoRA/QLoRA jako rdzeń; DoRA/IA3 tylko rozszerzenie |
| Błędna interpretacja biznesowa | wysoki | human-in-the-loop i wyraźne granice systemu |

## 8. Zarządzanie zakresem

### Must have

- dataset i jego dokumentacja,
- baseline 4B,
- działający QLoRA,
- benchmark B0/B1/B2/Q1/Q2,
- notebook demonstracyjny,
- slajdy i trainer guide,
- próba generalna oraz adapter awaryjny.

### Should have

- LoRA BF16,
- Q3 z kontekstem procedury,
- trzy seedy,
- testy adversarial i regresyjne,
- analiza ranku i modułów docelowych.

### Could have

- DoRA i rsLoRA,
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
- proponowane tagi: `dataset-v1`, `baseline-v1`, `adapter-v0.1`,
  `content-freeze-v1`, `workshop-v1.0`,
- komunikaty commitów używają formy `feat:`, `fix:`, `docs:`, `test:`,
  `experiment:` i `chore:`.

## 10. Następna decyzja wykonawcza

Rozpoczynamy Sprint 1. Pierwszy przegląd następuje po wygenerowaniu próbnych
100–150 rekordów, zanim rozszerzymy zbiór do pełnej wielkości. Pozwala to
skorygować jakość szablonów bez kosztownego przebudowywania całego datasetu.

