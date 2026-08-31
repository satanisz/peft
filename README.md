# Parameter-Efficient Fine-Tuning — wykład i materiały warsztatowe

Aktualny produkt: wykład 60-minutowy o PEFT, LoRA i QLoRA, oparty na własnym
eksperymencie Financial Control Copilot. Bez notebooków i treningu na żywo.
Oryginalny trzygodzinny warsztat pozostaje zachowany jako materiał dodatkowy.

- [Narracja wykładu i notatki prowadzącego](materials/lecture60_presenter_guide.md)
- [Zweryfikowany przebieg treningów](docs/36_lecture60_training_review.md)
- [Aktualny plan wykonania i wydania wykładu](docs/37_lecture60_delivery_plan.md)
- [Sprint 7 — Q2 i Evidence v2](docs/39_sprint_7_q2_evidence_v2_executive_plan.md)
- [Wynik S7.0–S7.1 — baseline i remediation](docs/40_sprint_7_0_7_1_baseline_and_remediation_report.md)
- [Projekt S7.2 i handoff dla Luna/low](docs/41_sprint_7_2_design_and_luna_handoff.md)

Deck 60-minutowy jest złożony i przeszedł pełny render oraz QA.
Protected Evidence v1 pozostaje FAILED/FROZEN/READ-ONLY, bez rerunu i bez
zgody produkcyjnej.

## Założenia

- grupa: 15 osób na poziomie średniozaawansowanym,
- forma bieżąca: wykład 60 minut, wyniki i konfiguracje wyłącznie na slajdach,
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
- [Raport authoringu S6-G1 Shadow freeze](docs/22_sprint_6_g1_authoring_report.md)
- [Karta shadow-challenge-v1](data/shadow/SHADOW_DATASET_CARD.md)
- [Raport S6-G2 Technical readiness](docs/23_sprint_6_g2_technical_readiness_report.md)
- [G2.1A — hardening approval, runnera i raportowania](docs/24_sprint_6_g2_1a_contract_hardening.md)
- [Raport G2.1B — rzeczywisty offline i fallback](docs/25_sprint_6_g2_1b_technical_hardening_report.md)
- [Końcowe review G0/G1/G2.1](docs/26_sprint_6_final_g0_g1_g2_1_review.md)
- [Plan odzyskania jakości Q2 / Evidence v2](docs/39_sprint_7_q2_evidence_v2_executive_plan.md)
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

Wykład 60-minutowy i pakiet QA są gotowe. Evidence v1 wykonano i zamknięto jako
`FAILED / FROZEN / READ-ONLY`; wynik jest częścią case study, a nie zgodą
produkcyjną. Następny opcjonalny projekt to Sprint 7: najpierw diagnoza oraz
system-first ablation, następnie — tylko po przejściu bramek train/dev — Q2 i
nowe, wcześniej niewidziane Evidence v2. Najbliższy krok wykonuje Sol/high:
S7.0 + S7.1.
