# Ręczny przegląd pilota dataset-v1

## Zakres

Przejrzano 20 rekordów ze splitu validation: po dwa przypadki dla każdego z
10 typów kontroli. W próbie znalazły się statusy poprawne oraz niezgodności.

Sprawdzano:

- zgodność źródeł z opisem problemu,
- poprawność złotego statusu i severity,
- istnienie wszystkich identyfikatorów dowodów,
- zgodność rekomendowanego działania z ustaleniem,
- sens biznesowy terminologii i checklist,
- brak danych rzeczywistych lub osobowych.

## Przejrzane przypadki

| Typ | Przypadki | Wynik |
|---|---|---|
| ARITHMETIC | TR-0046, TR-0047 | zaakceptowane |
| CROSS_SECTION | TR-0106, TR-0107 | zaakceptowane |
| PERIOD | TR-0166, TR-0167 | zaakceptowane |
| UNIT | TR-0226, TR-0227 | zaakceptowane |
| CURRENCY | TR-0286, TR-0287 | zaakceptowane |
| DIRECTION | TR-0346, TR-0347 | zaakceptowane |
| VARIANCE | TR-0406, TR-0407 | zaakceptowane |
| DISCLOSURE | TR-0466, TR-0467 | zaakceptowane po korekcie generatora |
| EVIDENCE | TR-0526, TR-0527 | zaakceptowane |
| INSUFFICIENT_DATA | TR-0586, TR-0587 | zaakceptowane |

## Wykryta i usunięta wada

Pierwsza wersja pilota stosowała generyczne elementy checklisty ujawnień do
niepasujących tematów. Generator został zmieniony tak, aby używać odrębnych
checklist m.in. dla MSSF 9, płynności, kapitału, ryzyka rynkowego, wartości
godziwej i podmiotów powiązanych. Po zmianie ponownie wykonano audyt.

## Wniosek

Próbka jest wystarczająco spójna do treningu demonstracyjnego. Nadal wymaga
oddzielnego, ręcznie zaprojektowanego benchmarku końcowego, ponieważ wspólny
styl szablonów może ułatwiać syntetyczny test regresyjny.

