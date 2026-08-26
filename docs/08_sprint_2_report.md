# Raport Sprintu 2 — baseline Qwen3-4B

## Decyzja wykonawcza

Sprint 2 osiągnął bramkę **M2 Baseline freeze**. Zamrażamy model, prompty,
dekodowanie i formalne wyniki walidacyjne jako punkt odniesienia dla LoRA i
QLoRA. Głównym baseline'em jakościowym jest **B2 few-shot**; **B1** pozostaje
ważnym, tańszym punktem odniesienia dla wartości samego prompt engineeringu.

Wynik nie uzasadnia samodzielnego użycia modelu w procesie bankowym. B2 poprawnie
klasyfikuje 72% przypadków, ale nadal myli część `WARN`, nie rozpoznaje jedynego
przypadku `NOT_APPLICABLE` i generuje fałszywe alarmy `FAIL`.

## Zamrożona konfiguracja

- model: `Qwen/Qwen3-4B-Instruct-2507`,
- rewizja: `cdbee75f17c01a7cc42f958dc650907174af0554`,
- typ parametrów: BF16,
- dekodowanie: greedy, `do_sample=false`, thinking wyłączony,
- limit odpowiedzi: 384 tokeny,
- dataset: `dataset-v1.0.0`, SHA-256
  `ffa0da9497872513506655df64d200289b33d608ac6b37c6bc89d906bb843d7c`,
- tuning promptu: wyłącznie 50 przypadków `development`,
- formalna ocena: 50 przypadków `validation`,
- `test` i `challenge`: nieotwarte w Sprincie 2.

Pełny kontrakt eksperymentu znajduje się w `configs/baseline_v1.json`.

## Warianty

- **B0** — minimalny prompt zero-shot bez jawnego kontraktu pól,
- **B1** — dopracowany prompt zero-shot z zasadami bezpieczeństwa i dokładnym
  kontraktem JSON,
- **B2** — prompt B1 oraz dwa deterministycznie dobrane przykłady ze splitu
  `train`, bez rodziny docelowego przypadku.

Model, dane i parametry generowania są identyczne. Zmienia się tylko kontrakt
promptu i liczba demonstracji.

## Formalne wyniki validation

| Wariant | JSON | Schemat | Status accuracy | Macro-F1 | Źródła | Human review | FAIL FPR | p95 | Peak VRAM |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B0 | 100% | 0% | 12% | 0,109 | 98% | 0% | 0,0%* | 14,85 s | 7,65 GiB |
| B1 | 100% | 100% | 46% | 0,349 | 100% | 48% | 20,0% | 14,67 s | 8,04 GiB |
| B2 | 100% | 100% | **72%** | **0,529** | 100% | **86%** | **14,3%** | 17,62 s | 9,86 GiB |

\* W B0 status zwykle nie znajduje się w wymaganej strukturze. Zerowy formalny
FAIL FPR nie oznacza bezpieczeństwa biznesowego i nie powinien być porównywany
bez informacji o zerowej zgodności schematu.

Wszystkie trzy warianty zwróciły tekst zawierający możliwy do wyodrębnienia
JSON, ale dopiero B1 i B2 spełniły kontrakt systemu. B2 zwiększył status accuracy
o 26 punktów procentowych i macro-F1 o 0,180 względem B1, kosztem około 2,4 razy
większego wejścia i 1,82 GiB dodatkowego peak VRAM.

## Koszt techniczny

| Wariant | Śr. input | Śr. output | Śr. latencja | p95 | Śr. output tok/s | Obcięte | Peak VRAM |
|---|---:|---:|---:|---:|---:|---:|---:|
| B0 | 309 | 342 | 12,87 s | 14,85 s | 26,62 | 44% | 7,65 GiB |
| B1 | 967 | 272 | 11,68 s | 14,67 s | 23,39 | 0% | 8,04 GiB |
| B2 | 2295 | 172 | 10,54 s | 17,62 s | 16,75 | 0% | 9,86 GiB |

Few-shot ma największy kontekst i najwyższe zużycie pamięci, ale generuje
krótsze, bardziej regularne odpowiedzi. Wyższe p95 B2 wynika z kilku długich
przypadków na początku przebiegu; mediana i średnia pozostają niższe niż dla B1.

## Iteracja promptu na development

Pierwszy prompt B1 osiągnął 52% schema validity. Analiza błędów wykazała przede
wszystkim niedozwoloną wartość `deterministic_check` w polu `performed_by`, puste
`recommended_action` oraz kopiowanie `content` zamiast `value`. Jedna jawna
iteracja doprecyzowała te reguły i podniosła na development:

- schema validity: 52% → 98%,
- status accuracy: 48% → 50%,
- macro-F1: 0,477 → 0,542.

Zachowano wyniki wersji v0, aby pokazać uczestnikom mierzalny efekt inżynierii
promptu. Po zamrożeniu promptu nie wprowadzano zmian na podstawie validation.

## Analiza błędów i znaczenie biznesowe

### B1

- `WARN`: F1 0,190,
- `INSUFFICIENT_DATA`: F1 0,353,
- `NOT_APPLICABLE`: F1 0,000,
- najtrudniejsze typy: `VARIANCE` (0/5 poprawnych), `DISCLOSURE` (1/5),
  `CROSS_SECTION`, `CURRENCY`, `INSUFFICIENT_DATA` i `PERIOD` (po 2/5).

B1 opanował format, lecz często błędnie rozstrzyga przypadki pośrednie. Sam
kontrakt JSON nie wystarcza do uzyskania dobrej decyzji kontrolnej.

### B2

- `PASS`: F1 0,857,
- `FAIL`: F1 0,788,
- `INSUFFICIENT_DATA`: F1 0,667,
- `WARN`: F1 0,333,
- `NOT_APPLICABLE`: F1 0,000 przy wsparciu jednego przypadku,
- najtrudniejsze typy: `DISCLOSURE` (2/5), `EVIDENCE`, `INSUFFICIENT_DATA` i
  `VARIANCE` (po 3/5).

B2 dobrze rozpoznaje przypadki jednoznaczne, ale wciąż zbyt łatwo eskaluje część
przypadków granicznych do `FAIL` i nie zawsze zatrzymuje się przy braku danych.
W banku oznacza to koszt niepotrzebnych alertów oraz ryzyko pozornie pewnego
wniosku przy niepełnym materiale. System musi pozostać human-in-the-loop.

## Szacunek czasu treningu Sprintu 3

Zamrożony train ma 384 800 tokenów na epokę, czyli 1 154 400 tokenów dla trzech
epok. Rzeczywista przepustowość treningu zostanie zmierzona w Sprincie 3;
scenariusze planistyczne są następujące:

| Efektywna przepustowość | 1 epoka | 3 epoki |
|---:|---:|---:|
| 100 tokenów/s | ok. 64 min | ok. 3 h 12 min |
| 300 tokenów/s | ok. 21 min | ok. 1 h 4 min |
| 600 tokenów/s | ok. 11 min | ok. 32 min |

To czas samego kroku treningowego; inicjalizacja, ewaluacja, checkpointy i
ewentualne ponowienia zwiększą czas ścienny. Krótka demonstracja 10–15 minut
będzie korzystać z podzbioru danych i gotowego adaptera awaryjnego.

## Artefakty M2

- `configs/baseline_v1.json` — zamrożony kontrakt,
- `results/b0_4b_validation*.json*` — odpowiedzi i metryki B0,
- `results/b1_4b_validation*.json*` — odpowiedzi i metryki B1,
- `results/b2_4b_validation*.json*` — odpowiedzi i metryki B2,
- `results/baseline_v1_validation_summary.json` — tabela i katalog błędów,
- `results/sprint2_environment.json` — środowisko sprzętowe i biblioteki,
- `results/*prompt_v0*` — audytowalna pierwsza iteracja promptu.

## Następny krok

Przed Sprintem 3 wykonujemy Sprint 2.5 — Label Boundary Hardening. Powstanie
jednoznaczna polityka statusów, osobny boundary pack oraz label-complete B3.
Nie zmieniamy zamrożonych wyników tego raportu. QLoRA przejdzie dalej dopiero po
M2.5 i będzie oceniane względem B1, B2 i B3 na oryginalnym oraz boundary
validation. Główna ocena na obu splitach `test` nastąpi dopiero po wyborze
adaptera.
