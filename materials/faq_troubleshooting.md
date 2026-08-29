# FAQ i troubleshooting prowadzącego

## Pytania merytoryczne

### Czy większy rank zawsze daje lepszą jakość?

Nie. Daje większą pojemność i koszt. Rank wybieramy eksperymentalnie przy stałych
danych i metrykach. W tym projekcie rank 8 dał 33,1 MB wag adaptera, a rank 16
66,1 MB; to porównanie kosztu, nie jakości.

### Czy QLoRA oznacza, że wszystko jest liczone w 4 bitach?

Nie. W 4 bitach przechowywana jest zamrożona baza. Obliczenia mogą używać BF16,
a adapter i gradienty mają własne typy danych.

### Kiedy wybrać RAG zamiast LoRA?

Gdy problemem jest aktualna, cytowalna wiedza. LoRA lepiej nadaje się do
stabilnego formatu i zachowania. W systemie bankowym często potrzebne są oba.

### Czy adapter można traktować jako wersję modelu?

Tak, ale tylko razem z ID i rewizją bazy, konfiguracją, promptem, hashami danych,
metrykami i warunkami użycia. Sam plik `safetensors` nie wystarcza.

### Dlaczego nie otwieramy protected evidence?

Diagnostic ujawnił FC-209, a guard powstał po jego analizie. Guard poprawia
bezpieczeństwo systemu, lecz nie jest niezależnym dowodem generalizacji. Bramka
pozostaje `HOLD`.

## Problemy podczas demonstracji

| Objaw | Diagnoza | Działanie prowadzącego |
|---|---|---|
| Out of memory | aktywacje lub rezerwacja przekroczyły budżet | zmniejsz `max_length` lub batch, zachowaj gradient accumulation; przejdź do fallbacku |
| Przykłady są ucinane | `max_length` poniżej p95/max danych | zatrzymaj trening; truncation narusza kontrakt demo |
| Loss spada, ale statusy są złe | loss nie mierzy decyzji biznesowej | pokaż benchmark per status i minimalne pary |
| JSON valid, schema invalid | generacja urwana albo pole pominięte | sprawdź `max_new_tokens` i kontrakt; nie uznawaj samego JSON za sukces |
| Reload 128 tokenów nie przeszedł | limit uciął kompletną odpowiedź | użyj zatwierdzonego `max_new_tokens=384`; nie zmieniaj golda |
| Adapter nie ładuje się | niezgodny model lub rewizja | porównaj manifest, ID bazy i revision; nie wymuszaj ładowania |
| Zapis checkpointu zawiódł | problem dysku/serializacji po poprawnym kroku | zachowaj log incydentu, użyj końcowego adaptera lub fallbacku |
| Źródło nie istnieje | hallucination albo błąd kontraktu | source-integrity guard i human review; nie poprawiaj odpowiedzi po cichu |
| Status przeczy poprawnemu obliczeniu | błąd semantyczny jak FC-209 | deterministic guard blokuje, człowiek rozstrzyga |
| Brak internetu | pobieranie modelu nie zadziała | użyj lokalnego cache, zapisanych logów i referencyjnego adaptera |

## Twardy limit demo

Jeżeli trening przekracza 15 minut albo środowisko staje się niestabilne:

1. przerwij część obliczeniową,
2. pokaż zapisane metryki Q1-DEMO,
3. omów manifest i rozmiar adaptera,
4. pokaż wynik fresh reloadu,
5. porównaj z pełnym Q1 i przejdź do benchmarku.

To zachowuje cele dydaktyczne bez udawania, że wynik mini-treningu dowodzi jakości.

