# Karty ćwiczeń dla uczestników

Nie zaglądaj do klucza prowadzącego przed omówieniem. Każdy zespół zapisuje:
decyzję, najważniejszą przesłankę, ryzyko pomyłki i sposób weryfikacji.

## Ćwiczenie 1 — dobór interwencji (6 minut)

Przypisz jeden dominujący mechanizm: prompt/few-shot, RAG, PEFT/SFT,
continued pretraining, kod deterministyczny. Możesz dodać mechanizm wspierający.

1. Treść procedury zmienia się co tydzień, a odpowiedź ma cytować obowiązującą wersję.
2. Wiedza jest dostępna w promptach, lecz model niestabilnie wybiera jeden z pięciu statusów.
3. Model nie rozumie nowego słownictwa produktowego występującego w milionach dokumentów.
4. Decyzja zależy od jawnej reguły `abs(actual - expected) > threshold`.

Pytania pomocnicze: czy zmienia się wiedza czy zachowanie? Jak często? Jaki jest
koszt błędu? Czy wynik musi być audytowalny?

## Ćwiczenie 2 — granice statusów (8 minut)

Dla każdej pary wskaż status po lewej i po prawej oraz jedną przesłankę, która
powoduje zmianę. Dostępne statusy: `PASS`, `WARN`, `FAIL`,
`INSUFFICIENT_DATA`, `NOT_APPLICABLE`.

1. Odchylenie wynosi 0,4 mln PLN / 1,4 mln PLN; próg ostrzegawczy to 1 mln PLN.
2. Niezgodność jest poniżej / powyżej progu materialności 5 mln PLN.
3. Kontrola nie ma triggera / trigger wystąpił, ale brakuje obowiązkowego raportu.

Następnie zaproponuj minimalną parę treningową: zmień dokładnie jedną przesłankę
tak, aby oczekiwany status musiał się zmienić.

## Ćwiczenie 3 — komitet model risk (7 minut)

Macie następujące dowody:

- validation macro-F1 = 1,000 dla trzech seedów,
- diagnostic macro-F1 = 0,834–0,949,
- FC-209: trzy razy `PASS` mimo poprawnego obliczenia `27 > 5`,
- retrospektywny guard blokuje sprzeczność FC-209,
- protected evidence nie zostało otwarte.

Zdecydujcie: `APPROVE`, `CONDITIONAL` czy `HOLD`. Oddzielcie trzy pytania:

1. Czy adapter nauczył się zachowania na validation?
2. Czy cały system bezpiecznie obsługuje znany błąd?
3. Czy mamy niezależny dowód generalizacji?

## Ćwiczenie dodatkowe — zaprojektuj benchmark bankowy (12 minut)

Wybierz przypadek z katalogu zastosowań i zaprojektuj kartę eksperymentu:

- baseline i kontrfaktyczny wariant bez PEFT,
- jednostkę splitu zapobiegającą leakage,
- trzy metryki techniczne i trzy biznesowe,
- dwa typy minimalnych par,
- warunek automatycznego `STOP`,
- miejsce dla RAG, kodu deterministycznego i human review.

