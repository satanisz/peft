# Protected Evidence v1 — guide prowadzącego

Appendix pokazuj po slajdzie 48 głównego decku. Łączny czas: 8–9 minut.

## Przejście ze slajdu 48

„Wasze HOLD było poprawne. Teraz pokażę, co wydarzyło się później — po G0,
G1, G2.1, osobnym approval i jawnym potwierdzeniu operatora.”

## A1 — trzy bramki przed evidence (1,5 min)

Podkreśl, że HOLD nie oznaczał zakazu testowania. Oznaczał brak prawa do
otwarcia danych przed spełnieniem warunków. Powiedz: „Od chwili otwarcia dane
nie są już niewidziane. Nie wolno poprawiać wyniku retuningiem na tym samym
zbiorze.”

Pytanie: którą bramkę najłatwiej pominąć pod presją terminu?

## A2 — agregaty kontra challenge (2 min)

Najpierw odczytaj dwa pierwsze wiersze. Następnie pokaż challenge i shadow.
Wypowiedz liczby dokładnie: original 0,971; boundary 1,000; challenge status
0,700; challenge severity 0,617; shadow `INSUFFICIENT_DATA` 0,600.

Puenta: „Schema i source integrity mogą wynosić 1,0, a decyzja nadal może być
błędna.”

Pytanie: której liczby zabrakłoby w dashboardzie opartym na jednym F1?

## A3 — CH-002 (3 min)

Nie pokazuj pełnego JSON. Prowadź wzrokiem po sekwencji: niezaufane źródło,
gold `INSUFFICIENT_DATA`, dwa seedy `PASS`, jeden `FAIL`.

Powiedz: „11 z 60 odpowiedzi primary dało false-assurance PASS zgodny z wrogą
instrukcją. To nie jest błąd kosmetyczny — PASS może zatrzymać eskalację.”

Pytanie: co powinno zablokować wynik — prompt, trening, guard czy właściciel
procesu? Oczekiwana odpowiedź: warstwy razem.

## A4 — decyzja systemowa (1,5–2 min)

Zamknij logicznie: Evidence v1 jest `FAILED/FROZEN/READ-ONLY`, warsztat może
wykorzystać wynik po dry-runie, produkcja ma `NOT APPROVED`.

Powiedz: „PEFT uczy zachowania. Nie przejmuje odpowiedzialności za decyzję.”

Pytanie końcowe: który wynik dawał największe fałszywe poczucie bezpieczeństwa?

Po dwóch odpowiedziach wróć do slajdu 49 głównego decku.

## Zasady bezpieczeństwa demonstracji

- Nie uruchamiaj live protected runnera ani treningu.
- Korzystaj z gotowego appendixu i zamrożonych raportów.
- Nie nazywaj assisted review review człowieka/SME.
- Nie ukrywaj 11 krytycznych primary i 2 shadow.
- Nie przedstawiaj appendixu jako dowodu production readiness.

## Źródła

- `results/sprint6/evidence_summary.json`
- `results/sprint6/protected_evidence_v1_closure.json`
- `results/sprint4/challenge_manual_review.json`
- `results/sprint6/shadow_manual_response_review.json`
- `docs/28_sprint_6_final_evidence_review.md`
