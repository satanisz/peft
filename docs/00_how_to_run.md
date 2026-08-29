# Uruchomienie projektu

## Wymagania

- Windows z aktualnym sterownikiem NVIDIA,
- `uv`,
- Python 3.12 instalowany automatycznie przez `uv`,
- dla profilu LLM: GPU NVIDIA lub wystarczająca ilość RAM dla CPU.

Systemowy Python 3.14 nie jest używany przez projekt. Plik `.python-version`
przypina wspieraną linię Pythona 3.12.

## Instalacja lekkiej warstwy

```powershell
uv sync
uv run peft-workshop generate
uv run peft-workshop validate-data
uv run python -m unittest discover -s tests -v
```

Ta warstwa obejmuje generator danych, schematy, walidację i metryki. Nie
instaluje PyTorch ani nie wymaga GPU.

## Instalacja warstwy LLM

```powershell
uv sync --extra llm
uv run peft-preflight
```

PyTorch jest pobierany z oficjalnego indeksu CUDA 12.8. Model zostanie pobrany
przy pierwszym uruchomieniu. Token Hugging Face nie jest wymagany dla wybranych
modeli, ale zwiększa limity pobierania.

## Oglądanie promptu

```powershell
uv run peft-workshop show-prompt FC-003 --variant B0
uv run peft-workshop show-prompt FC-003 --variant B1
uv run peft-workshop show-prompt FC-003 --variant B2
```

## Baseline smoke

Zero-shot na splicie walidacyjnym:

```powershell
uv run peft-baseline `
  --profile smoke `
  --variant B1 `
  --split validation `
  --output results/b0_smoke_zero_shot_validation.jsonl

uv run peft-workshop evaluate `
  results/b0_smoke_zero_shot_validation.jsonl `
  --output results/b0_smoke_zero_shot_validation_metrics.json
```

Few-shot:

```powershell
uv run peft-baseline `
  --profile smoke `
  --variant B2 `
  --split validation `
  --output results/b2_smoke_few_shot_validation.jsonl

uv run peft-workshop evaluate `
  results/b2_smoke_few_shot_validation.jsonl `
  --output results/b2_smoke_few_shot_validation_metrics.json
```

Profil `smoke` służy do testu przepływu, nie do wyznaczania docelowej jakości.
Formalny benchmark na splicie `test` wykonamy dopiero dla przypiętego modelu 4B,
po zamrożeniu promptu i konfiguracji.

## Zamrożony baseline 4B

Przykład odtworzenia B1 na splicie validation:

```powershell
$env:HF_HUB_OFFLINE = "1"
uv run peft-baseline `
  --profile workshop `
  --variant B1 `
  --split validation `
  --data data/generated/dataset_v1.jsonl `
  --output results/b1_4b_validation.jsonl

uv run peft-workshop evaluate `
  results/b1_4b_validation.jsonl `
  --data data/generated/dataset_v1.jsonl `
  --output results/b1_4b_validation_metrics.json
```

Analogicznie uruchamiamy B0 i B2. Zamrożone ustawienia znajdują się w
`configs/baseline_v1.json`, a pełne wyniki w `docs/08_sprint_2_report.md`.

## Dataset-v1

```powershell
uv run peft-generate-dataset --mode pilot
uv run peft-audit-dataset `
  --data data/pilot/dataset_v1_pilot.jsonl `
  --json-output results/dataset_v1_pilot_audit.json `
  --markdown-output results/dataset_v1_pilot_audit.md

uv run peft-generate-dataset --mode full
uv run peft-audit-dataset --data data/generated/dataset_v1.jsonl
uv run peft-token-stats --data data/generated/dataset_v1.jsonl
```

Pełny generator zapisuje plik zbiorczy oraz oddzielne pliki dla każdego splitu.
Karta danych znajduje się w `data/DATASET_CARD.md`.

## Boundary pack i baseline B3

```powershell
uv run peft-generate-boundary
uv run peft-workshop validate-data `
  --data data/generated/boundary_pack_v1.jsonl

uv run peft-baseline `
  --profile workshop `
  --variant B3 `
  --split validation `
  --data data/generated/boundary_pack_v1.jsonl `
  --output results/b3_boundary_validation.jsonl

uv run peft-workshop evaluate `
  results/b3_boundary_validation.jsonl `
  --data data/generated/boundary_pack_v1.jsonl `
  --output results/b3_boundary_validation_metrics.json
```

B3 używa pięcioetykietowej hierarchii decyzji oraz trzech stałych przykładów z
boundary train dla najtrudniejszych statusów: `WARN`, `NOT_APPLICABLE` i
`INSUFFICIENT_DATA`. Pełny wariant pięciu demonstracji został odrzucony przez
smoke test pamięci. Boundary `test`, oryginalny `test` oraz `challenge`
pozostają zamknięte.

## Sprint 3 — QLoRA

```powershell
uv sync --extra llm --extra train
uv run peft-preflight --output results/sprint3/environment.json
```

Instaluje PEFT, TRL, datasets i bitsandbytes. Suche przebiegi sprawdzają
lineage, rozkład etykiet oraz to, że pipeline otwiera wyłącznie train:

```powershell
uv run peft-train --config configs/qlora_q0_v1.json --dry-run
uv run peft-train --config configs/qlora_q1_v1.json --dry-run
```

Rzeczywisty trening pokazowy:

```powershell
uv run peft-train --config configs/qlora_demo_v1.json
```

Pełne kontrolowane treningi referencyjne:

```powershell
uv run peft-train --config configs/qlora_q0_v1.json
uv run peft-train --config configs/qlora_q1_v1.json
```

Q0 używa wyłącznie 400 rekordów train v1. Q1 dodaje 240 rekordów boundary
train; pozostałe parametry są identyczne. Maksymalna długość 1728 pokrywa
zmierzone maksimum 1672 tokenów, a pipeline zatrzyma trening przy jakimkolwiek
obcięciu. Checkpointy referencyjne zapisują model-only: umożliwiają inferencję,
ale nie przechowują stanu optymalizatora do automatycznego resume. Jest to
świadomy workaround dla kosztownej serializacji `paged_adamw_8bit` na Windows.

Ponowne ładowanie i inferencja na dozwolonym validation:

```powershell
uv run peft-adapter `
  --config configs/qlora_q1_v1.json `
  --data data/generated/dataset_v1/validation.jsonl `
  --output results/sprint3/q1_original_validation.jsonl

uv run peft-adapter `
  --config configs/qlora_q1_v1.json `
  --data data/splits/boundary_validation.jsonl `
  --output results/sprint3/q1_boundary_validation.jsonl
```

Ocena używa tego samego narzędzia co baseline:

```powershell
uv run peft-workshop evaluate `
  results/sprint3/q1_original_validation.jsonl `
  --data data/generated/dataset_v1/validation.jsonl `
  --output results/sprint3/q1_original_validation_metrics.json

uv run peft-workshop evaluate `
  results/sprint3/q1_boundary_validation.jsonl `
  --data data/splits/boundary_validation.jsonl `
  --output results/sprint3/q1_boundary_validation_metrics.json
```

Inspekcja, scalenie i formalna bramka M3:

```powershell
uv run peft-adapter-ops inspect `
  --config configs/qlora_q1_v1.json `
  --output results/sprint3/q1_adapter_manifest.json

uv run peft-adapter-ops merge `
  --config configs/qlora_q1_v1.json `
  --output artifacts/merged/q1-v0.1-bf16 `
  --manifest results/sprint3/q1_merge_manifest.json

uv run peft-adapter `
  --config configs/qlora_q1_v1.json `
  --merged-model artifacts/merged/q1-v0.1-bf16 `
  --data data/generated/dataset_v1/development.jsonl `
  --limit 1 `
  --output results/sprint3/q1_merged_reload_smoke.jsonl

uv run peft-sprint3-report
```

Wagi w `artifacts/`, checkpointy oraz model scalony są lokalne i ignorowane
przez Git. Repozytorium przechowuje konfiguracje, hashe, metryki i manifesty.
Oryginalny test, boundary test i challenge pozostają zamknięte do Sprintu 4.

Preflight oraz raporty treningowe zapisują środowisko, zużycie pamięci,
przepustowość, długości tokenów, trainable parameters i hashe artefaktów.

## Sprint 4 — trzy seedy i evidence package

Sprint 4 wykorzystuje adapter Q1 z M3 jako pierwszy seed i trenuje tylko dwa
brakujące seedy. Przed długim uruchomieniem:

```powershell
.\scripts\run_sprint4_training.ps1 -Phase preflight
```

Oczekiwany wynik to `READY_FOR_TRAINING`. Pełny bezpieczny przebieg otwartych
etapów:

```powershell
.\scripts\run_sprint4_training.ps1 -Phase all
```

Faza `all` wykonuje kolejno preflight, dwa treningi, inspekcję adapterów,
original validation, boundary validation i bramkę pre-test. Jest wznawialna na
poziomie ukończonych artefaktów. Nie otwiera original test, boundary test ani
challenge.

Można też uruchamiać etapy oddzielnie:

```powershell
.\scripts\run_sprint4_training.ps1 -Phase train
.\scripts\run_sprint4_training.ps1 -Phase inspect
.\scripts\run_sprint4_training.ps1 -Phase validation
```

Sam wynik `READY_TO_OPEN_PROTECTED_SPLITS` z automatycznej bramki nie wystarcza.
Review Sol/high z 28 sierpnia 2026 ustawił analityczną decyzję
`HOLD_FOR_EVIDENCE_HARDENING`. Najpierw należy wykonać Sprint 4.2A opisany w
`docs/15_sprint_4_2a_executive_plan.md`. Dopiero po zmianie wersjonowanej bramki
na `APPROVED_TO_OPEN_PROTECTED_SPLITS` można uruchomić:

```powershell
.\scripts\run_sprint4_evidence.ps1 -ConfirmOpenProtectedSplits
```

Bez przełącznika, bez raportu pre-test, przy decyzji STOP albo przy analitycznym
HOLD skrypt kończy się przed odczytem chronionych danych. Szczegóły metodologiczne i progi zawiera
[`13_sprint_4_executive_plan.md`](13_sprint_4_executive_plan.md).

## Sprint 4.2A — przygotowanie i diagnostic

Na Sol/high można bez GPU wykonać audyt danych, analizę severity oraz Q2 guard
na istniejących validation:

```powershell
.\scripts\run_sprint4_2a.ps1 -Phase prepare
```

Oczekiwany status przed review to `HOLD_PENDING_INDEPENDENT_REVIEW`. Formalna
inferencja pozostaje zablokowana, dopóki
`data/reviews/diagnostic_set_v1_review.json` nie potwierdzi niezależnego review
30/30 przypadków.

Po zatwierdzeniu review przełączyć Codex na Luna/low i uruchomić:

```powershell
.\scripts\run_sprint4_2a.ps1 -Phase diagnostic
```

Po zakończeniu wrócić na Sol/high. Wynik
`READY_FOR_SOL_HIGH_APPROVAL_REVIEW` nie otwiera testów automatycznie; wymaga
oddzielnej decyzji i commita bramki protected evidence.

Sprint 4.2A zakończył się decyzją `HOLD_DIAGNOSTIC_THRESHOLDS`. Analiza per
przypadek wykazała drift kontraktu severity i nadmierne użycie WARN, dlatego
Sprint 4.2B wykonuje prompt-only ablation bez kolejnego treningu. Najpierw na
Sol/high przygotować i zwalidować eksperyment:

```powershell
.\scripts\run_sprint4_2b_prompt_rerun.ps1 -Phase prepare
```

Po ponownym review poprawki `FC-209` przez SME przełączyć Codex na Luna/low:

```powershell
.\scripts\run_sprint4_2b_prompt_rerun.ps1 -Phase rerun
```

Runner zachowuje baseline v1, zapisuje osobne wyniki promptu v2 i porównuje 29
niezmienionych przypadków. `FC-209` raportuje osobno. Protected splits pozostają
zamknięte.

Sprint 4.2B zakończył się decyzją `HOLD_PROMPT_V2_THRESHOLDS`. Prompt v2
ustabilizował severity, review oraz source integrity, ale wszystkie trzy seedy
poprawnie obliczyły 27 mln PLN w FC-209 i mimo to zwróciły `PASS` przy progu
5 mln PLN. Sprint 4.2C demonstruje blokadę takiej sprzeczności przez regułę
deterministyczną, bez kolejnej inferencji:

```powershell
.\scripts\run_sprint4_2c_guard.ps1
```

Oczekiwany wynik to `READY_FOR_SPRINT5_DEMO_WITH_PROTECTED_HOLD`: FC-209 jest
blokowany i kierowany do człowieka we wszystkich seedach, a pozostałe 29
odpowiedzi przechodzi bez zmian. Reguła powstała po analizie diagnostycznej,
więc nie jest podstawą do otwarcia protected evidence. Szczegóły zawiera
[`17_sprint_4_2c_deterministic_guard.md`](17_sprint_4_2c_deterministic_guard.md).

## Sprint 6 — S6-G0 Evidence Contract Freeze

M5 jest zamknięta tagiem `content-freeze-v1`. Na Sol/high uruchom bramkę G0:

```powershell
.\scripts\run_sprint6_g0.ps1
```

Skrypt wykonuje testy, kompiluje komórki notebooków, sprawdza 53 slajdy z
notatkami i źródłami, zgodność trzech adapterów z manifestami, progi evidence,
status M4/4.2C oraz brak wyników chronionych. Sprawdza jedynie istnienie ścieżek
protected — nie czyta treści przypadków ani goldów.

Oczekiwany wynik to `S6_G0_PASS` zapisany w
`results/sprint6/g0_preflight.json`. Jest to zgoda wyłącznie na przygotowanie i
review `shadow-challenge-v1`. Nie pozwala jeszcze otworzyć protected evidence.

Runner chronionych danych wymaga kolejno `S6_G0_PASS`, `S6_G1_PASS`,
`S6_G2_PASS`, osobnego commita z decyzją `APPROVED_TO_OPEN_PROTECTED_SPLITS` i
jawnego parametru operatora.

## Sprint 6 — S6-G1 Shadow freeze

Authoring, audyt podobieństwa i kontrolę wspomaganą uruchamia Sol/high:

```powershell
.\scripts\run_sprint6_g1.ps1 -Phase all
```

Bez niezależnego review oczekiwany wynik to
`S6_G1_HOLD_PENDING_HUMAN_SME`. Człowiek/SME sprawdza 50/50 przypadków w
`data/reviews/shadow_challenge_v1_review.json`, podpisuje review i rozstrzyga
wszystkie uwagi. Następnie uruchamia samą bramkę:

```powershell
.\scripts\run_sprint6_g1.ps1 -Phase gate
```

G1 PASS pozwala rozpocząć wyłącznie próbę techniczną S6-G2 na Luna/low. Nie
pozwala jeszcze otworzyć protected evidence.

**Bieżący stan projektu:** człowiek/SME zatwierdził 50/50 goldów, a bramka
wydała `S6_G1_PASS`. Generator tej wersji jest zablokowany przed nadpisaniem;
należy przejść do S6-G2.

Po wygenerowaniu evidence należy skopiować i uzupełnić szablon review:

```powershell
Copy-Item `
  configs/sprint4_challenge_review_template.json `
  results/sprint4/challenge_manual_review.json

uv run peft-sprint4-evidence-report
```

Raport nie wydaje automatycznej decyzji M4 PASS; kieruje wynik do review
Sol/high.
