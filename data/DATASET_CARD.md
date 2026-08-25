# Dataset card — Financial Control Copilot dataset-v1

## Informacje podstawowe

- wersja: `1.0.0`,
- język: polski,
- domena: kontrola finansowa i sprawozdawczość bankowa,
- charakter danych: w 100% syntetyczne,
- generator: deterministyczny, seed `20260826`,
- liczba rekordów: 620,
- dane klientów lub osób fizycznych: brak.

Dataset służy do demonstracji supervised fine-tuningu metodami LoRA i QLoRA.
Nie jest przeznaczony do wdrażania autonomicznego systemu kontrolnego ani do
oceny rzeczywistego banku.

## Splity

| Split | Rekordy | Przeznaczenie |
|---|---:|---|
| train | 400 | trening adaptera |
| development | 50 | debugowanie pipeline'u i promptu |
| validation | 50 | dobór konfiguracji treningu |
| test | 100 | syntetyczny test regresyjny |
| challenge | 20 | prompt injection i przypadki adversarial |

Rodzina scenariusza (`group_id`) występuje dokładnie w jednym splicie. Zapobiega
to przenikaniu wariantów liczbowych tej samej rodziny między train i test.

## Zakres

Zbiór zawiera po 62 rekordy dla każdego rodzaju kontroli:

- `ARITHMETIC`,
- `CROSS_SECTION`,
- `PERIOD`,
- `UNIT`,
- `CURRENCY`,
- `DIRECTION`,
- `VARIANCE`,
- `DISCLOSURE`,
- `EVIDENCE`,
- `INSUFFICIENT_DATA`.

Uwzględnia statusy `PASS`, `WARN`, `FAIL`, `INSUFFICIENT_DATA` oraz
`NOT_APPLICABLE`, a także 70 oznaczonych rodzajów mutacji.

## Sposób utworzenia

Generator łączy:

- katalog procedur kontrolnych,
- fikcyjne miary i noty bankowe,
- kontrolowane wartości liczbowe,
- mutacje błędów, braków i niejednoznaczności,
- zdefiniowane złote odpowiedzi i źródła dowodowe.

Każdy rekord zawiera metadane wersji, rodziny, mutacji, seeda i pochodzenia.
Generator nie korzysta z dokumentów ani danych rzeczywistego banku.

## Kontrola jakości

- 100% rekordów przechodzi JSON Schema,
- brak dokładnie zduplikowanych przypadków,
- brak rodzin obecnych w wielu splitach,
- każdy `source_id` złotej odpowiedzi występuje w wejściu,
- wykonano ręczny przegląd 20 rekordów walidacyjnych,
- challenge zawiera 20 jawnie oznaczonych prób prompt injection.

Pełny raport znajduje się w `results/dataset_v1_audit.md`.

## Ograniczenia

1. Dane są krótkie i bardziej uporządkowane niż rzeczywiste sprawozdania.
2. Część sformułowań pochodzi ze wspólnych szablonów. Syntetyczny split `test`
   służy do regresji, a nie jako jedyny dowód generalizacji.
3. Zbiór nie odwzorowuje pełnej różnorodności polskich regulacji, produktów ani
   praktyk księgowych.
4. Złote odpowiedzi są regułowe; nie zastępują przeglądu eksperta finansowego.
5. Wyniki na tym zbiorze nie mogą być interpretowane jako gotowość produkcyjna.
6. Ostateczny benchmark szkoleniowy powinien raportować również oddzielny,
   ręcznie przygotowany zbiór diagnostyczny i przypadki spoza szablonów.

## Ryzyka użycia

- przeuczenie na stylu syntetycznych odpowiedzi,
- nadmierna skłonność do `PASS` albo `FAIL`,
- poprawny JSON przy błędnym wniosku,
- nieuwzględnienie rzeczywistego kontekstu regulacyjnego,
- błędne potraktowanie wyniku LLM jako decyzji kontrolera.

W każdym zastosowaniu wynik wymaga walidacji deterministycznej i przeglądu
człowieka odpowiedzialnego za kontrolę.

## Reprodukcja

```powershell
uv run peft-generate-dataset --mode full
uv run peft-audit-dataset --data data/generated/dataset_v1.jsonl
uv run peft-token-stats --data data/generated/dataset_v1.jsonl
```

