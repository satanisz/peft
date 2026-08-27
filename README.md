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
- [Scenariusz demonstracyjny Sprintu 3](docs/11_sprint_3_training_scenario.md)
- [Raport Sprintu 3 — QLoRA i M3](docs/12_sprint_3_report.md)
- [Zrewidowany executive plan Sprintu 4](docs/13_sprint_4_executive_plan.md)
- [Analityczny review Sprintu 4](docs/14_sprint_4_analytical_review.md)

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

Sprint 3 zakończył się decyzją M3 PASS. Q1 osiągnął macro-F1 1,000 oraz 100%
poprawności 60 minimalnych par na boundary validation, zachowując macro-F1
1,000 na oryginalnym validation i redukując input tokens o 51,6% względem B3.
Q1 jest kandydatem `adapter-v0.1` do pełnego benchmarku Sprintu 4. Wyniki są
syntetyczne i jednoseedowe; testy oraz challenge pozostają zamknięte, a użycie
poza warsztatem wymaga niezależnego review eksperckiego.

Replikacja Sprintu 4 została ukończona dla trzech seedów. Review z 28 sierpnia
2026 wstrzymał otwarcie test/challenge do czasu zbudowania diagnostic setu poza
szablonami, Q2/source integrity guard i ponownej decyzji Sol/high.
