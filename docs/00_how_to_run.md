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
uv run peft-workshop show-prompt FC-003 --mode zero-shot
uv run peft-workshop show-prompt FC-003 --mode few-shot
```

## Baseline smoke

Zero-shot na splicie walidacyjnym:

```powershell
uv run peft-baseline `
  --profile smoke `
  --mode zero-shot `
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
  --mode few-shot `
  --split validation `
  --output results/b2_smoke_few_shot_validation.jsonl

uv run peft-workshop evaluate `
  results/b2_smoke_few_shot_validation.jsonl `
  --output results/b2_smoke_few_shot_validation_metrics.json
```

Profil `smoke` służy do testu przepływu, nie do wyznaczania docelowej jakości.
Formalny benchmark na splicie `test` wykonamy dopiero dla przypiętego modelu 4B,
po zamrożeniu promptu i konfiguracji.

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

## Warstwa treningowa — późniejszy etap

```powershell
uv sync --extra llm --extra train
```

Instaluje PEFT, TRL, datasets i bitsandbytes. Przed treningiem powstaną osobne
skrypty preflight dla kwantyzacji NF4 i pomiaru pamięci GPU.
