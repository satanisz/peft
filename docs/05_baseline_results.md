# Pierwszy baseline — model smoke 0.6B

## Status eksperymentu

Data wykonania: 7 sierpnia 2026.

Model: `Qwen/Qwen3-0.6B`, rewizja
`c1899de289a04d12100db370d81485cdf75e47ca`.

Cel: sprawdzenie kompletnego pipeline'u, promptu, walidatora i metryk. Wynik nie
jest reprezentatywny dla docelowego modelu 4B i nie zostanie użyty jako wynik
końcowy szkolenia.

Pomiar wykonano na 10 przypadkach walidacyjnych. Dwa wcześniej obejrzane
przypadki zostały przeniesione do splitu `development`. Split `test` nie został
użyty.

## Wyniki

| Metryka | Zero-shot | Few-shot |
|---|---:|---:|
| Poprawny JSON | 100% | 100% |
| Zgodność ze schematem | 0% | 90% |
| Poprawne identyfikatory źródeł | 100% | 100% |
| Poprawny typ kontroli | 10% | 100% |
| Poprawny status | 30% | 40% |
| Poprawna istotność | 30% | 30% |
| Poprawna decyzja o human review | 0% | 30% |
| Evidence precision | 100% | 90% |
| Evidence recall | 73,3% | 83,3% |
| Średnia liczba tokenów wejścia | 781 | 2013 |
| Średnia latencja generacji | 6,15 s | 5,80 s |

Latencji nie należy interpretować jako przewagi few-shot. Pomiar obejmuje tylko
pojedynczy przebieg, a wariant few-shot generował krótsze odpowiedzi.

## Najważniejsze obserwacje

1. Dwie demonstracje niemal rozwiązały problem formatu: schema validity wzrosło
   z 0% do 90%.
2. Poprawny format nie przełożył się na poprawne decyzje. Status accuracy
   wzrosło tylko z 30% do 40%.
3. Model wykazywał silny bias do `PASS`: oznaczył jako PASS przypadki z
   brakującymi danymi, niepełnym ujawnieniem i nieuzasadnioną wariancją.
4. Zero-shot często kopiował opis kontraktu zamiast wartości z wejścia lub
   używał tekstu tam, gdzie schemat wymagał obiektu.
5. Mały model generował zniekształcone polskie znaki w części pól. To osobny
   wymiar oceny jakości językowej.
6. Tryb thinking w modelu smoke musiał zostać jawnie wyłączony. W pierwszej
   próbie zużywał limit tokenów na rozumowanie i ucinał odpowiedź przed
   zakończeniem JSON-a.

## Wniosek dydaktyczny

Ten eksperyment daje mocne otwarcie warsztatu:

> Model może poprawnie wyjaśnić problem i jednocześnie nie nadawać się do
> automatycznego procesu kontrolnego.

Poprawny JSON, poprawne cytowanie źródeł i trafna decyzja są niezależnymi
wymiarami. Benchmark musi raportować je osobno.

## Następny eksperyment

1. Uruchomić B0/B1/B2 na docelowym modelu 4B.
2. Zamrozić prompt i parametry dekodowania przed użyciem splitu testowego.
3. Rozszerzyć zbiór treningowy, zachowując obecne 40 przypadków jako zestaw
   diagnostyczny.
4. Przeprowadzić QLoRA i porównać ją z najlepszym baseline'em promptowym.

