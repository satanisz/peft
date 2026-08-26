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

Status: można rozpocząć po 21:00 na podstawie warunkowej akceptacji M2.5

- wybór i przypięcie modelu,
- konfiguracja LoRA BF16,
- konfiguracja QLoRA NF4,
- trening kontrolny bez boundary pack oraz główny trening z boundary pack,
- trening, checkpointing i logowanie,
- zapis, ładowanie i scalanie adaptera,
- test na docelowym GPU.

Rezultat: powtarzalny trening oraz gotowy adapter demonstracyjny.

## Etap 5 — pełny benchmark

- B0/B1/B2/B3/L1/Q0/Q1/Q1b/Q2/Q3,
- trzy seedy dla głównych wariantów,
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

Po 21:00 rozpocząć Sprint 3 od preflightu QLoRA oraz konfiguracji Q0 i Q1.
Przed użyciem poza warsztatem wymagany jest niezależny sign-off ekspercki i
formalna decyzja o zamrożeniu `boundary-pack-v1.0.0`.
