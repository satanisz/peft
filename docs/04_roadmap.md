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

Status: `M5_ACCEPTED_CONTENT_FREEZE_WITH_PROTECTED_HOLD` — zaakceptowany przez
właściciela 29 sierpnia 2026. Trening Q1-DEMO i fresh reload zakończyły się
poprawnie; 53 slajdy zawierają rzeczywiste metryki, a pakiet pomocniczy i trzy
notebooki są gotowe. Pełny dry-run 180 minut należy do Sprintu 6.

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

S6-G0 zakończyło się PASS: kontrakt dowodowy, progi i hashe adapterów są
zamrożone, a protected evidence nie zostało odczytane. Następnie tworzymy i
recenzujemy 50 nowych przypadków shadow challenge do bramki S6-G1. Protected
splits można otworzyć dopiero po PASS G1/G2, osobnej decyzji Sol/high i jawnym
potwierdzeniu operatora.

M3 nie jest zgodą produkcyjną. Przed użyciem poza warsztatem wymagane są
niezależny sign-off ekspercki, dane zatwierdzone przez bank i governance.

Szczegóły: [`13_sprint_4_executive_plan.md`](13_sprint_4_executive_plan.md).
Review: [`14_sprint_4_analytical_review.md`](14_sprint_4_analytical_review.md).
Sprint 4.2A: [`15_sprint_4_2a_executive_plan.md`](15_sprint_4_2a_executive_plan.md).
Sprint 4.2B: [`16_sprint_4_2b_error_analysis_and_rerun_plan.md`](16_sprint_4_2b_error_analysis_and_rerun_plan.md).
Sprint 4.2C: [`17_sprint_4_2c_deterministic_guard.md`](17_sprint_4_2c_deterministic_guard.md).
Sprint 5: [`19_sprint_5_material_update_report.md`](19_sprint_5_material_update_report.md).
Sprint 6: [`20_sprint_6_executive_plan.md`](20_sprint_6_executive_plan.md).
S6-G0: [`21_sprint_6_g0_report.md`](21_sprint_6_g0_report.md).
