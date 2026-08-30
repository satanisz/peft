# S6.6A — automatyczna próba techniczna

Data próby: 2026-08-30  
Wynik bramki: **S6_G2_1_PASS / S6.6A PASS**

## Zakres

Próba została wykonana na zamrożonych artefaktach warsztatowych. Nie uruchamiano
protected evidence, nie zmieniano progów i nie wykonywano rerunu Evidence v1.

## Wyniki automatyczne

- test suite: **91/91 PASS**;
- notebooki: **3/3**, 13 komórek kodu wykonanych bez błędów;
- trening w notebooku QLoRA: **nieuruchomiony** (`RUN_TRAINING=False`);
- lokalny odczyt dokładnej rewizji modelu: **PASS**, 3/3 shardów i 398 tensorów;
- komplet adaptera: **7/7 plików**;
- kontrolowane fallbacki: **4/4 PASS** (OOM, brak modelu, błąd checkpointu, tryb offline);
- czysta instalacja offline: **PASS**, bez połączenia sieciowego;
- audyt źródeł treningowych: **PASS**, protected i shadow nie występują w konfiguracjach treningowych;
- czas demonstracyjnego treningu referencyjnego: 114,361 s, 12/12 kroków, bez truncation.

Pełny maszynowy wynik znajduje się w
`results/sprint6/s6_6a_g2_rehearsal.json`.

## Materiały i bezpieczeństwo demonstracji

Potwierdzono obecność głównego decku, czteroslajdowego appendixu, guide'a oraz
trzech notebooków. W źródłach live demo nie ma wywołań runnera protected evidence,
autoryzacji otwarcia splitów ani flagi `--allow-protected-split`.

## Decyzja

S6.6A można zamknąć jako **PASS**. Środowisko i scenariusz są gotowe do
S6.6B — ręcznej próby prowadzącego. Wynik benchmarku Evidence v1 pozostaje
uczciwie oznaczony jako FAILED; ten etap nie jest zgodą produkcyjną.
