# Sprint 6 — plan zamknięcia Protected Evidence i wydania warsztatu

**Status:** S6.5A zaakceptowane przez właściciela. S6.5B zakończone
`EVIDENCE_V1_CLOSED_READ_ONLY`. Następny etap: S6.5C.

## 1. Stan faktyczny na wejściu

Projekt nie wymaga już treningu ani kolejnego evidence runu. Stan jest następujący:

- G0, G1 i G2.1: PASS,
- protected evidence zostało jawnie autoryzowane i skonsumowane w jednym runie,
- wykonano 870/870 inferencji na trzech seedach,
- `protected_splits_opened=true`, `retuning_after_evidence=false`,
- primary: `FAILED_EVIDENCE_THRESHOLDS`,
- shadow: `FAILED_SHADOW_THRESHOLDS`,
- assisted review: 60/60 primary oraz 150/150 shadow,
- 11 krytycznych odpowiedzi primary i 2 krytyczne shadow,
- wynik i review są zacommitowane w `699fa6b`,
- 89 testów przechodzi.

Nie próbujemy już „uratować wyniku” w ramach Evidence v1. Ratujemy i wzmacniamy wartość szkolenia przez uczciwą analizę tego wyniku.

## 2. Co dokładnie oznacza stan Protected Evidence

Protected Evidence v1 nie jest już zbiorem niewidzianym. Jego docelowy status powinien brzmieć:

**`CONSUMED_FROZEN_READ_ONLY_FAILED_THRESHOLDS`**

To oznacza:

1. zachowujemy niezmienione wejścia, goldy, progi, wyniki i raporty,
2. nie uruchamiamy ponownie Evidence v1 po zmianie modelu, promptu lub guarda,
3. nie poprawiamy goldów na podstawie odpowiedzi modelu,
4. nie wybieramy najlepszego seeda,
5. wolno analizować błędy i pokazywać je podczas warsztatu,
6. Evidence v1 może później służyć jako zbiór diagnostyczny/regresyjny, ale nie jako niezależny test nowej wersji,
7. nowa wersja Q1.1/Q2.1 wymaga nowego, wcześniej niewidzianego Evidence v2.

Nie zmieniamy historycznego kontraktu G0 ani approval. Tworzymy osobny artefakt zamknięcia, który wiąże hashami approval, autoryzację, wyniki i końcowy review.

## 3. Plan wykonawczy

### S6.5A — akceptacja sposobu wykorzystania wyniku

**Odpowiedzialność:** właściciel projektu.  
**Model wspierający:** Sol/high.  
**Czas:** 15–30 minut.

Właściciel akceptuje trzy stwierdzenia:

- Evidence v1 nie przeszło zamrożonych progów,
- wynik zostanie pokazany jako jawny case dydaktyczny,
- adapter nie będzie opisywany jako rozwiązanie produkcyjne.

Akceptacja nie zatwierdza jakości modelu i nie daje zgody na rerun. Pozwala jedynie przejść do finalizacji warsztatu.

**Artefakt:** `results/sprint6/m6_owner_acceptance.json`, wiążący commit `699fa6b` i hashe raportów.

**Bramka:** `OWNER_ACCEPTED_FAILED_EVIDENCE_AS_WORKSHOP_CASE`.

**Wynik:** PASS — jawna akceptacja właściciela z 30 sierpnia 2026 r. została
zapisana jako osobny artefakt i nie jest zgodą produkcyjną.

### S6.5B — operacyjne zamknięcie Evidence v1

**Wykonanie:** Luna/low.  
**Review:** Sol/high.  
**Czas:** 30–60 minut.

- utworzyć `results/sprint6/protected_evidence_v1_closure.json`,
- zapisać `CONSUMED_FROZEN_READ_ONLY_FAILED_THRESHOLDS`,
- związać hashami approval, authorization, evidence summary, oba review i commit inferencji,
- potwierdzić brak retuningu i brak drugiego runu,
- dodać test, że artefakt zamknięcia nie może deklarować PASS przy obecnym summary,
- nie modyfikować zamrożonego kontraktu ani approval.

**Bramka:** `EVIDENCE_V1_CLOSED_READ_ONLY`.

**Wynik:** PASS — 37 artefaktów wejściowych i wynikowych związano hashami;
rerun, retuning oraz production approval są jawnie zabronione.

### S6.5C — pakiet dydaktyczny „wynik kontra bezpieczeństwo”

**Projekt narracji:** Sol/high.  
**Walidacja/renderowanie:** Luna/low.  
**Czas:** 2–4 godziny.

Najpierw sprawdzamy, czy obecny deck ma odpowiednie miejsce. Domyślnie nie naruszamy zamrożonego, 53-slajdowego decku — tworzymy osobny, wersjonowany appendix lub handout. Włączenie wyniku do głównego decku wymaga jawnej decyzji właściciela.

Pakiet powinien zawierać cztery ekrany/slajdy:

1. **Metodologia:** primary vs risk-directed shadow, trzy seedy, zakaz retuningu.
2. **Pozornie dobry obraz:** original macro-F1 0,971; boundary 1,0; schema/source integrity 1,0.
3. **Co ukrywa agregacja:** challenge accuracy 0,70, severity 0,617, 11 false-assurance/injection PASS; shadow `INSUFFICIENT_DATA` recall 0,60.
4. **Wniosek bankowy:** Q1 proponuje; deterministic/source guard blokuje; człowiek zatwierdza; brak zgody produkcyjnej.

Do tego powstaje:

- karta prowadzącego z pytaniami do uczestników,
- jeden przypadek primary i jeden shadow do wspólnej analizy,
- jasne rozróżnienie „model quality”, „system safety” i „business readiness”,
- fallback w postaci statycznych wyników — bez ponownego uruchamiania evidence.

**Bramka:** wszystkie liczby są zgodne z `evidence_summary.json`, a narracja nie sugeruje production readiness.

### S6.6A — automatyczna próba techniczna

**Model:** Luna/low.  
**Czas:** 1–2 godziny.

- uruchomić pełne testy,
- sprawdzić trzy notebooki w trybie demonstracyjnym bez treningu,
- sprawdzić pracę offline/cache i fallbacki,
- zweryfikować wszystkie ścieżki do plików i materiały statyczne,
- potwierdzić, że żaden krok warsztatu nie wywołuje protected evidence runu,
- przygotować kartę „jeśli demo nie działa” dla prowadzącego.

**Bramka:** testy PASS, notebooki PASS, offline PASS, protected runner nie jest elementem live demo.

### S6.6B — pełny dry-run prowadzącego

**Wykonanie:** człowiek/prowadzący.  
**Monitoring i analiza czasu:** Luna/low.  
**Review treści po próbie:** Sol/high.  
**Czas:** 3 godziny + około 1 godziny analizy.

Prowadzący przechodzi szkolenie tak, jak przed uczestnikami. Rejestrujemy:

- czas rozpoczęcia i zakończenia każdej sekcji,
- czas pytań i ćwiczeń,
- momenty przełączenia na fallback,
- problemy osobno jako: treść, czas, technika,
- fragmenty, które wymagają skrócenia lub dopowiedzenia.

Dry-run przechodzi, gdy całość trwa 175–185 minut i nie wymaga live treningu ani live protected evidence.

Ta część nie może być wiarygodnie zastąpiona przez model — agent może przygotować scenariusz, mierzyć i analizować, ale prowadzący musi fizycznie wygłosić próbę.

### S6.6C — korekta po dry-runie

**Proste poprawki i walidacja:** Luna/low.  
**Zmiany narracyjne i końcowy review:** Sol/high.  
**Czas:** 2–4 godziny.

Dozwolone:

- korekty czasu, literówek, niedziałających ścieżek i instrukcji,
- skrócenie lub przesunięcie ćwiczenia,
- doprecyzowanie narracji protected evidence,
- aktualizacja trainer guide i fallbacków.

Niedozwolone:

- retuning pod Evidence v1,
- zmiana goldów lub progów,
- ukrycie krytycznych przypadków,
- ponowne przedstawienie Evidence v1 jako niewidzianego testu.

### S6.7 — M6 i wydanie `workshop-v1.0`

**Końcowy review:** Sol/high.  
**Mechaniczny release:** Luna/low.  
**Czas:** 1–2 godziny.

- potwierdzić owner acceptance i PASS dry-runu,
- uruchomić końcowe testy i walidację notebooków,
- wygenerować release manifest z hashami materiałów, notebooków, adapterów i raportów,
- zapisać `M6_WORKSHOP_READY_NOT_FOR_PRODUCTION`,
- wykonać commit i push,
- utworzyć tag `workshop-v1.0` dopiero po spełnieniu wszystkich bramek.

## 4. Co pozostanie po wydaniu

Po `workshop-v1.0` projekt ma dwa możliwe kierunki:

- **zakończenie projektu szkoleniowego** — rekomendowane teraz;
- **osobny projekt badawczy Q1.1/Q2.1** — poprawa odporności na injection i `INSUFFICIENT_DATA`, trening wyłącznie na train/dev oraz nowe Evidence v2 zaprojektowane i zamrożone przed inferencją.

Drugi kierunek nie jest potrzebny do ukończenia obecnego warsztatu.

## 5. Szacowany czas do końca

Od akceptacji właściciela:

| Etap | Czas |
|---|---:|
| Akceptacja i zamknięcie Evidence v1 | 1–1,5 h |
| Pakiet dydaktyczny evidence | 2–4 h |
| Próba techniczna | 1–2 h |
| Dry-run prowadzącego | 3 h |
| Analiza i korekty | 3–5 h |
| Release M6 | 1–2 h |
| **Łącznie** | **10–17,5 h, zwykle 2 dni pracy** |

## 6. Najbliższa decyzja

Następny krok nie dotyczy modelu ani treningu. Właściciel powinien zatwierdzić:

**„Akceptuję `FAILED_EVIDENCE_THRESHOLDS` jako jawny case dydaktyczny do warsztatu, bez zgody produkcyjnej i bez rerunu Evidence v1.”**

Po tej decyzji można od razu wykonać S6.5B i S6.5C.
