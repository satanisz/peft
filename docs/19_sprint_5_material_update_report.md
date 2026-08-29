# Sprint 5 — raport aktualizacji materiałów

**Data:** 29 sierpnia 2026  
**Status:** `READY_FOR_M5_CONTENT_FREEZE_REVIEW_WITH_PROTECTED_HOLD`

## Wynik

Pakiet szkoleniowy został zaktualizowany o wynik rzeczywistego Q1-DEMO i fresh
reloadu. Materiały zachowują rozdział między demonstracją pipeline, jakością
adaptera, bezpieczeństwem systemu i gotowością produkcyjną.

## Zmiany w talii

- slajd 34: 12 kroków, 114,361 s, 7,487 GiB, zero truncation, reload 1/1,
- slajd 37: rzeczywiste porównanie wag adapterów rank 8 i rank 16 — 33,1 vs 66,1 MB,
- slajd 40: przypadek 128 vs 384 tokeny jako lekcja kontraktu generacji,
- zaktualizowane notatki i źródła repozytoryjne bez zmiany agendy 180 minut.

Talia nadal zawiera 53 slajdy. Każdy ma notatki prowadzącego i blok `[Sources]`.

## Nowe materiały

- ściąga LoRA/QLoRA i kontrakt benchmarku,
- karty ćwiczeń oraz osobny klucz prowadzącego,
- FAQ i troubleshooting z twardym limitem 15 minut,
- katalog zastosowań bankowych,
- checklista prowadzącego,
- trzy notebooki: dobór metody i dane, QLoRA demo, benchmark i guard.

Notebook treningowy jest bezpieczny domyślnie: `RUN_TRAINING=False`. Pozostałe
notebooki czytają tylko jawne dane train/validation, raporty i artefakty; nie
otwierają protected splits.

## Walidacja

- 53 slajdy, 53 zestawy notatek, 53 bloki źródeł,
- test przepełnienia slajdów: PASS,
- wizualny review całej talii oraz osobno slajdów 34, 37 i 40: PASS,
- trzy notebooki poprawne składniowo i wykonane bez treningu: PASS,
- 65 testów projektu: PASS,
- `git diff --check`: PASS.

## Decyzja i ograniczenia

Rekomendacja: właściciel może zaakceptować M5 Content freeze po krótkim review
treści. Kolejny etap to Sprint 6: próba od czystego środowiska i pełny dry-run
180 minut z pomiarem czasu oraz symulacją fallbacku.

Protected evidence pozostaje `HOLD`. Materiał wykorzystuje dane syntetyczne i
nie stanowi zgody produkcyjnej ani polityki banku.
