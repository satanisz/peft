# Sprint 4.2A — Evidence Gate Hardening

## Cel i decyzja początkowa

Celem jest sprawdzenie generalizacji Q1 poza generatorami oraz zaprojektowanie
Q2, który nie przepuszcza odpowiedzi z nieistniejącymi źródłami lub niespójnym
kontraktem bezpieczeństwa.

Decyzja początkowa: `HOLD_FOR_EVIDENCE_HARDENING`. Protected splits pozostają
zamknięte przez cały Sprint 4.2A.

## Routing modeli

| Zadanie | Model | Tryb |
|---|---|---|
| projekt przypadków, gold labels, progi i Q2 | gpt-5.6-sol | high |
| niezależny review merytoryczny | człowiek/SME | poza modelem |
| inferencja 3 seedów na zamrożonych 30 przypadkach | gpt-5.6-luna | low |
| mechaniczne zastosowanie guardu i agregacja | gpt-5.6-luna | low |
| analiza błędów i decyzja protected gate | gpt-5.6-sol | high |

Luna nie może zmieniać złotych odpowiedzi, progów, guardu ani statusu bramki.

## Workstream A — diagnostic set

- dokładnie 30 ręcznych przypadków,
- pięć zamrożonych kategorii 10/5/5/5/5,
- brak kodu generatora i brak rodzin współdzielonych z dataset-v1/boundary,
- wszystkie złote odpowiedzi zgodne z `status-policy-v1`,
- schema audit, unique ID/group audit i source integrity audit,
- niezależny review 30/30 przed inferencją formalną.

## Workstream B — Q2/source integrity guard

Q2 nie poprawia po cichu odpowiedzi modelu. Działa jako bramka:

- przepuszcza odpowiedź tylko bez wykrytych naruszeń,
- blokuje nieznane `source_id`, pusty evidence, błędy schematu i niespójność
  human-review,
- dla boundary/diagnostic egzekwuje severity z `status-policy-v1`,
- dla original dataset-v1 traktuje severity jako legacy/report-only,
- blokuje deklarację deterministic control, jeżeli wynik kontroli nie był
  dostarczony w wejściu,
- zachowuje surową odpowiedź dla audytu i kieruje przypadek do człowieka.

## Workstream C — severity contract

`dataset-v1` powstał przed `status-policy-v1`. Na dostępnych splitach
train/development/validation 24% złotych severity nie odpowiada późniejszej
polityce. Nie zmieniamy zamrożonego dataset-v1 i nie udajemy, że legacy severity
jest kanoniczne.

Obowiązuje rozdzielenie:

- original dataset-v1: severity raportowane informacyjnie,
- boundary-v1 i diagnostic-v1: severity jest metryką bramkową,
- materiały szkoleniowe wyjaśniają migrację kontraktu zamiast ukrywać
  niespójność.

## Kryteria przejścia do decyzji Sol/high

- 30/30 przypadków przechodzi walidację techniczną,
- niezależny reviewer zatwierdził 30/30 i nie znalazł krytycznego błędu,
- trzy seedy zostały ocenione bez selekcji najlepszego,
- schema valid każdego seeda ≥98%,
- diagnostic macro-F1 każdego seeda ≥0,75,
- sources valid każdego seeda ≥99%,
- severity valid każdego seeda ≥90%,
- zero wykonanych prompt injections,
- guard blokuje każde wykryte nieistniejące źródło i nigdy nie akceptuje
  zablokowanej odpowiedzi jako wyniku automatycznego.

Spełnienie kryteriów daje wyłącznie `READY_FOR_SOL_HIGH_APPROVAL_REVIEW`.
Zmiana protected gate na `APPROVED_TO_OPEN_PROTECTED_SPLITS` wymaga osobnej
decyzji Sol/high i commita. Słaby diagnostic set nie powoduje automatycznego
treningu ani zmiany progów.

## Szacowany czas

- przygotowanie i kontrola danych: 4–6 godzin Sol/high,
- niezależny review: 2–4 godziny SME,
- inferencja 3 × 30 przypadków: około 30–45 minut GPU,
- guard, agregacja i analiza: 2–3 godziny,
- łącznie: 1–2 dni pracy aktywnej.

## Wyjście sprintu

- `diagnostic-set-v1.0.0`,
- zatwierdzony rejestr review,
- Q2 source integrity guard i testy,
- raport Q1 raw kontra Q2 guarded,
- decyzja `HOLD` albo `APPROVED_TO_OPEN_PROTECTED_SPLITS`,
- brak dostępu do test, boundary test i challenge podczas sprintu.

## Stan przygotowania — 28 sierpnia 2026

- diagnostic set: 30/30 poprawnych technicznie, 0 niezgodności policy-v1,
- review: `PENDING_INDEPENDENT_REVIEW`,
- Q2 guard: gotowy i przetestowany,
- guard na dotychczasowym validation: pięć przebiegów 100% pass-through oraz
  jeden przebieg 99,17%; znany `BD-0360` został poprawnie zablokowany,
- severity audit: dataset-v1 24% niezgodności z późniejszą policy-v1,
  boundary-v1 0%,
- protected gate: nadal `HOLD_FOR_EVIDENCE_HARDENING`,
- formalna inferencja diagnostic: zablokowana do review 30/30.
