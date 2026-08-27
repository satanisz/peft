# Sprint 4 — zrewidowany executive plan po M3

## Decyzja wykonawcza

Sprint 4 wymaga zmiany. M3 rozstrzygnął już główną ablation Q0 kontra Q1:
boundary data poprawiły macro-F1 o 0,214 i pair accuracy o 38,3 pp. Powtarzanie
Q0, automatyczny Q1b i szeroki sweep ranku nie zwiększają teraz najważniejszej
wartości dowodowej. Największym ryzykiem jest generalizacja perfekcyjnego wyniku
Q1 poza syntetyczne wzorce oraz stabilność między seedami.

Nowy Sprint 4 jest podzielony na dwa kontrakty:

1. **Replication contract** — trzy seedy Q1, z czego wynik M3 jest seedem 1,
   a trenujemy tylko dwa brakujące seedy.
2. **Evidence contract** — po zamrożeniu konfiguracji jednokrotnie otwieramy
   testy i challenge, bez wybierania najlepszego seeda i bez dostrajania na
   wyniku testowym.

## Co zmieniono względem poprzedniego planu

| Element | Poprzednio | Teraz |
|---|---|---|
| Q0 | ponowny element macierzy | wynik Sprintu 3 jest zamrożoną ablation |
| Q1 | trzy nowe treningi | istniejący seed + dwa nowe treningi |
| Q1b | wariant naprawczy | wyłączony; tylko po review Sol/high |
| L1 BF16 | element główny | opcjonalny smoke/ablation, nie blokuje M4 |
| rank/target sweep | priorytetowy | backlog po evidence package |
| wybór seeda | nieprecyzyjny | zakaz wyboru najlepszego; agregujemy wszystkie |
| test | po eksperymentach | jedna operacja po automatycznej bramce pre-test |
| challenge | test adversarial | osobny wynik i obowiązkowy review jakościowy |
| Q2/Q3 | wspólna macierz | Q2 po Q1 jako eksperyment architektoniczny; Q3 do materiałów |

## Zamrożona macierz treningowa

| Rola | Seed | Konfiguracja | Akcja |
|---|---:|---|---|
| Q1-S1 | 20260827 | `qlora_q1_v1.json` | reuse wyniku M3 |
| Q1-S2 | 20260828 | `qlora_q1_seed_20260828_v1.json` | trening |
| Q1-S3 | 20260829 | `qlora_q1_seed_20260829_v1.json` | trening |

Model, rewizja, dane, LoRA, kwantyzacja, optimizer, liczba epok i wszystkie
pozostałe parametry są identyczne. Różnią się tylko seed, identyfikator i ścieżki
artefaktów. Preflight sprawdza tę własność automatycznie.

## Model operacyjny Codex

| Etap | Model | Dlaczego |
|---|---|---|
| projekt i zamrożenie progów | Sol/high | decyzje metodologiczne i ryzyko leakage |
| preflight, trening, inspekcja, validation | Luna/low | mechaniczny, zdeterminowany workflow |
| błąd bramki lub niestabilny seed | Sol/high | analiza przyczyny, zakaz automatycznego tuningu |
| decyzja o otwarciu testu | Sol/high | nieodwracalna utrata statusu „unopened” |
| generowanie evidence po zgodzie | Luna/low | wykonanie zamrożonej macierzy |
| analiza M4 i rekomendacja bankowa | Sol/high | synteza jakości, ryzyka i biznesu |

Luna/low nie podejmuje decyzji o zmianie hiperparametrów, odrzuceniu seeda,
uruchomieniu Q1b ani otwarciu protected splits. [Oficjalna dokumentacja
OpenAI](https://developers.openai.com/api/docs/models/gpt-5.6-luna) opisuje Lunę
jako model do kosztowo wrażliwych, masowych workflow; w projekcie używamy jej
tylko tam, gdzie decyzje zostały wcześniej zakodowane w bramkach.

## Fazy wykonania

### S4.0 — preflight i freeze

- potwierdzenie taga `adapter-v0.1` i referencyjnego commita,
- kontrola czystego źródłowego worktree,
- porównanie kontraktów konfiguracji,
- potwierdzenie train-only lineage i zero dostępu do test/challenge,
- potwierdzenie obecności adaptera seed 1,
- zapis `results/sprint4/preflight.json`.

Warunek wyjścia: `READY_FOR_TRAINING`.

### S4.1 — dwa brakujące treningi

- Q1-S2 i Q1-S3, po 3 epoki / 240 kroków,
- model-only checkpointy co 80 kroków,
- zero truncation, peak VRAM nie więcej niż 12 GiB,
- brak automatycznego resume stanu optymalizatora.

Szacunek na obecnym GPU: około 88–95 minut na seed, łącznie 3–3,5 godziny z
ładowaniem, zapisem i inspekcją. Seed 1 nie jest trenowany ponownie.

### S4.2 — validation i bramka pre-test

- original validation: 50 przypadków dla S2 i S3,
- boundary validation: 120 przypadków dla S2 i S3,
- seed 1 wykorzystuje zamrożone wyniki M3,
- raport: średnia, minimum, maksimum, range i population std,
- zakaz wybierania najlepszego seeda.

Szacunek GPU: około 1,8–2,2 godziny dla dwóch nowych seedów. Bramka zwraca
`READY_TO_OPEN_PROTECTED_SPLITS` albo `STOP_AND_RETURN_TO_SOL_HIGH`.

Ustalane przed wynikiem kryteria obejmują między innymi:

- original macro-F1: mean ≥0,95 i każdy seed ≥0,90,
- boundary macro-F1: mean ≥0,90, każdy seed ≥0,85, range ≤0,10,
- WARN i NOT_APPLICABLE recall każdego seeda ≥0,80,
- pair accuracy każdego seeda ≥0,80,
- FAIL FPR każdego seeda ≤0,15,
- unsafe PASS każdego seeda ≤0,05,
- schema valid każdego seeda ≥0,98.

### S4.3 — jednorazowe protected evidence

Uruchamiane dopiero po review wyniku pre-test i jawnej zgodzie operatora:

- original test: 100 przypadków × 3 seedy,
- boundary test: 120 przypadków × 3 seedy,
- challenge: 20 przypadków × 3 seedy,
- wszystkie seedy raportowane; brak wyboru najlepszego,
- po niepowodzeniu testu raportujemy wynik i nie dostrajamy na test.

Szacunek GPU: około 3,5–4,5 godziny. Challenge wymaga dodatkowo ręcznego review
20 unikalnych przypadków; sama zgodność statusu nie dowodzi odporności na prompt
injection.

Progi protected evidence są zamrożone przed otwarciem danych:

- original test macro-F1: mean ≥0,90 i każdy seed ≥0,85,
- boundary test macro-F1: mean ≥0,85 i każdy seed ≥0,80,
- boundary WARN oraz NOT_APPLICABLE recall każdego seeda ≥0,75,
- boundary pair accuracy każdego seeda ≥0,75,
- boundary FAIL FPR każdego seeda ≤0,15,
- boundary unsafe PASS każdego seeda ≤0,08,
- schema valid na testach każdego seeda ≥0,98,
- challenge status accuracy: mean ≥0,85 i każdy seed ≥0,75,
- challenge schema valid każdego seeda ≥0,95,
- ręczne review wszystkich 20 przypadków i wszystkich 60 odpowiedzi trzech
  seedów oraz zero wykonanych prompt injections.

Szablon review znajduje się w `configs/sprint4_challenge_review_template.json`.
Po uzupełnieniu zapisujemy go jako
`results/sprint4/challenge_manual_review.json`.

### S4.4 — diagnostic set poza szablonami

Przed M4 należy przygotować co najmniej 30 ręcznych przypadków, których treść
nie jest generowana przez `dataset-v1` ani boundary generator:

- 10 kontroli liczbowych z wieloma źródłami,
- 5 przypadków niejednoznacznej stosowalności,
- 5 przypadków brakujących danych,
- 5 przypadków wrogich instrukcji w dokumentach,
- 5 neutralnych lub pozadomenowych regresji.

Zbiór wymaga niezależnego review eksperta. Nie jest źródłem treningowym i nie
może służyć do strojenia konfiguracji Q1.

### S4.5 — Q2 i rekomendacja architektoniczna

Q2 nie wymaga kolejnego treningu. Ten sam adapter Q1 otrzymuje wyniki kontroli
deterministycznych Python/SQL. Porównanie Q1–Q2 ma odpowiedzieć, czy kod usuwa
błędy liczbowe i ogranicza ryzyko biznesowe. Q3 z pełnym kontekstem procedury
pozostaje demonstracją architektury do Sprintu 5, chyba że Q2 ujawni lukę
wymagającą wcześniejszego pomiaru.

## Bramka M4 — Evidence package

M4 może otrzymać PASS dopiero, gdy:

- trzy seedy są kompletne i raportowane bez selekcji,
- configuration freeze i pre-test gate są zapisane,
- test, boundary test i challenge mają oddzielne raporty,
- diagnostic set poza szablonami ma review eksperckie,
- challenge ma review prompt-injection,
- regresja severity z M3 jest wyjaśniona,
- Q1–Q2 zawiera techniczną i biznesową analizę kosztu błędu,
- wszystkie wyniki są powiązane z konfiguracją, commitem i hashem adaptera.

M4 nie jest zgodą produkcyjną; jest pakietem dowodowym do profesjonalnego
szkolenia.

Automatyczny raport protected evidence zwraca wyłącznie:

- `FAILED_EVIDENCE_THRESHOLDS`,
- `PENDING_MANUAL_REVIEW`,
- `READY_FOR_M4_SOL_REVIEW`.

Ostateczna decyzja M4 wymaga Sol/high i jawnego uzasadnienia.

## Polecenia dla Luna/low

Po commicie przygotowawczym:

```powershell
.\scripts\run_sprint4_training.ps1 -Phase preflight
.\scripts\run_sprint4_training.ps1 -Phase all
```

`all` wykonuje wyłącznie preflight, dwa treningi, inspekcję i dozwolone
validation. Nie otwiera testów ani challenge. Po zakończeniu należy wrócić do
Sol/high i przeanalizować `results/sprint4/m4_pretest_summary.md`.

Protected evidence ma osobny, celowo niewygodny interfejs:

```powershell
.\scripts\run_sprint4_evidence.ps1 -ConfirmOpenProtectedSplits
```

Nie uruchamiać go na podstawie samego powodzenia treningu — wymagane są bramka
pre-test i jawna decyzja operatora.

## Plan awaryjny

- przerwanie treningu przed końcem: uruchomić tę samą fazę ponownie; nie używać
  częściowego seeda,
- pełny metrics JSON + adapter: runner bezpiecznie pomija ukończony seed,
- błąd checkpointu: nie zmieniać konfiguracji; wrócić do Sol/high,
- brak VRAM: zatrzymać, nie obniżać ranku ani długości automatycznie,
- słaby pojedynczy seed: raportować i wrócić do Sol/high; nie usuwać go,
- brak READY pre-test: protected splits pozostają zamknięte,
- słaby test: raportować bez ponownego strojenia na test.
