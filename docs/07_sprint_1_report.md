# Sprint 1 — raport wykonania

## Status

**Ukończony — M1 Data freeze**

Wersja danych: `dataset-v1.0.0`  
Data zamrożenia: 26 sierpnia 2026  
Seed: `20260826`

## Zrealizowany zakres

- deterministyczny generator przypadków,
- pilot 120 rekordów,
- pełny zbiór 620 rekordów,
- 10 typów kontroli i 70 oznaczonych mutacji,
- grupowy podział danych,
- 20 przypadków prompt injection,
- audyt schematu, duplikatów, źródeł i leakage,
- ręczny przegląd 20 rekordów,
- karta danych oraz rejestr pochodzenia,
- analiza długości tokenów,
- osobne pliki dla każdego splitu.

## Wynik dataset-v1

| Split | Rekordy |
|---|---:|
| train | 400 |
| development | 50 |
| validation | 50 |
| test | 100 |
| challenge | 20 |
| **Razem** | **620** |

| Status | Rekordy | Udział |
|---|---:|---:|
| PASS | 194 | 31,3% |
| FAIL | 188 | 30,3% |
| INSUFFICIENT_DATA | 140 | 22,6% |
| WARN | 86 | 13,9% |
| NOT_APPLICABLE | 12 | 1,9% |

Rozkład nie tworzy dominującej klasy `PASS`, która była problemem modelu smoke.

## Kontrola jakości

- poprawność schematu: 620/620,
- dokładne duplikaty: 0,
- rodziny występujące w więcej niż jednym splicie: 0,
- challenge oznaczone jako prompt injection: 20/20,
- ręcznie przejrzane przypadki: 20,
- testy automatyczne po rozszerzeniu: 11/11.

W pilocie audyt wykrył dokładne duplikaty oraz zbyt generyczne checklisty
ujawnień. Oba problemy usunięto przed wygenerowaniem pełnego zbioru.

## Długość danych

Dla tokenizera Qwen3:

- średnia długość pełnego przykładu: 963 tokeny,
- p95: 1065 tokenów,
- maksimum: 1124 tokeny,
- train, jedna epoka: 384 800 tokenów,
- train, trzy epoki: około 1,15 mln tokenów.

W praktyce konfiguracja `max_seq_length=1152` obejmie wszystkie przypadki, a
`1024` obejmie większość i może wymagać kontrolowanego skrócenia części wejść.
Na pierwsze testy QLoRA rekomendowane jest 1152 lub 1280 tokenów.

## Ważne ograniczenie metodologiczne

Zbiór powstał z kontrolowanych szablonów. Split testowy jest użyteczny do
regresji i porównania konfiguracji, ale nie może być jedynym dowodem
generalizacji. W Sprincie 4 wyniki zostaną uzupełnione o ręcznie przygotowany
benchmark diagnostyczny, przypadki adversarial oraz analizę jakościową.

## Artefakty

- `data/generated/dataset_v1.jsonl`,
- `data/generated/dataset_v1/*.jsonl`,
- `data/DATASET_CARD.md`,
- `data/dataset_registry.json`,
- `data/reviews/dataset_v1_pilot_review.md`,
- `results/dataset_v1_audit.json`,
- `results/dataset_v1_audit.md`,
- `results/dataset_v1_token_stats.json`.

## Decyzja M1

Dataset zostaje zamrożony. Zmiana złotych odpowiedzi, generatora albo splitów
wymaga nowej wersji danych i ponownego uruchomienia pełnego audytu.

Następny etap: **Sprint 2 — baseline Qwen3-4B**.

