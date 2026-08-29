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
- [Executive plan Sprintu 4.2A](docs/15_sprint_4_2a_executive_plan.md)
- [Analiza błędów i prompt rerun Sprintu 4.2B](docs/16_sprint_4_2b_error_analysis_and_rerun_plan.md)
- [Deterministic guard Sprintu 4.2C](docs/17_sprint_4_2c_deterministic_guard.md)
- [Narracja i scenariusze Sprintu 5](docs/18_sprint_5_narrative_and_scenarios.md)
- [Raport aktualizacji materiałów Sprintu 5](docs/19_sprint_5_material_update_report.md)
- [Executive plan Sprintu 6](docs/20_sprint_6_executive_plan.md)
- [Raport S6-G0 Evidence Contract Freeze](docs/21_sprint_6_g0_report.md)
- [Pakiet materiałów](materials/README.md)

## Planowane artefakty

```text
data/                 dane źródłowe, wygenerowane i podziały benchmarkowe
src/                  generowanie danych, trening i ewaluacja
configs/              jawne konfiguracje eksperymentów
results/              wyniki, wykresy i przykłady błędów
materials/            talia, ściąga, ćwiczenia, FAQ i katalog zastosowań
notebooks/            trzy demonstracje prowadzącego bez auto-startu treningu
```

## Najbliższy kamień milowy

Sprint 5 ma status `M5_ACCEPTED_CONTENT_FREEZE_WITH_PROTECTED_HOLD`.
Q1-DEMO ukończyło 12 kroków w 114,361 s, zapisało adapter rank 8 i przeszło
fresh reload przy limicie 384 tokenów. Talia 53 slajdów, trzy notebooki i pakiet
uczestnika/prowadzącego są zamrożone jako M5 Content freeze.

Sprint 6 obejmuje próbę od czystego środowiska, 50 nowych przypadków shadow
challenge, kontrolowane protected evidence i pełny dry-run 180 minut. Protected
evidence pozostaje zamknięte. S6-G0 ma status PASS; następny krok to authoring i
review shadow challenge do G1. Wyniki dotyczą danych
syntetycznych i nie stanowią zgody produkcyjnej.
