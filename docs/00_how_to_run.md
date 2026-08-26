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

## Warstwa treningowa — późniejszy etap

```powershell
uv sync --extra llm --extra train
```

Instaluje PEFT, TRL, datasets i bitsandbytes. Przed treningiem powstaną osobne
skrypty preflight dla kwantyzacji NF4 i pomiaru pamięci GPU.
