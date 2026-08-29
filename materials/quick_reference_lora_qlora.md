# LoRA i QLoRA — ściąga warsztatowa

## 1. Najpierw wybierz właściwą interwencję

| Problem | Pierwszy wybór | Kiedy rozważyć PEFT |
|---|---|---|
| Wiedza zmienia się często i trzeba cytować źródło | RAG | Gdy dodatkowo trzeba ustabilizować format lub zachowanie |
| Stabilny format, etykiety i sposób rozumowania | prompt/few-shot, potem PEFT | Gdy prompt nie daje stabilnego kontraktu |
| Jedna jawna reguła liczbowa lub zakaz | kod deterministyczny | Nie zastępuj reguły adapterem |
| Nowy język lub szeroka domena | continued pretraining + RAG/SFT | Gdy brakuje reprezentacji domeny, nie tylko formatu |

PEFT jest dobrym kandydatem, gdy wiedza jest względnie stabilna, zachowanie jest
powtarzalne, a pełny fine-tuning byłby zbyt drogi albo trudny w wersjonowaniu.

## 2. LoRA w jednym równaniu

Zamrożona macierz `W` dostaje małą aktualizację:

`W' = W + (alpha / r) * B * A`

- `r` — rank; zwiększa pojemność adaptera i koszt pamięciowy,
- `alpha` — skala aktualizacji; interpretuj razem z rankiem,
- `dropout` — regularizacja ścieżki LoRA,
- `target_modules` — miejsca, w których model może zmienić zachowanie,
- adapter — wersjonowany artefakt zależny od dokładnej rewizji modelu bazowego.

Punkt startowy do warsztatu: `r=8–16`, `alpha=2*r`, `dropout=0.05`, a target
modules dobieraj świadomie. `all-linear` daje dużą swobodę, ale zwiększa liczbę
parametrów i zakres możliwych zmian.

## 3. Co QLoRA dodaje do LoRA

QLoRA przechowuje zamrożone wagi modelu bazowego w 4 bitach, natomiast
obliczenia i adapter nie muszą być 4-bitowe. Typ przechowywania i typ obliczeń
to dwa różne ustawienia.

- NF4: format kwantyzacji przeznaczony dla wag o rozkładzie zbliżonym do normalnego,
- double quantization: kompresuje także stałe kwantyzacji,
- BF16 compute: stabilny wybór na wspieranym GPU,
- paged optimizer: ogranicza skoki pamięci, nie zastępuje kontroli aktywacji,
- gradient checkpointing: oszczędza pamięć kosztem dodatkowych obliczeń.

Pamięć GPU zużywają: baza, adapter, aktywacje, gradienty, stan optymalizatora,
bufory i cache. Sam rozmiar pliku modelu nie przewiduje peak VRAM.

## 4. Wyniki demonstracyjne z tego projektu

| Element | Q1-DEMO | Pełny Q1 |
|---|---:|---:|
| Rank / alpha | 8 / 16 | 16 / 32 |
| Kroki | 12 | 240 |
| Czas treningu | 114,361 s | 5301,854 s |
| Peak GPU allocated | 7,487 GiB | 7,551 GiB |
| Wagi adaptera | 33,1 MB | 66,1 MB |
| Cel | pipeline i reload | wynik eksperymentalny |

Demo wykorzystało 50 przypadków, wszystkie pięć statusów i zero truncation.
Fresh reload przeszedł 1/1 przy `max_new_tokens=384`. To test używalności
artefaktu, a nie dowód generalizacji.

## 5. Minimalny kontrakt eksperymentu

1. Przypnij model, rewizję, prompt, dane i seed.
2. Rozdziel rodziny przypadków przed splitami; parafrazy nie mogą przeciekać.
3. Zapisz rozkład klas, tokeny i liczbę uciętych przykładów przed treningiem.
4. Porównaj z promptem, few-shot i RAG/kodem, nie tylko z innym adapterem.
5. Raportuj co najmniej trzy seedy dla głównego kandydata.
6. Mierz JSON/schema, statusy per klasa, minimalne pary, koszt biznesowy i źródła.
7. Reloaduj adapter w świeżym procesie i sprawdź zgodność modelu bazowego.
8. Testów chronionych nie używaj do strojenia ani projektowania reguł.

## 6. Czerwone flagi

- wysoki accuracy przy klasie dominującej i brak macro-F1,
- perfekcyjna validation z rodzinami wspólnymi dla train i validation,
- `WARN` i `NOT_APPLICABLE` bez osobnego recall,
- poprawny JSON traktowany jako poprawna decyzja,
- wybór najlepszego seeda po wyniku testowym,
- guard napisany po zobaczeniu błędu przedstawiany jako niezależny dowód,
- merge bez manifestu i testu świeżego reloadu,
- decyzja wysokiego wpływu wykonywana bez kodu kontrolnego i człowieka.

## 7. Reguła bankowa

LLM proponuje interpretację i uzasadnienie. Kod sprawdza twarde reguły,
schemat, zakresy i spójność źródeł. Człowiek zatwierdza działanie o istotnym
wpływie. Adapter nie jest samodzielnym systemem kontroli.

