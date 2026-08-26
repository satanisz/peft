# Parameter-Efficient Fine-Tuning — warsztat

Materiały do trzygodzinnego, technicznego szkolenia o PEFT, LoRA i QLoRA,
zbudowanego wokół zastosowań bankowych.

## Założenia

- grupa: 15 osób na poziomie średniozaawansowanym,
- forma: wykład połączony z demonstracją prowadzoną przez prowadzącego,
- główny przypadek: `Financial Control Copilot`,
- przykład uzupełniający: `BankAssist-PL`,
- język materiałów i danych: polski,
- nacisk: implementacja, eksperymenty, benchmarki oraz wartość biznesowa,
- dodatkowa warstwa materiałów: pogłębione notatki dla prowadzącego.

## Dokumenty projektowe

- [Uruchomienie projektu](docs/00_how_to_run.md)
- [Plan szkolenia](docs/01_training_blueprint.md)
- [Financial Control Copilot](docs/02_financial_control_copilot.md)
- [Plan eksperymentów i benchmarku](docs/03_experiment_plan.md)
- [Roadmapa przygotowania materiałów](docs/04_roadmap.md)
- [Pierwsze wyniki baseline](docs/05_baseline_results.md)
- [Executive plan i sprinty](docs/06_executive_plan.md)
- [Zasady współpracy w Git](CONTRIBUTING.md)
- [Karta dataset-v1](data/DATASET_CARD.md)
- [Raport Sprintu 1](docs/07_sprint_1_report.md)
- [Raport Sprintu 2 — baseline Qwen3-4B](docs/08_sprint_2_report.md)
- [Executive plan Sprintu 2.5 — Label Boundary Hardening](docs/09_sprint_2_5_executive_plan.md)
- [Raport Sprintu 2.5 — wyniki B1/B2/B3](docs/10_sprint_2_5_report.md)

## Planowane artefakty

```text
data/                 dane źródłowe, wygenerowane i podziały benchmarkowe
notebooks/            demonstracje od baseline'u do QLoRA
src/                  generowanie danych, trening i ewaluacja
configs/              jawne konfiguracje eksperymentów
results/              wyniki, wykresy i przykłady błędów
slides/               slajdy i notatki prowadzącego
trainer_guide/        scenariusz, pytania, troubleshooting i plan awaryjny
```

## Najbliższy kamień milowy

Sprint 2.5 został warunkowo zaakceptowany do celów warsztatowych. Boundary
pack zawiera 540 przypadków, a B3 osiągnął macro-F1 0,894 na boundary
validation. Sprint 3 (Q0/Q1) rozpocznie się po 21:00; formalne zamrożenie
`boundary-pack-v1.0.0` dla użycia poza warsztatem wymaga niezależnego review
eksperckiego.
