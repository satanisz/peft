# S6.7 — końcowy review Sol/high

**Historyczny review formatu warsztatowego.** Późniejsza decyzja właściciela
zmieniła produkt na wykład 60-minutowy. Dawna bramka czasu nie blokuje tego
wydania; obowiązuje [plan S6.7-L](37_lecture60_delivery_plan.md).
Nie zmieniamy historii próby i nie deklarujemy wstecznego PASS.

Data review: 2026-08-30  
Decyzja: **M6_RELEASE_HOLD_DRY_RUN_DURATION_ONLY**

## Wynik

Projekt jest technicznie gotowym kandydatem do wydania `workshop-v1.0`.
Jedyną niespełnioną bramką jest potwierdzenie pełnego czasu próby prowadzącego.
Nie utworzono artefaktu M6 ani tagu release przed spełnieniem tej bramki.

## Bramki zakończone

- owner acceptance: `OWNER_ACCEPTED_FAILED_EVIDENCE_AS_WORKSHOP_CASE`;
- Evidence v1: `CONSUMED_FROZEN_READ_ONLY_FAILED_THRESHOLDS`;
- Evidence v1 pozostaje bez rerunu, retuningu i zgody produkcyjnej;
- pakiet dydaktyczny S6.5C oraz presenter guide są kompletne;
- S6.6A: PASS;
- pełny test suite: 91/91 PASS;
- trzy notebooki: poprawny JSON i wykonanie bez treningu potwierdzone w S6.6A;
- główny deck i appendix: poprawne pakiety PowerPoint;
- model i adapter: lokalny cache, komplet wag oraz fallbacki PASS;
- użytkownik potwierdził, że sekcje uruchamiają się natychmiastowo i bez
  problemów technicznych.

## Otwarta bramka

Potwierdzenie technicznego uruchomienia sekcji nie zastępuje pełnego dry-runu
prowadzącego. M6 wymaga fizycznego wygłoszenia szkolenia i zapisania czasu
całkowitego w przedziale **175–185 minut**.

Minimalny artefakt S6.6B musi zawierać:

- datę próby i prowadzącego;
- całkowity czas w minutach;
- informację, czy wykonano wszystkie akty, pytania i ćwiczenia;
- potwierdzenie braku live treningu i live protected evidence;
- liczbę problemów technicznych, czasowych i treściowych;
- decyzję `S6_6B_PASS` wyłącznie dla czasu 175–185 minut.

## Zakres do delegowania na Luna/low

Po uzyskaniu prawdziwego wyniku S6.6B Luna/low może mechanicznie:

1. zapisać i zwalidować artefakt dry-runu;
2. wykonać końcowe testy oraz notebook rehearsal;
3. wygenerować release manifest z SHA-256;
4. zapisać `M6_WORKSHOP_READY_NOT_FOR_PRODUCTION`;
5. wykonać commit i push;
6. utworzyć i wypchnąć tag `workshop-v1.0` tylko przy komplecie bramek.

Instrukcja wykonawcza znajduje się w
`docs/35_sprint_6_7_luna_low_release_handoff.md`.
