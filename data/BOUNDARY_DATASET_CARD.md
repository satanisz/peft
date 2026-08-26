# Karta danych — boundary-pack-v1.0.0

## Przeznaczenie

`boundary-pack-v1.0.0` jest syntetycznym zbiorem diagnostycznym do nauki i
oceny granic statusów w przypadku `Financial Control Copilot`. Uzupełnia, ale
nie zastępuje zamrożonego `dataset-v1.0.0`.

Zbiór służy do:

- porównania promptingu z LoRA/QLoRA,
- sprawdzania granic `PASS/WARN`, `WARN/FAIL` oraz
  `NOT_APPLICABLE/INSUFFICIENT_DATA`,
- analizy kosztu niepotrzebnych alertów i niebezpiecznych akceptacji,
- demonstracji data-centric fine-tuningu podczas szkolenia.

Nie służy do autonomicznych decyzji kontrolnych, oceny zgodności prawnej ani
odwzorowania częstości statusów w konkretnym banku.

## Konstrukcja

Zbiór zawiera 540 rekordów w 270 minimalnych parach. W każdej parze zmienia się
dokładnie jedno pole źródłowe zawierające przesłankę decyzyjną. Zadanie,
procedura, identyfikatory źródeł i pozostały kontekst pozostają takie same.

| Split | Rekordy | Pary | Status użycia |
|---|---:|---:|---|
| train | 240 | 120 | trening i demonstracje |
| development | 60 | 30 | rozwój promptu i konfiguracji |
| validation | 120 | 60 | wybór konfiguracji |
| test | 120 | 60 | zamrożony, nieotwarty |

| Status | Liczba |
|---|---:|
| PASS | 80 |
| WARN | 160 |
| FAIL | 80 |
| INSUFFICIENT_DATA | 110 |
| NOT_APPLICABLE | 110 |

`WARN` i `NOT_APPLICABLE` występują w dziewięciu rodzajach kontroli. Zapobiega
to prostemu skojarzeniu `NOT_APPLICABLE` wyłącznie z `DISCLOSURE`.

## Polityka etykiet

Złote odpowiedzi wynikają z `configs/status_policy_v1.json`. Kolejność decyzji
to: zakres kontroli, kompletność danych, materialne naruszenie, częściowa lub
niematerialna niezgodność, zgodność.

Każdy rekord posiada:

- `group_id` identyfikujący minimalną parę,
- `boundary_type`,
- `reason_code`,
- `paired_status`,
- syntetyczne źródła i jawne provenance.

## Podział i leakage

Cała rodzina pary trafia do jednego splitu. Generator sprawdza:

- brak rodziny w wielu splitach,
- brak dokładnych duplikatów,
- dokładnie jedną zmienioną przesłankę w parze,
- brak jawnej nazwy złotej etykiety w zadaniu i źródłach,
- zgodność `source_id` i schematu.

Split `test` został wygenerowany i zahashowany, ale nie jest używany w Sprincie
2.5. Nie należy go otwierać przed wyborem konfiguracji adaptera w Sprincie 4.

## Review

Review implementacyjne obejmuje 100% rekordów `NOT_APPLICABLE` oraz
warstwową próbkę przekraczającą 20% pozostałych rekordów. Sprawdzane są złota
etykieta, stosowalność, dowody i pojedyncza przesłanka pary. Rejestr znajduje
się w `data/reviews/boundary_pack_v1_review.jsonl`.

Review właściciela projektu i przyszłego właściciela procesu bankowego jest
osobną bramką. Obecna akceptacja dotyczy wyłącznie syntetycznego warsztatu.

## Ograniczenia

- rozkład klas jest diagnostyczny, a nie produkcyjny,
- powtarzalne szablony mogą tworzyć skróty językowe mimo wariantów liczbowych,
- wagi kosztów są porządkowe, nie finansowe,
- brak zewnętrznego SME i danych konkretnego banku,
- dobry wynik na tym zbiorze nie dowodzi gotowości produkcyjnej.

## Odtwarzanie

```powershell
uv run peft-generate-boundary
uv run peft-workshop validate-data --data data/generated/boundary_pack_v1.jsonl
uv run python -m unittest discover -s tests -v
```

Wersja, hashe pliku zbiorczego i splitów są zapisane w
`data/boundary_registry.json`.
