# Plan eksperymentów i benchmarku

## Pytanie eksperymentalne

Czy QLoRA poprawia jakość wykonywania i dokumentowania kontroli finansowej w
porównaniu z dobrze zaprojektowanym promptem, bez niedopuszczalnego wzrostu
fałszywych alarmów i regresji na zadaniach ogólnych?

## Hipotezy

1. Few-shot poprawi zgodność formatu, ale będzie wrażliwy na długość i dobór
   przykładów.
2. QLoRA istotnie poprawi zgodność JSON, klasyfikację statusu i styl ustalenia.
3. Sam fine-tuning nie zagwarantuje poprawności arytmetycznej.
4. Połączenie kontroli deterministycznych z QLoRA da najlepszy wynik dla zadań
   liczbowych.
5. RAG poprawi zgodność z procedurą, ale nie zastąpi uczenia zachowania.
6. Zbyt agresywny trening zwiększy false positives lub pogorszy odpowiedzi na
   zadaniach spoza domeny.

## Porównywane warianty

| ID | Wariant | Cel |
|---|---|---|
| B0 | model bazowy, zero-shot | minimalny baseline |
| B1 | model bazowy, dopracowany prompt | wartość prompt engineeringu |
| B2 | model bazowy, few-shot | koszt przykładów w kontekście |
| L1 | LoRA BF16 | wpływ adaptera bez kwantyzacji bazowych wag |
| Q1 | QLoRA NF4 | główna metoda warsztatowa |
| Q2 | QLoRA + kontrole Python/SQL | architektura rekomendowana |
| Q3 | QLoRA + kontrole + kontekst procedury | pełny wzorzec rozwiązania |
| D1 | DoRA lub rsLoRA | opcjonalne rozszerzenie dla prowadzącego |

Pełny fine-tuning może zostać pokazany jako wynik referencyjny dla mniejszego
modelu, ale nie jest wymagany do demonstracji na żywo.

## Zmienne kontrolowane

- identyczny model bazowy i tokenizer,
- przypięta rewizja modelu,
- identyczne podziały danych,
- te same parametry generowania,
- ten sam limit nowych tokenów,
- porównywalny budżet przykładów lub tokenów,
- jawne chat template i prompt systemowy,
- brak dostępu do test setu podczas doboru konfiguracji,
- co najmniej trzy seedy w wynikach referencyjnych.

## Metryki jakości

### Struktura

- `json_valid_rate`,
- `schema_valid_rate`,
- kompletność wymaganych pól,
- zgodność typów i dozwolonych etykiet.

### Wykrywanie problemów

- precision, recall i F1 dla `FAIL`,
- macro-F1 wszystkich statusów,
- false positive rate,
- false negative rate dla błędów o wysokiej istotności,
- accuracy typu kontroli i poziomu istotności.

### Dowody i wnioskowanie

- poprawność identyfikatorów źródeł,
- evidence precision i evidence recall,
- zgodność liczb z przekazanym wynikiem deterministycznym,
- prawidłowe użycie `INSUFFICIENT_DATA`,
- liczba twierdzeń bez pokrycia w źródłach.

### Jakość operacyjna

- poprawność rekomendowanej akcji,
- prawidłowa eskalacja do człowieka,
- odporność na instrukcje osadzone w dokumentach,
- ocena człowieka w ślepym porównaniu A/B.

## Metryki techniczne

- liczba i procent trenowanych parametrów,
- szczytowe wykorzystanie VRAM,
- czas treningu,
- tokeny i przykłady na sekundę,
- wielkość checkpointu adaptera,
- czas ładowania,
- inferencja p50 i p95,
- pamięć inferencji przed i po scaleniu adaptera.

## Test regresji

Osobny, niewykorzystany podczas treningu zestaw obejmie:

- zwykłe podsumowanie neutralnego tekstu,
- pytania wymagające odmowy przy braku kontekstu,
- proste instrukcje w języku polskim,
- odpowiedzi niezwiązane z kontrolą finansową,
- przypadki, w których poprawnym wynikiem jest `PASS`.

## Ablations dla prowadzącego

Poza głównym szkoleniem przygotujemy porównania:

- rank `4/8/16/32`,
- adapter tylko na attention vs `all-linear`,
- różne wartości `alpha`,
- LoRA dropout `0` vs wartość dodatnia,
- 1, 2 i 3 epoki,
- mały i pełny zbiór treningowy,
- FP16/BF16, jeśli sprzęt pozwala,
- klasyczne skalowanie vs rsLoRA,
- dane czyste vs dane z trudnymi negatywami.

Nie będziemy wybierać najlepszego wariantu na podstawie pojedynczego wyniku.
Raport pokaże średnią, rozrzut między seedami i analizę typów błędów.

## Minimalne kryteria sukcesu demonstracji

- pipeline działa od surowego przypadku do raportu metryk,
- baseline jest zapisany przed treningiem,
- model QLoRA generuje poprawny schemat w co najmniej 95% przypadków testowych,
- poprawa macro-F1 jest widoczna względem B1, ale raport nie ukrywa regresji,
- false positive rate jest raportowany osobno,
- żadna liczba prezentowana jako wynik eksperymentu nie pochodzi z train setu,
- wynik można odtworzyć z konfiguracji zapisanej w repozytorium.

Próg 95% dla schematu jest kryterium inżynieryjnym projektu, a nie obietnicą
wyniku. Jeżeli eksperyment go nie osiągnie, pokazujemy przyczynę i poprawiamy
pipeline albo walidację.

## Scenariusz prezentacji wyniku

1. Pokazać trzy odpowiedzi B0, w tym odpowiedź przekonującą, ale błędną.
2. Uruchomić automatyczny benchmark B0/B1/B2.
3. Pokazać liczbę trenowanych parametrów i aktualne zużycie pamięci.
4. Uruchomić krótki trening QLoRA.
5. Załadować wcześniej przygotowany pełny adapter.
6. Porównać Q1 z B1 na identycznych przypadkach.
7. Dodać wynik deterministycznej kontroli i pokazać Q2.
8. Zakończyć tabelą jakości, kosztu i typowych błędów.

