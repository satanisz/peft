# Raport QA datasetu

Źródło: `C:/Users/stani/Projects/peft/data/pilot/dataset_v1_pilot.jsonl`

Status: **PASS**

## Podsumowanie

- rekordy: 120
- rodziny scenariuszy: 120
- rodzaje mutacji: 50
- dokładne duplikaty: 0
- rodziny przeciekające między splitami: 0
- SHA-256: `cab57746177befb7f3a2afabd8512e74ad9d2a7f06de00743eb5fb9fb20117c3`

## Splity

| Split | Liczba |
|---|---:|
| development | 10 |
| test | 20 |
| train | 80 |
| validation | 10 |

## Statusy

| Status | Liczba |
|---|---:|
| FAIL | 37 |
| INSUFFICIENT_DATA | 24 |
| NOT_APPLICABLE | 2 |
| PASS | 43 |
| WARN | 14 |

## Typy kontroli

| Typ | Liczba |
|---|---:|
| ARITHMETIC | 12 |
| CROSS_SECTION | 12 |
| CURRENCY | 12 |
| DIRECTION | 12 |
| DISCLOSURE | 12 |
| EVIDENCE | 12 |
| INSUFFICIENT_DATA | 12 |
| PERIOD | 12 |
| UNIT | 12 |
| VARIANCE | 12 |

## Błędy

- Brak.

## Ostrzeżenia

- Split train zawiera mniej niż docelowe 400 przypadków
