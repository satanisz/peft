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
7. Kontrastowe dane graniczne poprawią `WARN` i `NOT_APPLICABLE` bardziej niż
   szeroki sweep ranku na niezmienionym zbiorze.
8. Label-complete prompt zmniejszy część błędów, ale adapter może osiągnąć
   podobną lub lepszą jakość przy istotnie krótszym wejściu.

## Porównywane warianty

| ID | Wariant | Cel |
|---|---|---|
| B0 | model bazowy, zero-shot | minimalny baseline |
| B1 | model bazowy, dopracowany prompt | wartość prompt engineeringu |
| B2 | model bazowy, few-shot | koszt przykładów w kontekście |
| B3 | model bazowy, status-aware label-complete | najsilniejszy baseline promptowy |
| L1 | LoRA BF16 | wpływ adaptera bez kwantyzacji bazowych wag |
| Q0 | QLoRA NF4 na dataset-v1 | kontrola wpływu boundary data |
| Q1 | QLoRA NF4 na dataset-v1 + boundary pack | główna metoda warsztatowa |
| Q1b | Q1 z samplingiem granicznym | wariant naprawczy, jeśli Q1 nie spełni M3 |
| Q2 | QLoRA + kontrole Python/SQL | architektura rekomendowana |
| Q3 | QLoRA + kontrole + kontekst procedury | pełny wzorzec rozwiązania |
| D1 | DoRA lub rsLoRA | backlog po wersji warsztatowej |

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
- prawidłowe odróżnienie `NOT_APPLICABLE` od `INSUFFICIENT_DATA`,
- liczba twierdzeń bez pokrycia w źródłach.

### Granice decyzji

- precision, recall, F1 i support dla każdego z pięciu statusów,
- pair accuracy i flip consistency dla minimalnych par,
- recall `WARN` oraz `NOT_APPLICABLE`,
- pomyłki `NOT_APPLICABLE` ↔ `INSUFFICIENT_DATA`,
- unsafe PASS rate,
- unnecessary escalation rate,
- ważony koszt błędu według jawnej macierzy biznesowej.

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

Priorytetowe porównania dla wersji warsztatowej:

- dataset-v1 vs dataset-v1 + boundary pack,
- sampling standardowy vs zorientowany na granice, jeśli Q1 nie spełni M3,
- rank `8/16`,
- adapter tylko na attention vs `all-linear`,
- 1 vs 3 epoki dla głównej konfiguracji,
- LoRA BF16 vs QLoRA, jeśli sprzęt pozwala.

Szerokie rank `4/8/16/32`, wiele wartości `alpha`, DoRA, rsLoRA i drugi model
bazowy pozostają w backlogu. Uruchomimy je dopiero po zamknięciu pakietu
dowodowego, jeśli nie zagrożą materiałom szkoleniowym.

Nie będziemy wybierać najlepszego wariantu na podstawie pojedynczego wyniku.
Raport pokaże średnią, rozrzut między seedami i analizę typów błędów.

## Minimalne kryteria sukcesu demonstracji

- pipeline działa od surowego przypadku do raportu metryk,
- baseline jest zapisany przed treningiem,
- model QLoRA generuje poprawny schemat w co najmniej 98% przypadków,
- na boundary validation poprawia macro-F1 o co najmniej 0,05 względem
  najlepszego z B1/B2/B3 albo pozostaje w granicy 0,02 przy co najmniej 30%
  redukcji input tokens,
- recall `WARN` nie spada względem najlepszego baseline'u, a recall
  `NOT_APPLICABLE` wynosi co najmniej 60% przy wsparciu 30 przypadków,
- recall `PASS` i `FAIL` nie spada o więcej niż 5 punktów procentowych,
- FAIL FPR nie przekracza 15%,
- false positive rate jest raportowany osobno,
- żadna liczba prezentowana jako wynik eksperymentu nie pochodzi z train setu,
- wynik można odtworzyć z konfiguracji zapisanej w repozytorium.

Progi są kryteriami inżynieryjnymi projektu, a nie obietnicą wyniku. Jeżeli
eksperyment ich nie osiągnie, pokazujemy przyczynę i poprawiamy
pipeline albo walidację.

## Scenariusz prezentacji wyniku

1. Pokazać trzy odpowiedzi B0, w tym odpowiedź przekonującą, ale błędną.
2. Uruchomić automatyczny benchmark B0/B1/B2/B3 i pokazać koszt kontekstu.
3. Pokazać liczbę trenowanych parametrów i aktualne zużycie pamięci.
4. Uruchomić krótki trening QLoRA.
5. Załadować wcześniej przygotowany pełny adapter.
6. Porównać Q0 i Q1 z najlepszym z B1/B2/B3 na identycznych przypadkach,
   w tym na minimalnej parze granicznej.
7. Dodać wynik deterministycznej kontroli i pokazać Q2.
8. Zakończyć tabelą jakości, kosztu i typowych błędów.
