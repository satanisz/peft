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

Status: ukończony dla profilu smoke; docelowy baseline 4B pozostaje częścią
etapu 5.

- stworzenie fikcyjnego mini-sprawozdania,
- przygotowanie 30–50 przypadków kontrolnych,
- walidacja schematu danych,
- notebook z inferencją zero-shot i few-shot,
- parser oraz walidator JSON,
- pierwsza tabela błędów modelu bazowego.

Rezultat: mierzalny baseline i materiał otwierający wykład.

## Etap 3 — dane warsztatowe

Status: następny

- generator wariantów liczbowych i tekstowych,
- generator kontrolowanych niezgodności,
- ręcznie napisane trudne przypadki,
- deduplikacja i kontrola podobieństwa,
- grupowy podział train/validation/test,
- karta danych oraz rejestr pochodzenia przykładów.

Rezultat: zestaw nadający się do uczciwego treningu i ewaluacji.

## Etap 4 — pipeline LoRA/QLoRA

- wybór i przypięcie modelu,
- konfiguracja LoRA BF16,
- konfiguracja QLoRA NF4,
- trening, checkpointing i logowanie,
- zapis, ładowanie i scalanie adaptera,
- test na docelowym GPU.

Rezultat: powtarzalny trening oraz gotowy adapter demonstracyjny.

## Etap 5 — pełny benchmark

- B0/B1/B2/L1/Q1/Q2/Q3,
- trzy seedy dla głównych wariantów,
- metryki techniczne,
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

Zbudować etap 3: generator większego zbioru treningowego, warianty językowe i
liczbowe, kontrolę duplikatów oraz grupowy podział danych. Obecne 40 przypadków
pozostaje małym zbiorem diagnostycznym i nie powinno zostać mechanicznie
powielone do treningu.
