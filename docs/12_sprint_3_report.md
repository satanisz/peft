# Sprint 3 — raport QLoRA i decyzja M3

## Executive summary

Sprint 3 zakończył się decyzją **M3 PASS — Adapter candidate**. Głównym
kandydatem jest Q1: adapter QLoRA dla `Qwen/Qwen3-4B-Instruct-2507`, trenowany
na 400 rekordach `dataset-v1` oraz 240 rekordach `boundary train`.

Q1 zachował macro-F1 1,000 na oryginalnym validation i poprawił boundary
macro-F1 z 0,786 dla Q0 do 1,000. Osiągnął 100% poprawności 60 minimalnych par,
zero unsafe `PASS`, zero nadmiernych eskalacji oraz 0% FAIL FPR. Wobec B3
zmniejszył średni prompt wejściowy z 2897 do 1401 tokenów, czyli o 51,6%.

Jest to zgoda na wykorzystanie adaptera jako kandydata warsztatowego i wejście
do Sprintu 4, nie zgoda na użycie produkcyjne w banku. Wynik pochodzi z jednego
seeda i danych syntetycznych. Oryginalny test, boundary test oraz challenge
pozostają nieotwarte.

## Co zostało wykonane

- powtarzalny pipeline QLoRA: NF4, double quant, BF16 compute i LoRA
  `all-linear`, rank 16, alpha 32,
- completion-only loss i status-aware zero-shot prompt,
- Q0 jako kontrola bez boundary train oraz Q1 jako główny wariant,
- 3 epoki bez obcięcia żadnego przykładu,
- model-only checkpointing odporny na problem serializacji optymalizatora na
  Windows,
- walidacja Q0/Q1 na oryginalnym i boundary validation,
- inspekcja adaptera, bezpieczny merge BF16 i realny reload scalonego modelu,
- 27-minutowy scenariusz demonstracyjny dla prowadzącego.

## Parametry i koszt treningu

| Wariant | Dane train | Kroki | Czas | Train loss | Peak VRAM | Truncation |
|---|---:|---:|---:|---:|---:|---:|
| Demo | 50 | 12 | 1 min 42 s | — | 7,49 GiB | 0 |
| Q0 | 400 | 150 | 54 min 53 s | 0,1186 | 7,38 GiB | 0 |
| Q1 | 640 | 240 | 88 min 22 s | 0,0830 | 7,55 GiB | 0 |

W obu pełnych wariantach trenowano 33 030 144 parametrów, około 1,48% parametrów
widocznych przez pipeline. Lossu Q0 i Q1 nie należy interpretować jako
samodzielnej miary jakości ani porównywać bez uwzględnienia różnej kompozycji
danych.

## Wyniki jakościowe

### Oryginalny validation — 50 przypadków

| Wariant | Status accuracy | Macro-F1 | Schemat | Severity | FAIL FPR |
|---|---:|---:|---:|---:|---:|
| Q0 | 100% | 1,000 | 100% | 96% | 0% |
| Q1 | 100% | 1,000 | 100% | 94% | 0% |

Q1 nie pogorszył głównej decyzji, schematu ani evidence. Severity spadło o jeden
przypadek względem Q0; błąd pozostaje do analizy regresyjnej w Sprincie 4.

### Boundary validation — 120 przypadków / 60 par

| Wariant | Macro-F1 | WARN recall | N/A recall | Brak danych recall | Pary | FAIL FPR | Unsafe PASS | Eskalacja |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B3 | 0,894 | 93,3% | 100% | 76,7% | 81,7% | 8,6% | 2,7% | 7,8% |
| Q0 | 0,786 | 66,7% | 80% | 90% | 61,7% | 9,5% | 8,0% | 11,1% |
| Q1 | 1,000 | 100% | 100% | 100% | 100% | 0% | 0% | 0% |

Najważniejsza ablation jest jednoznaczna: samo dostrojenie na standardowym
train nie wystarczyło. Dodanie boundary train dało względem Q0 +0,214
macro-F1, +38,3 pp pair accuracy, +33,3 pp WARN recall i usunęło unsafe PASS.
To jest centralny przykład biznesowo-techniczny warsztatu: jakość danych na
granicach decyzji miała większe znaczenie niż samo uruchomienie QLoRA.

## Efektywność i artefakty

- adapter Q1: 66 127 776 bajtów wag; cały katalog 77 562 126 bajtów,
- trainable parameters: 33 030 144,
- model scalony BF16: 8 056 443 216 bajtów,
- merge: `safe_merge=true`,
- reload scalonego modelu: PASS na development case, 11,88 s,
- Q1 boundary p95 latency: 24,60 s,
- Q1 boundary peak GPU podczas inferencji: 3,53 GiB,
- redukcja input tokens względem B3: 51,6%.

Wagi i model scalony pozostają lokalnie w `artifacts/` i nie trafiają do Git.
Repozytorium przechowuje konfiguracje, hashe, metryki, odpowiedzi walidacyjne i
manifesty umożliwiające audyt.

## Incydent checkpointów

Pierwszy formalny bieg Q0 zatrzymał się podczas serializacji pełnego stanu
`paged_adamw_8bit` na Windows. Bieg został odrzucony, a diagnostyczny checkpoint
nie wszedł do M3. Po ustawieniu `save_only_model=true` Q0 wykonał 150/150, a Q1
240/240 kroków. Adaptery, checkpointy model-only, merge i reload zostały
zweryfikowane. Incydent `S3-Q0-CHECKPOINT-001` ma status `resolved`.

Konsekwencją workaroundu jest brak automatycznego resume stanu optymalizatora.
Jest to akceptowalne dla referencyjnego treningu warsztatowego od początku, ale
nie powinno być bezrefleksyjnie kopiowane do długich treningów produkcyjnych.

## Decyzja M3

Wszystkie formalne kryteria M3 są spełnione:

- oba treningi zakończone i zero truncation,
- peak VRAM poniżej 12 GiB,
- demo poniżej 15 minut,
- adapter i model scalony można ponownie załadować,
- schemat co najmniej 98%,
- poprawa boundary przy jednoczesnej redukcji tokenów,
- brak regresji recall `WARN`, `PASS` i `FAIL`,
- `NOT_APPLICABLE` recall powyżej progu,
- FAIL FPR poniżej progu.

**Decyzja: PASS — Q1 jest kandydatem `adapter-v0.1` do pełnego benchmarku.**
Q1b nie jest potrzebny jako wariant naprawczy w Sprincie 3.

## Ograniczenia i ryzyka

1. Wyniki pochodzą z danych syntetycznych i jednego seeda.
2. Boundary train i validation są rozłączne grupowo, ale pochodzą z tego samego
   generatora i rodzin wzorców; perfekcyjny wynik może zawyżać generalizację.
3. Validation było używane do wyboru Q1, dlatego nie jest końcowym estymatorem
   jakości.
4. Oryginalny test, boundary test i challenge pozostają zamknięte do Sprintu 4.
5. Severity na oryginalnym validation wynosi 94%, mimo perfekcyjnych statusów.
6. Każde rzeczywiste zastosowanie bankowe wymaga danych zatwierdzonych przez
   ekspertów, human-in-the-loop, kontroli deterministycznych i governance.

## Rekomendacja dla Sprintu 4

Przypiąć Q1 jako jednoseedowy adapter candidate i rozpocząć pełny benchmark:
trzy seedy, zamknięte testy, challenge, analiza błędów severity oraz porównanie
Q1 z Q2 (adapter + kontrole deterministyczne). Rank i target modules badać
dopiero jako jawne ablations; nie wykonywać Q1b bez wykrytej regresji.

Pełne metryki i automatyczna bramka znajdują się w
`results/sprint3/m3_summary.json` oraz `results/sprint3/m3_summary.md`.
