# Diagnostic set v1 — karta danych

## Cel

`diagnostic-set-v1.0.2` jest ręcznie napisanym benchmarkiem poza generatorami
`dataset-v1` i `boundary-pack-v1`. Ma sprawdzić, czy Q1 nauczył się reguł
kontroli, czy jedynie stylu syntetycznych szablonów.

Zbiór nie jest źródłem treningowym, nie służy do strojenia Q1 i nie zawiera
danych rzeczywistego banku ani klientów.

## Zakres

| Kategoria | Przypadki | Liczba |
|---|---|---:|
| wieloźródłowe kontrole liczbowe | FC-201–FC-210 | 10 |
| niejednoznaczna stosowalność | FC-211–FC-215 | 5 |
| brakujące lub sprzeczne dane | FC-216–FC-220 | 5 |
| prompt injection w dokumentach | FC-221–FC-225 | 5 |
| neutralne i pozadomenowe | FC-226–FC-230 | 5 |

Wszystkie rekordy mają `generation_method=manual`, unikalne rodziny i split
`validation`. Identyfikator `validation` oznacza, że zbiór jest dozwolony przed
protected evidence; nie należy go łączyć z dotychczasowym validation przy
raportowaniu wyników.

## Kontrakt złotych odpowiedzi

- status wynika z kolejności decyzji `status-policy-v1`,
- severity: PASS/N/A → NONE, WARN/INSUFFICIENT_DATA → MEDIUM, FAIL → HIGH,
- `requires_human_review` wynika z tej samej polityki,
- każdy dowód używa wyłącznie `source_id` obecnego w wejściu,
- obliczenie deterministyczne jest używane tylko wtedy, gdy wynik znajduje się
  w `input.deterministic_check`,
- treść prompt injection jest traktowana jako niezaufana zawartość dokumentu.

## Status review

Walidacja schematu i spójności implementacyjnej: wykonana. Review wspomagany
Sol/high: wykonany dla 30/30 przypadków; po review usunięto trzy wskazówki
etykietowe i poprawiono jedną rekomendację operacyjną. Złote statusy oraz
obliczenia nie wymagały zmian. Po diagnostyce doprecyzowano porównywalność
zakresu w `FC-209`; złoty status pozostał bez zmian. Ponownego review SME
wymaga wyłącznie ten przypadek: `PENDING_FC209_AMENDMENT_REVIEW`.

Kryteria: `configs/diagnostic_review_criteria_v1.json`.
Formularz: `data/reviews/diagnostic_set_v1_review.json`.
Review wspomagany: `data/reviews/diagnostic_set_v1_assisted_review.json`.

## Ograniczenia

- przypadki są syntetyczne i ręcznie napisane przez autora projektu,
- 30 rekordów nie estymuje jakości produkcyjnej,
- rozkład statusów jest diagnostyczny,
- benchmark może wskazać kierunek błędów, lecz nie uzasadnia strojenia na
  protected testach,
- ostateczne zatwierdzenie wymaga osoby niezależnej od autorstwa przypadków.
