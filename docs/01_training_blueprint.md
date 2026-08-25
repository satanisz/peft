# Specyfikacja szkolenia

## Cel

Uczestnik ma zrozumieć, kiedy PEFT daje wartość biznesową, jak działa LoRA i
QLoRA oraz jak zaprojektować wiarygodny eksperyment dostrajania LLM. Szkolenie
nie kończy się na spadającym `training_loss`: prowadzi do oceny jakości,
bezpieczeństwa, kosztu i gotowości rozwiązania do dalszego rozwoju.

## Odbiorcy i forma

- 15 osób na poziomie średniozaawansowanym,
- znajomość Pythona, podstaw ML i ogólnej architektury transformera,
- jedna demonstracja wykonywana przez prowadzącego,
- uczestnicy analizują dane, konfiguracje i wyniki, ale nie konfigurują swoich
  środowisk w trakcie spotkania,
- materiał techniczny jest uzupełniony decyzjami architektonicznymi i
  przypadkami użycia w banku.

## Dwie warstwy materiału

### Ścieżka uczestnika

Uczestnik powinien po szkoleniu umieć:

- odróżnić prompting, RAG, SFT, continued pretraining i PEFT,
- wyjaśnić ideę aktualizacji niskiego rzędu,
- rozumieć rolę `rank`, `alpha`, modułów docelowych i kwantyzacji,
- przeczytać konfigurację LoRA/QLoRA,
- zinterpretować wyniki benchmarku,
- wskazać wartościowe i ryzykowne zastosowania bankowe.

### Ścieżka prowadzącego — poziom zaawansowany

Prowadzący powinien dodatkowo opanować:

- dokładne liczenie parametrów adaptera dla warstw transformera,
- pamięć wag, gradientów, stanów optymalizatora i aktywacji,
- gradient checkpointing, mixed precision i wpływ długości sekwencji,
- różnicę między kwantyzacją przechowywania a typem obliczeń,
- NF4, double quantization i przygotowanie modelu do k-bit training,
- dobór modułów `q/k/v/o` i MLP oraz konsekwencje `all-linear`,
- chat templates, maskowanie lossu i packing przykładów,
- adaptery niescalone i scalone oraz wpływ na inferencję,
- rsLoRA, DoRA, AdaLoRA i IA3 na poziomie umożliwiającym odpowiedzi na pytania,
- metodologię ablation study, kontrolę leakage i analizę regresji.

## Agenda — 180 minut

| Minuty | Moduł | Rezultat |
|---:|---|---|
| 0–10 | Problem bankowy i odpowiedź modelu bazowego | wspólna definicja sukcesu |
| 10–25 | Prompt, RAG, SFT czy PEFT? | drzewo decyzji |
| 25–50 | LoRA od strony matematycznej i implementacyjnej | zrozumienie konfiguracji |
| 50–68 | QLoRA i pamięć GPU | zrozumienie przepływu treningu |
| 68–80 | DoRA, rsLoRA, AdaLoRA, IA3, prompt/prefix tuning | mapa alternatyw |
| 80–90 | Przerwa | — |
| 90–105 | Dane i baseline | jawny punkt odniesienia |
| 105–132 | Demonstracja QLoRA | działający adapter |
| 132–148 | Inferencja, zapis i scalanie adaptera | artefakt do użycia |
| 148–168 | Benchmark i analiza błędów | ocena jakości i kosztu |
| 168–177 | Zastosowania, ryzyka i wdrożenie w banku | decyzje biznesowe |
| 177–180 | Podsumowanie | trzy najważniejsze wnioski |

## Główna narracja

1. Model bazowy otrzymuje realistyczne zadanie kontrolne i popełnia mierzalne
   błędy.
2. Dobry prompt poprawia część wyników, dlatego stanowi obowiązkowy baseline.
3. RAG dostarcza aktualne procedury i fakty, ale nie gwarantuje poprawnego
   sposobu wykonania kontroli ani formatu raportu.
4. QLoRA uczy stabilnego zachowania: klasyfikacji, formatu, cytowania dowodów,
   eskalacji i odmowy przy braku danych.
5. Kod deterministyczny wykonuje obliczenia; LLM interpretuje wyniki i tworzy
   ustalenie kontrolne.
6. Dopiero benchmark pokazuje, czy adapter ma wartość.

## Proporcje treści

- 35% teoria i mechanika PEFT,
- 35% demonstracja techniczna,
- 20% benchmark, analiza błędów i metodologia,
- 10% zastosowania biznesowe, ryzyko i operacjonalizacja.

## Zasady demonstracji

- wszystkie modele, dane i wersje bibliotek są pobrane przed szkoleniem,
- pełny trening referencyjny jest wykonany wcześniej,
- podczas szkolenia uruchamiany jest krótki, rzeczywisty trening pokazowy,
- gotowy adapter umożliwia kontynuację przy awarii GPU,
- każda demonstracja ma zapisany oczekiwany wynik i wariant awaryjny,
- uczestnicy widzą także przykłady, w których dostrojony model jest gorszy.

## Wartość biznesowa

W każdej części technicznej odpowiadamy na trzy pytania:

1. Jaki proces bankowy może na tym skorzystać?
2. Jaki koszt lub ryzyko rozwiązanie redukuje?
3. Co musi pozostać kontrolą deterministyczną albo decyzją człowieka?

