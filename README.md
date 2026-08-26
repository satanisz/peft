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

Sprint 2 zakończył się zamrożeniem baseline'u Qwen3-4B. Następnym kamieniem
milowym jest działający adapter QLoRA NF4 mieszczący się w 12 GB VRAM i
poprawiający co najmniej część metryk validation względem B1.
