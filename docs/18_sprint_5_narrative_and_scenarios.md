# Sprint 5 — narracja, slajdy i scenariusze warsztatowe

## Cel komunikacyjny

Po 180 minutach uczestnicy mają umieć dobrać metodę adaptacji LLM, przeczytać
konfigurację LoRA/QLoRA, zaprojektować eksperyment bez leakage oraz obronić
decyzję, które elementy bankowego procesu należą do LLM, kodu
deterministycznego i człowieka.

Centralna teza szkolenia:

> PEFT tanio uczy zachowania, ale nie zwalnia z projektowania danych,
> benchmarku i warstw bezpieczeństwa.

Otwarciem i finałem jest FC-209. Model we wszystkich trzech seedach poprawnie
obliczył `2418 - 2391 = 27`, a następnie uznał, że 27 nie przekracza progu 5.
Przypadek pozwala połączyć matematykę LoRA, projekt danych, ewaluację i
governance bez przedstawiania adaptera jako rozwiązania produkcyjnego.

## Przebieg 180 minut

| Czas | Slajdy | Akt | Rezultat uczestnika |
|---:|---:|---|---|
| 0–10 | 1–5 | problem i kontrakt sukcesu | rozumie, co naprawdę mierzymy |
| 10–25 | 6–9 | wybór interwencji | odróżnia prompt, RAG, SFT, PEFT i CPT |
| 25–50 | 10–18 | LoRA od środka | rozumie rank, alpha, target modules i adapter lifecycle |
| 50–80 | 19–25 | QLoRA i pamięć | odróżnia typ przechowywania od typu obliczeń |
| 80–90 | 26 | przerwa | — |
| 90–105 | 27–33 | dane i eksperyment | rozpoznaje leakage i wartość par granicznych |
| 105–148 | 34–40 | demonstracja | potrafi czytać log, manifest i wynik reloadu |
| 148–168 | 41–48 | benchmark i analiza błędów | nie myli perfekcyjnej validation z generalizacją |
| 168–180 | 49–53 | bank, governance, decyzja | projektuje human-in-the-loop i dalszy plan |

## Mapa 53 slajdów

| # | Tytuł / rola narracyjna |
|---:|---|
| 1 | Parameter-Efficient Fine-Tuning w banku — otwarcie |
| 2 | Model policzył 27, a następnie uznał, że 27 ≤ 5 — napięcie |
| 3 | Sukces ma trzy mierzalne wymiary, osadzone w bezpieczeństwie procesu |
| 4 | Financial Control Copilot wspiera, ale nie zatwierdza — zakres |
| 5 | Jedna historia prowadzi od promptu do guarda — mapa spotkania |
| 6 | Najpierw ustal, czy problem dotyczy wiedzy czy zachowania |
| 7 | Prompt, RAG, SFT, PEFT i continued pretraining rozwiązują inne problemy |
| 8 | Najlepsze bankowe przypadki PEFT mają stabilny kontrakt i dużo powtórzeń |
| 9 | Ćwiczenie 1: dobierz interwencję do czterech przypadków |
| 10 | Full fine-tuning aktualizuje wszystko; zwykle nie tego potrzebujemy |
| 11 | LoRA zakłada, że użyteczna aktualizacja ma niski efektywny rząd |
| 12 | W′ = W + (α/r)BA — mała ścieżka aktualizacji obok zamrożonej wagi |
| 13 | Rank 16 może zastąpić miliony trenowanych parametrów |
| 14 | Target modules określają, gdzie model może zmienić zachowanie |
| 15 | Rank, alpha, dropout i inicjalizacja tworzą jeden układ |
| 16 | Adapter można zapisać, przełączyć, zmergować albo wycofać |
| 17 | rsLoRA, DoRA, AdaLoRA i IA3 są narzędziami do innych ograniczeń |
| 18 | Checkpoint: pięć pytań, zanim uruchomisz trening |
| 19 | QLoRA trenuje adapter przez zamrożony model przechowywany w 4 bitach |
| 20 | Pamięć zużywają nie tylko wagi — liczą się aktywacje, gradienty i optimizer |
| 21 | NF4 kompresuje bazowe wagi, nie cały pipeline treningowy |
| 22 | Double quantization i paged optimizer mają różne role |
| 23 | Storage dtype i compute dtype odpowiadają na dwa różne pytania |
| 24 | Konfiguracja referencyjna mieści QLoRA 4B w około 7,6 GiB VRAM |
| 25 | LoRA, QLoRA czy pełny FT? Wybór zaczyna się od ograniczenia |
| 26 | Przerwa — po powrocie przechodzimy od mechaniki do eksperymentu |
| 27 | LLM jest jedną warstwą systemu bankowego |
| 28 | Pięć statusów rozdziela błąd, brak danych i brak zastosowania |
| 29 | Split po rodzinach chroni przed nauką parafraz tego samego przypadku |
| 30 | Jedna zmieniona przesłanka tworzy wartościową parę graniczną |
| 31 | Dobry JSON nie oznacza dobrej decyzji — baseline 0.6B |
| 32 | Q0 vs Q1 izoluje wartość danych granicznych, nie samego treningu |
| 33 | Ćwiczenie 2: oznacz status i wskaż przesłankę rozstrzygającą |
| 34 | Demo ma pokazać pipeline, nie udawać pełnego eksperymentu |
| 35 | Trening obserwujemy w warstwach uczenia, zasobów i danych |
| 36 | Q1: rank 16, alpha 32, all-linear, 640 przykładów, 240 kroków |
| 37 | Produktem treningu jest mały adapter i manifest, nie katalog checkpointów |
| 38 | Reload jest częścią testu; merge to decyzja wdrożeniowa |
| 39 | Checkpoint może zawieść przy zapisie mimo poprawnego kroku treningu |
| 40 | Plan B jest elementem profesjonalnego demo, nie oznaką porażki |
| 41 | Macro-F1 jest początkiem rozmowy, a nie końcową zgodą |
| 42 | Boundary data zmieniły wynik Q1: 1,000 F1 i 100% par |
| 43 | Trzy seedy usuwają wygodną historię o jednym szczęśliwym przebiegu |
| 44 | Prompt v2 naprawił kontrakt pól, nie decyzje modelu |
| 45 | Pięć przypadków ujawniło różne klasy błędów |
| 46 | FC-209: poprawne obliczenie, błędna decyzja we wszystkich seedach |
| 47 | Guard blokuje sprzeczność; nie naprawia odpowiedzi po cichu |
| 48 | Ćwiczenie 3: otwieramy protected evidence czy zatrzymujemy bramkę? |
| 49 | Portfel bankowy: od niskiego ryzyka do decyzji o wysokiej konsekwencji |
| 50 | Adapter to tylko jeden element model risk management |
| 51 | Human oversight zależy od wpływu systemu na decyzję, nie od nazwy modelu |
| 52 | Plan 90 dni: najpierw kontrakt i benchmark, dopiero potem skala |
| 53 | Trzy prawdy: dane graniczne, wiele metryk, hybrydowa odpowiedzialność |

## Scenariusz ćwiczenia 1 — wybór interwencji

**Czas:** 6 minut. **Forma:** cztery grupy po 3–4 osoby.

Każda grupa otrzymuje jeden przypadek:

1. Co tydzień zmienia się treść procedury, a odpowiedź ma ją cytować.
2. Format i styl odpowiedzi są stabilne, ale model regularnie myli statusy.
3. Model nie zna nowego słownictwa produktowego i dokumentów domenowych.
4. Potrzebna jest jedna reguła liczbowa `różnica > próg`.

Oczekiwane decyzje: odpowiednio RAG, PEFT/SFT, continued pretraining rozważane
łącznie z RAG/SFT oraz kod deterministyczny. Prowadzący pyta o koszt błędu i
częstotliwość zmiany wiedzy. Nie uznaje „fine-tuning wszystkiego” za odpowiedź
bez wskazania mechanizmu.

## Scenariusz ćwiczenia 2 — granice statusów

**Czas:** 8 minut. **Forma:** głosowanie, następnie praca w parach.

Uczestnicy klasyfikują trzy minimalne pary:

- `PASS → WARN`: odchylenie 0,4 vs 1,4 mln PLN,
- `WARN → FAIL`: ta sama niezgodność poniżej i powyżej progu materialności,
- `NOT_APPLICABLE → INSUFFICIENT_DATA`: brak triggera vs trigger obecny, lecz
  brak obowiązkowego źródła.

Punkt dydaktyczny: różnica między klasami powinna być zapisana jako przesłanka,
nie pozostawiona intuicji anotatora. Prowadzący zbiera rozbieżności i wiąże je z
koniecznością review goldów.

## Scenariusz demonstracji QLoRA

**Czas:** 35–43 minuty. **Model wykonawczy:** Luna/low.

1. Pokaż konfigurację demo i policz trainable parameters.
2. Uruchom 12-krokowy trening na 50 zbalansowanych przykładach.
3. Co kilka kroków pokaż loss, peak VRAM i brak truncation.
4. W trakcie treningu omów NF4, BF16 compute i gradient accumulation.
5. Po treningu pokaż katalog adaptera oraz manifest.
6. W świeżym procesie wykonaj reload i jedną inferencję.
7. Porównaj demo z przygotowanymi wynikami Q0/Q1; nie wyciągaj wniosków
   jakościowych z 12 kroków.

Plan awaryjny: jeżeli trening przekroczy 15 minut albo środowisko GPU zawiedzie,
zatrzymaj go, pokaż zapisany log `results/sprint3/demo_dry_run.json`, załaduj
referencyjny adapter Q1 i kontynuuj od reloadu. Uczestnicy zawsze widzą
rzeczywisty artefakt oraz pełne, wcześniej zamrożone wyniki.

## Scenariusz ćwiczenia 3 — decyzja bramkowa

**Czas:** 7 minut. **Forma:** mini-komitet model risk.

Grupa otrzymuje:

- validation 1,000 macro-F1 dla trzech seedów,
- diagnostic macro-F1 od 0,834 do 0,949,
- FC-209: trzy razy `PASS` mimo `27 > 5`,
- guard blokujący FC-209, zaprojektowany po analizie diagnostic.

Pytanie: „Czy otwieramy protected evidence?”. Poprawna decyzja warsztatowa to
`HOLD`: retrospektywny guard ogranicza ryzyko operacyjne, ale nie poprawia
metryk modelu i nie jest niezależnym dowodem generalizacji. Jednocześnie wynik
jest gotowy do wykorzystania w materiale szkoleniowym.

## Runbook prowadzącego

- Przed spotkaniem: sprawdzić GPU, lokalne modele, adaptery, zależności i wolne
  miejsce; uruchomić demo dry-run.
- W czasie spotkania: nie czekać na długi trening; limit 15 minut jest twardy.
- Każdy wykres przedstawiać w kolejności: pytanie → liczba → znaczenie →
  ograniczenie.
- Nie pokazywać protected splitów. Obowiązujący status to `HOLD`.
- Przy pytaniu prawnym odróżnić wzorzec governance od porady prawnej i odesłać
  do aktualnego tekstu AI Act oraz polityk banku.
- Po spotkaniu: zebrać decyzje z ćwiczeń, błędne etykiety i pytania do FAQ.

## Kryteria odbioru tego etapu

- 53 slajdy z notatkami prowadzącego i blokami źródeł,
- trzy ćwiczenia z oczekiwanymi odpowiedziami,
- pełny scenariusz demo oraz plan awaryjny,
- realne wyniki projektu, bez otwierania protected evidence,
- jasne rozdzielenie jakości modelu, bezpieczeństwa systemu i gotowości
  produkcyjnej,
- zweryfikowany wizualnie plik PPTX.
