[CmdletBinding()]
param(
    [ValidateSet("preflight", "train", "inspect", "validation", "all")]
    [string]$Phase = "preflight"
)

$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptRoot
Set-Location -LiteralPath $projectRoot

$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Brak .venv. Uruchom: uv sync --extra llm --extra train"
}

$matrixPath = Join-Path $projectRoot "configs\sprint4_matrix_v1.json"
$matrix = Get-Content -Raw -LiteralPath $matrixPath | ConvertFrom-Json
$newSeeds = @($matrix.seeds | Where-Object { $_.role -eq "train" })

function Invoke-Python {
    param([string[]]$Arguments)
    & $pythonPath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Polecenie Python zakończyło się kodem ${LASTEXITCODE}: $($Arguments -join ' ')"
    }
}

function Test-CompletedTraining {
    param($SeedSpec)
    $metricsPath = Join-Path $projectRoot $SeedSpec.training_metrics
    $adapterWeights = Join-Path (Join-Path $projectRoot $SeedSpec.adapter) "adapter_model.safetensors"
    $configPath = Join-Path $projectRoot $SeedSpec.config
    if (-not (Test-Path -LiteralPath $metricsPath) -or -not (Test-Path -LiteralPath $adapterWeights)) {
        return $false
    }
    $metrics = Get-Content -Raw -LiteralPath $metricsPath | ConvertFrom-Json
    $configHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $configPath).Hash.ToLowerInvariant()
    return $metrics.status -eq "completed" -and
        $metrics.token_stats.truncated_case_count -eq 0 -and
        $metrics.config_sha256 -eq $configHash
}

function Test-CompletedEvaluation {
    param($SeedSpec, [string]$MetricsPath, [int]$ExpectedCount)
    $resolved = Join-Path $projectRoot $MetricsPath
    if (-not (Test-Path -LiteralPath $resolved)) {
        return $false
    }
    $metrics = Get-Content -Raw -LiteralPath $resolved | ConvertFrom-Json
    $config = Get-Content -Raw -LiteralPath (Join-Path $projectRoot $SeedSpec.config) | ConvertFrom-Json
    return $metrics.aggregate.count -eq $ExpectedCount -and
        $metrics.metadata.adapter_id -eq $config.id -and
        -not $metrics.metadata.protected_split_authorized
}

function Invoke-Preflight {
    Invoke-Python -Arguments @(
        "-m", "peft_workshop.sprint4_preflight",
        "--matrix", "configs/sprint4_matrix_v1.json",
        "--output", "results/sprint4/preflight.json"
    )
}

function Invoke-TrainingRuns {
    foreach ($seedSpec in $newSeeds) {
        if (Test-CompletedTraining -SeedSpec $seedSpec) {
            Write-Host "SKIP: trening $($seedSpec.name) jest kompletny."
            continue
        }
        Write-Host "START: trening $($seedSpec.name)."
        Invoke-Python -Arguments @("-m", "peft_workshop.train", "--config", $seedSpec.config)
    }
}

function Invoke-AdapterInspection {
    foreach ($seedSpec in $newSeeds) {
        if (-not (Test-CompletedTraining -SeedSpec $seedSpec)) {
            throw "Brak kompletnego treningu $($seedSpec.name); inspekcja zatrzymana."
        }
        Invoke-Python -Arguments @(
            "-m", "peft_workshop.adapter_ops", "inspect",
            "--config", $seedSpec.config,
            "--output", $seedSpec.adapter_manifest
        )
    }
}

function Invoke-ValidationRuns {
    foreach ($seedSpec in $newSeeds) {
        if (-not (Test-CompletedTraining -SeedSpec $seedSpec)) {
            throw "Brak kompletnego treningu $($seedSpec.name); validation zatrzymane."
        }
        if (-not (Test-CompletedEvaluation -SeedSpec $seedSpec -MetricsPath $seedSpec.original_validation_metrics -ExpectedCount 50)) {
            Invoke-Python -Arguments @(
                "-m", "peft_workshop.adapter_inference",
                "--config", $seedSpec.config,
                "--data", $matrix.allowed_validation.original,
                "--output", $seedSpec.original_validation_output
            )
            Invoke-Python -Arguments @(
                "-m", "peft_workshop.cli", "evaluate", $seedSpec.original_validation_output,
                "--data", $matrix.allowed_validation.original,
                "--output", $seedSpec.original_validation_metrics
            )
        } else {
            Write-Host "SKIP: original validation $($seedSpec.name) jest kompletne."
        }
        if (-not (Test-CompletedEvaluation -SeedSpec $seedSpec -MetricsPath $seedSpec.boundary_validation_metrics -ExpectedCount 120)) {
            Invoke-Python -Arguments @(
                "-m", "peft_workshop.adapter_inference",
                "--config", $seedSpec.config,
                "--data", $matrix.allowed_validation.boundary,
                "--output", $seedSpec.boundary_validation_output
            )
            Invoke-Python -Arguments @(
                "-m", "peft_workshop.cli", "evaluate", $seedSpec.boundary_validation_output,
                "--data", $matrix.allowed_validation.boundary,
                "--output", $seedSpec.boundary_validation_metrics
            )
        } else {
            Write-Host "SKIP: boundary validation $($seedSpec.name) jest kompletne."
        }
    }
    Invoke-Python -Arguments @("-m", "peft_workshop.sprint4_report")
}

switch ($Phase) {
    "preflight" { Invoke-Preflight }
    "train" {
        Invoke-Preflight
        Invoke-TrainingRuns
    }
    "inspect" { Invoke-AdapterInspection }
    "validation" { Invoke-AdapterInspection; Invoke-ValidationRuns }
    "all" {
        Invoke-Preflight
        Invoke-TrainingRuns
        Invoke-AdapterInspection
        Invoke-ValidationRuns
    }
}
