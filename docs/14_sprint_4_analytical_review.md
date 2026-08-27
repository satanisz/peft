# Sprint 4 — analytical review przed protected evidence

## Decyzja wykonawcza

**Decyzja: `CONDITIONAL_HOLD_BEFORE_PROTECTED_EVIDENCE`.**

Replikacja Q1 jest technicznie udana: trzy seedy zakończyły trening, nie było
obciętych przykładów, peak VRAM wyniósł około 7,55 GiB, a statusy na original i
boundary validation osiągnęły macro-F1 1,000. Nie ma podstaw do odrzucenia Q1
jako adaptera warsztatowego.

Nie otwieramy jeszcze original test, boundary test ani challenge. Review
wykrył, że dotychczasowa bramka nie traktowała `severity` i integralności
`source_id` jako kryteriów blokujących. Ponadto perfekcyjne statusy pochodzą z
danych syntetycznych tworzonych przez te same generatory i rodziny wzorców co
train. Otwarcie kolejnego syntetycznego testu przed zbudowaniem benchmarku poza
szablonami dałoby ograniczoną nową informację i odebrałoby możliwość bezpiecznej
korekty systemu bez strojenia na teście.

Protected splits pozostają nieotwarte. Stan blokady zapisuje
`configs/sprint4_protected_open_gate_v1.json`.

## Podsumowanie dotychczasowych sprintów

| Sprint | Najważniejszy rezultat | Decyzja | Główna lekcja |
|---|---|---|---|
| 1 | `dataset-v1.0.0`: 620 przypadków, 400 train, grupowe splity, 20 injection | M1 PASS | Jakość, lineage i freeze danych są częścią eksperymentu, nie pracą pomocniczą. |
| 2 | B0/B1/B2 na Qwen3-4B; B2 macro-F1 0,529 na validation | M2 PASS | Prompt i few-shot poprawiają format i decyzje, ale słabo obsługują WARN i N/A. |
| 2.5 | 540 przypadków boundary, 270 minimalnych par, B3 macro-F1 0,894 | M2.5 warunkowo | Jawna polityka etykiet i dane kontrastowe ograniczają koszt błędów. |
| 3 | Q0 kontra Q1; Q1 boundary macro-F1 1,000, 51,6% mniej input tokens niż B3 | M3 PASS | Boundary train miał większą wartość niż samo uruchomienie QLoRA. |
| 4 — replikacja | Trzy seedy Q1, wszystkie status macro-F1 1,000 | replikacja PASS, protected HOLD | Stabilność statusu nie jest jeszcze dowodem generalizacji ani pełnej poprawności dowodów. |

## Wynik replikacji Q1

| Seed | Czas treningu | Peak VRAM | Original F1 | Boundary F1 | Severity original | Sources boundary |
|---:|---:|---:|---:|---:|---:|---:|
| 20260827 | 88 min 22 s | 7,551 GiB | 1,000 | 1,000 | 94% | 100% |
| 20260828 | 85 min 43 s | 7,552 GiB | 1,000 | 1,000 | 94% | 99,17% |
| 20260829 | 84 min 45 s | 7,551 GiB | 1,000 | 1,000 | 98% | 100% |

Wszystkie seedy osiągnęły 100% recall `WARN`, `NOT_APPLICABLE`, 100% pair
accuracy, 0% FAIL FPR i 0% unsafe PASS. Rozrzut status macro-F1 wynosi zero.
Średni czas treningu to około 86 min 17 s na seed.

## Ustalenia review

### 1. Replikacja jest stabilna technicznie

- wszystkie biegi mają status `completed`,
- każdy wykonał 240/240 kroków i 3 epoki,
- nie obcięto żadnego przypadku,
- różnica peak VRAM między seedami wynosi około 0,001 GiB,
- konfiguracje różnią się wyłącznie seedem, identyfikatorem i ścieżką wyniku.

### 2. Statusy są stabilne, severity nie jest perfekcyjne

Original validation zawiera odpowiednio 3, 3 i 1 błędów severity. Powtarza się
przypadek `TR-0107`, w którym niezgodność CROSS_SECTION o oczekiwanej severity
HIGH bywa oceniana jako MEDIUM. Inne błędy są zależne od seeda. Nie zmieniają
statusu kontrolnego, ale mają znaczenie dla priorytetyzacji alertów w banku.

### 3. Wystąpiła jedna halucynacja identyfikatora źródła

W `BD-0360` seed 20260828 zwrócił `boundary.199.policy` zamiast dostępnego
`boundary.179.policy`. Status pozostał poprawny, ale evidence precision i recall
spadły do 0,5. To dowód, że perfekcyjne macro-F1 może maskować błąd śladu
dowodowego.

### 4. Perfekcyjny wynik nie dowodzi generalizacji

Train i validation są rozłączne grupowo i nie ma wykrytego leakage rekordów.
Korzystają jednak z tych samych generatorów, struktury procedur i słownika
odpowiedzi. Wynik 1,000 należy interpretować jako opanowanie zamkniętego
kontraktu syntetycznego, nie jako estymację jakości na dokumentach bankowych.

### 5. Protected evidence jest metodologicznie gotowe, lecz ma niski przyrost
informacji bez diagnostic setu

Progi, seedy i skrypt jednorazowego otwarcia są zamrożone. Original test i
boundary test pochodzą jednak z tych samych generatorów. Najpierw potrzebny jest
ręczny zestaw poza szablonami, aby decyzja o ewentualnej korekcie nie była
podejmowana po zobaczeniu testów chronionych.

## Sprint 4.2A — Evidence Gate Hardening

Ten etap staje się obowiązkowy przed S4.3:

1. Zacommitować wyniki replikacji i związać je z konfiguracją 1.1.0.
2. Przygotować co najmniej 30 ręcznych przypadków poza generatorami:
   10 liczbowych wieloźródłowych, 5 niejednoznacznej stosowalności, 5 braków
   danych, 5 prompt injection i 5 neutralnych lub pozadomenowych.
3. Wykonać niezależny review złotych odpowiedzi przed inferencją.
4. Zaimplementować Q2/source integrity guard, który odrzuca nieistniejące
   `source_id` i wymusza kontrolowaną eskalację do human review.
5. Porównać raw Q1 i guarded Q2 na original validation, boundary validation i
   diagnostic set; nie używać testów chronionych.
6. Wyjaśnić regułę severity i raportować ją oddzielnie od statusu.
7. Wykonać ponowny review Sol/high. Dopiero decyzja
   `APPROVED_TO_OPEN_PROTECTED_SPLITS` odblokowuje runner S4.3.

### Aktualizacja 28 sierpnia 2026 — przygotowanie Sprintu 4.2A

- 30 przypadków zostało ręcznie zaprojektowanych i przechodzi walidację 30/30,
- Q2/source integrity guard został zaimplementowany i wykrywa znany błąd
  `BD-0360`, blokując odpowiedź bez automatycznego zgadywania źródła,
- analiza wykazała, że 24% severity w dostępnych splitach starego dataset-v1
  jest niezgodne z późniejszym `status-policy-v1`, podczas gdy boundary-v1 ma
  0% takich niespójności,
- original severity zostało sklasyfikowane jako legacy/report-only; policy-v1
  jest egzekwowane dla boundary-v1 i diagnostic-v1,
- formalna inferencja diagnostic pozostaje zablokowana do niezależnego review
  30/30 przypadków.

Status: `DESIGNED_PENDING_INDEPENDENT_REVIEW_AND_DIAGNOSTIC_RUN`.

Szacunek: 1–2 dni pracy aktywnej, około 1–2 godzin GPU na inference i review.
Nie jest potrzebny nowy trening Q1.

## Wpływ na kolejne sprinty

- Sprint 4 wydłuża się o 1–2 dni i kończy dopiero po hardeningu, protected
  evidence, review challenge oraz porównaniu Q1–Q2.
- Sprint 5 rozpoczyna się po M4; materiały muszą pokazywać osobno status,
  severity i poprawność cytowanych źródeł.
- Sprint 6 dodaje próbę awarii evidence guard i przypadek z nieistniejącym
  `source_id`.
- L1, Q1b, rank sweep i Q3 nadal pozostają poza ścieżką krytyczną.

## Warunek otwarcia kolejnego etapu

Otwarcie jest rekomendowane dopiero, gdy wszystkie wymagania Sprintu 4.2A są
spełnione, wyniki są zamrożone w Git, a analityczna bramka ma decyzję
`APPROVED_TO_OPEN_PROTECTED_SPLITS`. Nie obniżamy progów po poznaniu wyników
testu i nie dostrajamy Q1 na protected evidence.
