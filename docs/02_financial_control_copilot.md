# Financial Control Copilot

## Cel przypadku

System wspiera kontrolera finansowego w analizie sprawozdania fikcyjnego banku.
Otrzymuje fragment raportu, dane tabelaryczne, wyniki kontroli obliczeniowych
oraz właściwą procedurę. Zwraca ustrukturyzowane ustalenie przeznaczone do
weryfikacji przez człowieka.

System nie zatwierdza sprawozdania, nie księguje korekt i nie podejmuje decyzji
regulacyjnych ani kredytowych.

## Dlaczego ten przypadek nadaje się do LoRA

Adapter może nauczyć model powtarzalnego zachowania:

- bankowej terminologii,
- klasyfikacji wyniku kontroli,
- wymaganej struktury odpowiedzi,
- wskazywania dowodu,
- odróżniania błędu od braku danych,
- krótkiego stylu raportowania ustaleń,
- zasad eskalacji do człowieka.

Adapter nie powinien przechowywać zmiennych regulaminów, aktualnych progów ani
danych konkretnego banku. Te informacje muszą przychodzić w kontekście lub z
warstwy retrieval.

## Granice systemu

```text
sprawozdanie/tabela ──> ekstrakcja ──> kontrole Python/SQL ──┐
                                                             ├─> LLM + LoRA ─> ustalenie
procedury/checklisty ────────────────> retrieval/context ─────┘                 │
                                                                                v
                                                                       kontroler-człowiek
```

## Typy kontroli w wersji warsztatowej

| Kod | Kontrola | Przykładowy problem |
|---|---|---|
| ARITHMETIC | uzgodnienie sum | suma składników nie zgadza się z `Razem` |
| CROSS_SECTION | spójność sekcji | inna kwota w tabeli i komentarzu |
| PERIOD | okres raportowy | porównanie kwartału z pełnym rokiem |
| UNIT | jednostka | tysiące pomylone z milionami |
| CURRENCY | waluta | PLN zestawione bez przeliczenia z EUR |
| DIRECTION | kierunek zmiany | opis mówi o wzroście, tabela o spadku |
| VARIANCE | istotna zmiana | zmiana powyżej progu bez wyjaśnienia |
| DISCLOSURE | kompletność | brak wymaganej noty lub uzasadnienia |
| EVIDENCE | jakość dowodu | wniosek bez wskazania źródła |
| INSUFFICIENT_DATA | brak danych | model powinien odmówić jednoznacznej oceny |

## Statusy wyniku

- `PASS` — dowody potwierdzają zgodność,
- `WARN` — potencjalny problem lub słaba jakość wyjaśnienia,
- `FAIL` — potwierdzona niezgodność,
- `INSUFFICIENT_DATA` — brak danych potrzebnych do oceny,
- `NOT_APPLICABLE` — kontrola nie dotyczy danego fragmentu.

## Schemat oczekiwanej odpowiedzi

```json
{
  "control_id": "FIN-REV-004",
  "control_type": "CROSS_SECTION",
  "status": "FAIL",
  "severity": "HIGH",
  "finding": "Wartość wyniku odsetkowego w tabeli różni się od komentarza.",
  "evidence": [
    {
      "source_id": "table_12.net_interest_income",
      "value": "1284000000 PLN"
    },
    {
      "source_id": "management_commentary.p47.s2",
      "value": "1248000000 PLN"
    }
  ],
  "calculation": {
    "performed_by": "deterministic_control",
    "difference": 36000000,
    "unit": "PLN"
  },
  "recommended_action": "Uzgodnić komentarz zarządu z zatwierdzoną tabelą.",
  "requires_human_review": true,
  "confidence": "HIGH"
}
```

Pole `confidence` nie jest probabilistyczną kalibracją modelu. To kategoria
operacyjna wyliczana z kompletności dowodów i rodzaju kontroli.

## Struktura przykładu treningowego

Każdy przypadek zawiera:

- `case_id`,
- wersję fikcyjnego raportu i procedury,
- typ kontroli,
- tekst i dane tabelaryczne,
- wynik kontroli deterministycznej, jeśli dotyczy,
- konwersację `system/user/assistant`,
- złotą odpowiedź strukturalną,
- identyfikatory dowodów,
- metadane scenariusza i poziomu trudności,
- informację, czy przykład jest syntetyczną mutacją innego przypadku.

## Plan danych

### Wersja minimalna — pierwszy eksperyment

- 30–50 przypadków,
- 5 typów kontroli,
- jeden fragment rachunku wyników,
- baseline i walidator, bez fine-tuningu.

### Wersja warsztatowa

- 400–700 przypadków treningowych,
- 100–150 walidacyjnych,
- 150–250 testowych,
- wszystkie typy kontroli,
- osobny zestaw adversarial i prompt-injection.

### Wersja rozszerzona

- 1500–3000 przypadków,
- kilka okresów i wersji raportu,
- różne szablony językowe,
- trudne przypadki wielodokumentowe,
- dane polskie i wybrany podzbiór angielski.

## Ochrona przed leakage

Podział nie może być wykonany wyłącznie losowo na rekordach. Razem grupujemy:

- przypadki pochodzące z tej samej tabeli,
- parafrazy tego samego ustalenia,
- mutacje tego samego błędu,
- fragmenty tej samej wersji raportu.

Zestaw testowy powinien zawierać nowe wartości, nowe sformułowania i część
nieznanych kombinacji typów błędów.

## Przykłady adversarial

- instrukcja w treści raportu nakazująca zwrócić `PASS`,
- komentarz bez identyfikowalnego źródła,
- sprzeczne dowody o różnej dacie,
- poprawne liczby z błędną jednostką,
- duża zmiana mająca prawidłowe wyjaśnienie,
- brak jednej wartości wymaganej do obliczenia,
- tekst sugerujący błąd, którego nie potwierdzają dane.

## Rozszerzenia biznesowe

Po warsztacie ten sam wzorzec można przenieść na:

- kontrolę raportów zarządczych,
- klasyfikację ustaleń audytowych,
- kompletność checklist ujawnień,
- kontrolę komentarzy do istotnych odchyleń,
- triage reklamacji i incydentów operacyjnych,
- porządkowanie dokumentacji kontroli wewnętrznej.

