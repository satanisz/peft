# Sprint 3 — scenariusz QLoRA po M2.5

## Decyzja projektowa

Sprint 3 przenosi wnioski M2.5 z warstwy promptu do adaptera. B3 pokazał, że
jawna hierarchia pięciu statusów i trzy demonstracje graniczne podnoszą
boundary macro-F1 do 0,894, ale zwiększają średni prompt do 2897 tokenów. Q1 ma
sprawdzić, czy QLoRA zachowa rozróżnienia `WARN`, `NOT_APPLICABLE` i
`INSUFFICIENT_DATA` bez przykładów w kontekście.

Nie traktujemy spadku lossu jako dowodu jakości. Dowodem jest dopiero porównanie
Q0 i Q1 na tych samych, osobno raportowanych zbiorach validation oraz przejście
bramki M3.

## Kontrolowany eksperyment

| Element | Q0 | Q1 |
|---|---|---|
| Model bazowy | Qwen3-4B-Instruct-2507 | ten sam |
| Metoda | QLoRA, NF4 + double quant | ta sama |
| LoRA | rank 16, alpha 32, all-linear | ta sama |
| Trening | 3 epoki, batch efektywny 8 | ten sam |
| Dane podstawowe | 400 train v1 | 400 train v1 |
| Boundary train | brak | 240 rekordów / 120 par |
| Prompt inferencji | status-aware, zero-shot | ten sam |
| Validation | oryginalny + boundary | te same |

Q0 izoluje efekt samego SFT/adaptera. Różnica Q1−Q0 mierzy wartość danych
granicznych, ponieważ model, seed, prompt i hiperparametry pozostają stałe.
Q1b z samplingiem granicznym wolno uruchomić dopiero wtedy, gdy Q1 nie spełni
M3 i analiza błędów wskaże niedouczenie granic.

## Ochrona przed błędnym eksperymentem

- pipeline przyjmuje tylko pliki splitu `train` i odrzuca chronione nazwy przed
  odczytem,
- oryginalny test, boundary test i challenge pozostają nieotwarte do Sprintu 4,
- completion-only loss nie uczy modelu odtwarzania promptu,
- limit 1728 pokrywa maksimum 1672 tokenów; truncation jest zabronione,
- odpowiedź treningowa nie występuje w treści użytkownika,
- Q0 i Q1 różnią się tylko obecnością boundary train,
- adapter jest ponownie ładowany w świeżym procesie przed uznaniem bramki
  technicznej,
- wagi kosztu i polityka statusów pozostają syntetycznym materiałem
  warsztatowym, nie polityką banku.

## Scenariusz demonstracji na szkoleniu

Ten fragment zajmuje około 27 minut w bloku 105–132 całego warsztatu.

### 1. Problem biznesowy — 3 min

Prowadzący pokazuje wynik M2.5: B2 dobrze rozpoznaje część `WARN`, ale myli
wszystkie 30 braków danych z `FAIL`, natomiast B3 naprawia większość granic za
cenę długiego kontekstu. Pytanie dla grupy brzmi: czy chcemy płacić za reguły i
przykłady przy każdym wywołaniu, czy przenieść zachowanie do adaptera?

### 2. Trzy minimalne pary — 5 min

Uczestnicy otrzymują po jednej przesłance, która zmienia decyzję:

| Para | Kontrola | Zmiana decyzji | Przypadki validation |
|---|---|---|---|
| A | VARIANCE | `PASS → WARN` | `BD-0301`, `BD-0302` |
| B | UNIT | `WARN → FAIL` | `BD-0331`, `BD-0332` |
| C | DIRECTION | `NOT_APPLICABLE → INSUFFICIENT_DATA` | `BD-0361`, `BD-0362` |

Prowadzący pyta najpierw o przesłankę, a dopiero potem odsłania etykietę. Dzięki
temu `NOT_APPLICABLE` nie jest przedstawiane jako synonim braku dokumentu.

### 3. Co naprawdę trenujemy — 4 min

Na jednej konfiguracji pokazujemy NF4, double quantization, BF16 compute, rank,
alpha, `all-linear`, batch efektywny oraz completion-only loss. Wskazujemy, że
bazowe wagi pozostają zamrożone, a aktualizowane są tylko macierze adaptera.

### 4. Rzeczywisty mini-trening — 3–5 min

Uruchamiamy `Q1-DEMO`: 50 zbalansowanych przypadków, po 10 na każdy status,
rank 8 i 12 kroków. Celem nie jest jakość produkcyjna, tylko obserwacja pamięci,
lossu, gradientu oraz powstania adaptera. Limit demonstracji wynosi 15 minut;
jeśli środowisko zawiedzie, używamy wcześniej zapisanego adaptera demo i logu.

### 5. Pełny adapter i ablation — 7 min

Ładujemy przygotowane Q0 i Q1. Na tych samych trzech parach porównujemy:

1. B3 — silny prompt z trzema demonstracjami,
2. Q0 — adapter bez boundary train,
3. Q1 — adapter z boundary train.

Tabela pokazuje macro-F1, recall każdego statusu, pair accuracy, unsafe PASS,
nadmierną eskalację, FAIL FPR, koszt błędu i średnią długość wejścia. Najpierw
interpretujemy Q1−Q0, a dopiero później Q1−B3.

### 6. Decyzja bankowa — 4 min

Kończymy pytaniem, gdzie umieścić człowieka w procesie. Adapter może wspierać
triage, standaryzację ustaleń, kontrolę kompletności i pierwszą klasyfikację,
ale nie zatwierdza polityki rachunkowości ani wyjątku regulacyjnego. Każdy
`WARN`, `FAIL`, brak danych i przypadek niskiej pewności trafia do kontrolera.

## Bramka M3

Automatyczny raport wymaga jednocześnie:

- poprawnego treningu i ponownego załadowania adaptera,
- nie więcej niż 12 GiB peak VRAM i zero truncation,
- co najmniej 98% poprawnych schematów,
- boundary macro-F1 lepszego od B3 o 0,05 albo wyniku w granicy 0,02 przy
  redukcji wejścia o co najmniej 30%,
- braku regresji recall `WARN`, recall N/A co najmniej 60%,
- FAIL FPR nie wyżej niż 15%,
- regresji recall `PASS` i `FAIL` nie większej niż 5 p.p.

Raport zawsze pokazuje również `INSUFFICIENT_DATA`, pary, unsafe PASS,
nadmierną eskalację i ważony koszt. Jeżeli Q1 nie przejdzie, wynik pozostaje
wartościową demonstracją: pokazuje, że dane kontrastowe lub sampling wymagają
poprawy, zamiast zachęcać do przypadkowego sweepu hiperparametrów.

