# Roadmapa przygotowania szkolenia

## Etap 1 — fundament projektu

Status: ukończony

- specyfikacja szkolenia,
- definicja głównego przypadku,
- schemat danych i odpowiedzi,
- plan benchmarku,
- kryteria sukcesu.

Rezultat: wiadomo dokładnie, czego uczymy i jak zmierzymy wynik.

## Etap 2 — minimalny benchmark bez fine-tuningu

Status: ukończony — `baseline-v1.0.0`, M2 Baseline freeze

- stworzenie fikcyjnego mini-sprawozdania,
- przygotowanie 30–50 przypadków kontrolnych,
- walidacja schematu danych,
- notebook z inferencją zero-shot i few-shot,
- parser oraz walidator JSON,
- pierwsza tabela błędów modelu bazowego.

Rezultat: mierzalny baseline i materiał otwierający wykład.

## Etap 3 — dane warsztatowe

Status: ukończony — `dataset-v1.0.0`, M1 Data freeze

- generator wariantów liczbowych i tekstowych,
- generator kontrolowanych niezgodności,
- ręcznie napisane trudne przypadki,
- deduplikacja i kontrola podobieństwa,
- grupowy podział train/validation/test,
- karta danych oraz rejestr pochodzenia przykładów.

Rezultat: zestaw nadający się do uczciwego treningu i ewaluacji.

## Etap 3.5 — granice etykiet

Status: warunkowo zaakceptowany 26 sierpnia 2026 — gotowy do rozpoczęcia
Sprintu 3 po 21:00.

- polityka `PASS/WARN/FAIL/INSUFFICIENT_DATA/NOT_APPLICABLE`,
- macierz stosowalności kontroli,
- 540 przypadków w minimalnych parach,
- osobny boundary train/development/validation/test,
- B3 label-complete i formalna ocena validation,
- review, rejestr warunkowej akceptacji i jawne ograniczenia wykorzystania.

Rezultat: mierzalne granice decyzji i uczciwy kontrakt dla adaptera.

## Etap 4 — pipeline LoRA/QLoRA

Status: ukończony 27 sierpnia 2026 — M3 PASS, Q1 jako `adapter-v0.1` candidate

- wybór i przypięcie modelu,
- konfiguracja LoRA BF16,
- konfiguracja QLoRA NF4,
- trening kontrolny bez boundary pack oraz główny trening z boundary pack,
- trening, checkpointing i logowanie,
- zapis, ładowanie i scalanie adaptera,
- test na docelowym GPU.

Rezultat: powtarzalny trening oraz gotowy adapter demonstracyjny.

## Etap 5 — pełny benchmark

Status: replikacja ukończona; `CONDITIONAL_HOLD_BEFORE_PROTECTED_EVIDENCE` po
review z 28 sierpnia 2026. Przed testami wymagany Evidence Gate Hardening.

- zamrożone B3/Q0 oraz trzy seedy Q1 bez wyboru najlepszego,
- Q2 jako eksperyment z kontrolami deterministycznymi,
- jawny backlog L1/Q1b/Q3 po zamknięciu evidence package,
- metryki techniczne,
- metryki granic, minimalnych par i kosztu błędu,
- testy adversarial i regresyjne,
- ślepa ocena wybranych odpowiedzi,
- katalog najlepszych i najgorszych przykładów.

Rezultat: dane do wykresów, slajdów i dyskusji biznesowej.

## Etap 6 — materiały szkoleniowe

- slajdy uczestnika,
- rozszerzone notatki prowadzącego,
- notebook demonstracyjny,
- skrócona ściąga LoRA/QLoRA,
- karta zastosowań bankowych,
- pytania kontrolne i odpowiedzi,
- dodatkowe ćwiczenia po szkoleniu.

Rezultat: kompletny pakiet dydaktyczny.

## Etap 7 — próba generalna

- czyste środowisko i ponowna instalacja,
- pełne przejście demonstracji,
- pomiar czasu każdego segmentu,
- symulacja braku internetu i awarii treningu,
- korekta materiału do dokładnie 180 minut.

Rezultat: szkolenie gotowe do przeprowadzenia.

## Następne zadanie

Sprinty 4.2A i 4.2B zostały zakończone. Sprint 4.2C blokuje stabilny błąd
decyzji liczbowej FC-209 we wszystkich seedach i ma status
`READY_FOR_SPRINT5_DEMO_WITH_PROTECTED_HOLD`. Następny krok to Sprint 5:
przygotowanie materiałów szkoleniowych pokazujących zarówno poprawę promptu v2,
jak i potrzebę hybrydowej architektury LLM + deterministic guard + human review.
Protected splits pozostają zamknięte.

M3 nie jest zgodą produkcyjną. Przed użyciem poza warsztatem wymagane są
niezależny sign-off ekspercki, dane zatwierdzone przez bank i governance.

Szczegóły: [`13_sprint_4_executive_plan.md`](13_sprint_4_executive_plan.md).
Review: [`14_sprint_4_analytical_review.md`](14_sprint_4_analytical_review.md).
Sprint 4.2A: [`15_sprint_4_2a_executive_plan.md`](15_sprint_4_2a_executive_plan.md).
Sprint 4.2B: [`16_sprint_4_2b_error_analysis_and_rerun_plan.md`](16_sprint_4_2b_error_analysis_and_rerun_plan.md).
Sprint 4.2C: [`17_sprint_4_2c_deterministic_guard.md`](17_sprint_4_2c_deterministic_guard.md).
