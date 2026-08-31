# S7.2 — zamrożony projekt train/dev v2 i handoff dla Luna/low

## Decyzja projektowa

**`S7_2_DESIGN_READY_FOR_LUNA_LOW`**

Sol/high zakończył projekt S7.2. Dane nie zostały jeszcze wygenerowane. Nie
wykonano treningu Q2, inferencji ani authoringu Evidence v2. Evidence v1
pozostaje `FAILED / FROZEN / READ-ONLY`.

## Zamrożony zakres

| Split | Przypadki | Statusy | Pary kontrfaktyczne | Zastosowanie |
|---|---:|---|---:|---|
| train-hardening v2 | 300 | 60 PASS, 60 WARN, 60 FAIL, 75 ID, 45 NA | 24 | opcjonalny trening Q2 po S7.3 |
| dev-hard v2 | 90 | 18 PASS, 18 WARN, 18 FAIL, 24 ID, 12 NA | 12 | prompt/guard ablation i późniejsza bramka Q2 |

`ID` oznacza `INSUFFICIENT_DATA`, a `NA` — `NOT_APPLICABLE`.

Macierz risk × status jest dokładnie zamrożona w
`configs/s7_train_dev_v2_spec.json`. Luna/low nie może zmieniać liczności ani
przesuwać trudnych przypadków do łatwiejszych klas.

## Pięć warstw przypadków

1. **Missing data i applicability — 35%**: rozróżnienie braku triggera, braku
   dowodu, potwierdzonego naruszenia i niematerialnej wady.
2. **Source trust i injection — 25%**: instrukcja w dokumencie nie jest
   dowodem; neutralny komunikat nie może być automatycznie uznany za injection.
3. **Severity i escalation — 20%**: severity oraz human review są pochodnymi
   statusu, nie niezależną intuicją modelu.
4. **Deterministic materiality — 15%**: PASS/WARN/FAIL wokół tolerancji,
   materiality oraz dokładnej granicy.
5. **Clean regression — 5%**: zwykłe przypadki bez injection i braków, aby
   guard nie nauczył systemu blokować wszystkiego.

W obu splitach występuje dziewięć typów kontroli. Każdy typ ma pokryć wszystkie
statusy w połączonym train/dev.

## Kontrakt danych v2

Nowością są jawne pola źródeł:

- `source_role`: `EVIDENCE`, `SCOPE_FACT`, `UNTRUSTED_INSTRUCTION` albo
  `METADATA`;
- `trusted_for_evidence`: wartość logiczna;
- `evidence_role`: rola wymagana przez procedurę kontrolną.

Kontrola deklaruje `applicability_rule` i `required_evidence_roles`. Dzięki
temu prompt oraz guard mogą sprawdzić zakres i kompletność bez dostępu do
`expected_output`.

Output pozostaje zgodny z obecnym schematem status-aware v2. S7.3 ma porównać
zmianę promptu i guarda, a nie jednocześnie zmieniać format odpowiedzi.

## Authoring bez leakage

Praca jest rozdzielona na trzy fazy:

1. **Generowanie** korzysta wyłącznie z nowych specyfikacji i polityki statusów.
   Kod ani agent nie wczytuje treści historycznych przypadków v1.
2. **Similarity scan** po zakończeniu generowania porównuje nowe dane z plikami
   związanymi w rejestrze wykluczeń. Jest to mechaniczna kontrola, nie źródło
   treści dla authoringu.
3. **Review** analizuje wyłącznie nowe przypadki, raporty walidacji i zamrożoną
   rubric. Nieudany similarity scan powoduje kwarantannę; nie wolno
   automatycznie parafrazować przypadku na podstawie tekstu v1.

Automatyczny FAIL obejmuje m.in. duplikaty, wspólne identyfikatory i rodziny,
cross-split leakage, 5-gram Jaccard ≥ 0,35 względem v1, Jaccard ≥ 0,30 między
train i dev oraz sequence-match ≥ 0,82 względem v1. Niższe progi ostrzegawcze
tworzą kolejkę review.

## Gold rubric

Każdy gold przechodzi kolejno:

1. applicability,
2. kompletność zaufanych ról dowodowych,
3. wynik deterministyczny i próg, jeśli występują,
4. status,
5. severity i human review jako pola pochodne,
6. evidence wyłącznie z zaufanych źródeł.

Przypadek jest odrzucany, jeśli więcej niż jeden status jest obronny, brakuje
jawnej podstawy zakresu lub reguły pierwszeństwa, gold cytuje nieufne źródło,
albo para kontrfaktyczna zmienia więcej niż jedną przesłankę.

Luna/low wykonuje assisted review 390/390. To nie jest akceptacja SME. Po
mechanicznym PASS Sol/high analizuje pakiet, a nazwany człowiek/SME zatwierdza
390/390 goldów przed `S7_TRAIN_DEV_V2_FROZEN`.

## Zadanie wykonawcze Luna/low

Luna/low ma:

1. uruchomić `scripts/validate_sprint7_2_design.py` i zatrzymać się, jeśli
   wynik nie jest `S7_2_DESIGN_READY_FOR_LUNA_LOW`;
2. utworzyć generator oparty wyłącznie na zamrożonej specyfikacji;
3. wygenerować nowy fikcyjny source pack oraz dokładnie 300 + 90 przypadków;
4. wdrożyć walidatory kontraktu, macierzy, status policy, derived fields,
   source trust, par kontrfaktycznych i split isolation;
5. po generowaniu wdrożyć i uruchomić oddzielny similarity/leakage scanner;
6. przygotować assisted review 390/390 oraz pusty szablon human/SME review;
7. zbudować registry z SHA-256 wszystkich artefaktów;
8. uruchomić 91 istniejących testów i nowe testy S7.2;
9. zapisać raporty i zatrzymać się na
   `S7_TRAIN_DEV_V2_READY_FOR_SOL_SME_REVIEW`;
10. wykonać commit i push wyłącznie po mechanicznym PASS.

## Oczekiwane artefakty Luna/low

- `data/sprint7/source_pack_v2.json`;
- `data/sprint7/train_hardening_v2.jsonl`;
- `data/sprint7/dev_hard_v2.jsonl`;
- `data/sprint7/train_dev_registry_v2.json`;
- `data/reviews/s7_train_dev_v2_assisted_review.json`;
- `data/reviews/s7_train_dev_v2_human_review_template.json`;
- `results/sprint7/s7_2_generation_report.json`;
- `results/sprint7/s7_2_similarity_report.json`;
- `results/sprint7/s7_2_mechanical_gate.json`.

## Warunki zatrzymania

Luna/low zatrzymuje pracę i wraca do Sol/high, gdy:

- liczności lub macierz nie mogą zostać spełnione bez zmiany specyfikacji;
- przypadek jest semantycznie niejednoznaczny;
- similarity threshold nie przechodzi;
- para kontrfaktyczna zmienia więcej niż jedną przesłankę;
- potrzeba zmienić rubric, próg albo status policy;
- walidator wykryje ślad protected/shadow w train/dev;
- test lub hash nie przechodzi.

Nie wolno usuwać trudnego przypadku, luzować progu ani regenerować do skutku
bez raportu i decyzji Sol/high.

## Polecenie dla Luna/low

```text
Przeczytaj docs/41_sprint_7_2_design_and_luna_handoff.md oraz wszystkie
zamrożone konfiguracje S7.2. Wykonaj mechaniczną część S7.2 na Luna/low.
Najpierw uruchom scripts/validate_sprint7_2_design.py. Następnie wygeneruj
dokładnie 300 przypadków train-hardening v2 i 90 dev-hard v2 według zamrożonej
macierzy, 36 par kontrfaktycznych i kontraktu source trust. Podczas authoringu
nie wczytuj treści v1; oddzielny similarity/leakage scan uruchom dopiero po
generowaniu. Wykonaj walidatory, assisted review 390/390, registry SHA-256 oraz
wszystkie testy. Nie zmieniaj specyfikacji, rubric, liczności ani progów. Nie
trenuj Q2, nie twórz Evidence v2 i nie uruchamiaj Evidence v1. Zatrzymaj się na
S7_TRAIN_DEV_V2_READY_FOR_SOL_SME_REVIEW; nie deklaruj akceptacji SME. Po
mechanicznym PASS wykonaj commit i push.
```

## Artefakty projektowe Sol/high

- `configs/s7_train_dev_v2_spec.json`;
- `configs/s7_gold_rubric_v2.json`;
- `configs/s7_provenance_policy_v2.json`;
- `configs/s7_similarity_leakage_policy_v2.json`;
- `results/sprint7/s7_2_design_gate.json`;
- `scripts/validate_sprint7_2_design.py`.
