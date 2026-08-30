# S6.7 — handoff mechanicznego release'u dla Luna/low

## Cel

Wydać `workshop-v1.0` jako **warsztat gotowy, nie rozwiązanie produkcyjne**.
Nie uruchamiać treningu, protected evidence ani rerunu Evidence v1.

## Warunek wejścia

Przed rozpoczęciem operator musi podać rzeczywisty czas pełnego dry-runu
prowadzącego. Jeżeli dry-run nie został fizycznie wygłoszony albo czas nie
mieści się w 175–185 minutach, zakończ pracę decyzją
`M6_RELEASE_HOLD_DRY_RUN_DURATION` i nie twórz tagu.

## Zadania

1. Utwórz `results/sprint6/s6_6b_dry_run_attestation.json` z datą, osobą
   prowadzącą, czasem całkowitym, wykonanymi aktami/ćwiczeniami, informacją o
   fallbackach, trzech kategoriach problemów oraz potwierdzeniem braku live
   treningu i live protected evidence.
2. Zaakceptuj `S6_6B_PASS` tylko dla kompletnej próby trwającej 175–185 minut.
3. Uruchom pełny `unittest` oraz trzy notebooki bez treningu. Zachowaj
   `RUN_TRAINING=False`.
4. Zweryfikuj integralność głównego decku, appendixu, guide'a, adaptera,
   raportów Evidence v1 oraz artefaktów S6.5–S6.6.
5. Wygeneruj `results/sprint6/workshop_v1_release_manifest.json`. Dla każdego
   wydawanego pliku zapisz ścieżkę, rozmiar i SHA-256; manifest ma wiązać także
   commit źródłowy i wynik testów.
6. Utwórz `results/sprint6/m6_workshop_release.json` z decyzją
   `M6_WORKSHOP_READY_NOT_FOR_PRODUCTION`. Jawnie zapisz:
   `production_approval=false`, `evidence_v1_rerun_allowed=false` oraz
   `retuning_on_evidence_v1_allowed=false`.
7. Dodaj testy integralności manifestu, M6 i ograniczeń Evidence v1.
8. Wykonaj finalny `git diff --check`, testy i sprawdzenie czystego statusu po
   commicie.
9. Wykonaj commit i push do `main`.
10. Dopiero po PASS wszystkich powyższych kroków utwórz annotated tag
    `workshop-v1.0` i wypchnij go do remote `github`.

## Twarde zakazy

- nie uruchamiaj `scripts/run_sprint4_evidence.ps1`;
- nie zmieniaj goldów, progów ani zamrożonych wyników;
- nie uruchamiaj treningu;
- nie opisuj adaptera jako rozwiązania produkcyjnego;
- nie twórz tagu przy warunkowym albo niepełnym wyniku S6.6B.

## Raport końcowy

Podaj: decyzję M6, liczbę testów, czas dry-runu, hash manifestu, commit release,
status push oraz status tagu. W przypadku HOLD podaj dokładnie jedną lub więcej
niespełnionych bramek i nie obchodź ich zmianą kryteriów.
