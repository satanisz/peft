[CmdletBinding()]
param(
    [ValidateSet("prepare", "rerun", "compare")]
    [string]$Phase = "prepare"
)

$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptRoot
Set-Location -LiteralPath $projectRoot
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
$matrix = Get-Content -Raw -LiteralPath (Join-Path $projectRoot "configs\sprint4_matrix_v1.json") | ConvertFrom-Json
$diagnosticData = "data/diagnostic/diagnostic_set_v1.jsonl"
$reviewPath = Join-Path $projectRoot "data\reviews\diagnostic_set_v1_review.json"

function Invoke-Python {
    param([string[]]$Arguments)
    & $pythonPath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Polecenie Python zakończyło się kodem ${LASTEXITCODE}: $($Arguments -join ' ')"
    }
}

function Assert-AmendmentReviewApproved {
    $review = Get-Content -Raw -LiteralPath $reviewPath | ConvertFrom-Json
    if ($review.dataset_version -ne "diagnostic-1.0.2" -or
        -not $review.reviewer_independent_from_authoring -or
        $review.summary.reviewed_case_count -ne 30 -or
        $review.summary.approved_case_count -ne 30 -or
        $review.summary.critical_error_count -ne 0 -or
        -not $review.summary.approved_for_q2_validation) {
        throw "Prompt v2 rerun pozostaje zablokowany do review poprawki FC-209 przez SME."
    }
}

function Test-CompletedRerun {
    param([string]$MetricsPath, [string]$ExpectedAdapterId)
    $resolved = Join-Path $projectRoot $MetricsPath
    if (-not (Test-Path -LiteralPath $resolved)) {
        return $false
    }
    $metrics = Get-Content -Raw -LiteralPath $resolved | ConvertFrom-Json
    return $metrics.aggregate.count -eq 30 -and
        $metrics.metadata.adapter_id -eq $ExpectedAdapterId -and
        $metrics.metadata.prompt_contract -eq "v2" -and
        -not $metrics.metadata.protected_split_authorized
}

function Invoke-Compare {
    Invoke-Python -Arguments @("-m", "peft_workshop.sprint4_2b_compare")
}

function Invoke-Rerun {
    Assert-AmendmentReviewApproved
    foreach ($seed in $matrix.seeds) {
        $seedConfig = Get-Content -Raw -LiteralPath (Join-Path $projectRoot $seed.config) | ConvertFrom-Json
        $predictions = "results/sprint4_2b/$($seed.name)_diagnostic_v2.jsonl"
        $metrics = "results/sprint4_2b/$($seed.name)_diagnostic_v2_metrics.json"
        $guarded = "results/sprint4_2b/$($seed.name)_diagnostic_v2_guarded.jsonl"
        $guardReport = "results/sprint4_2b/$($seed.name)_diagnostic_v2_guard_report.json"
        if (Test-CompletedRerun -MetricsPath $metrics -ExpectedAdapterId $seedConfig.id) {
            Write-Host "SKIP: $($seed.name) prompt v2 jest kompletne."
        } else {
            Invoke-Python -Arguments @(
                "-m", "peft_workshop.adapter_inference",
                "--config", $seed.config,
                "--data", $diagnosticData,
                "--output", $predictions,
                "--prompt-contract", "v2"
            )
            Invoke-Python -Arguments @(
                "-m", "peft_workshop.cli", "evaluate", $predictions,
                "--data", $diagnosticData,
                "--output", $metrics
            )
        }
        Invoke-Python -Arguments @(
            "-m", "peft_workshop.q2_guard",
            "--data", $diagnosticData,
            "--predictions", $predictions,
            "--output", $guarded,
            "--report", $guardReport,
            "--severity-mode", "enforce_status_policy_v1"
        )
    }
    Invoke-Compare
}

switch ($Phase) {
    "prepare" {
        Invoke-Python -Arguments @("-m", "peft_workshop.cli", "validate-data", "--data", $diagnosticData)
        Invoke-Compare
    }
    "rerun" { Invoke-Rerun }
    "compare" { Invoke-Compare }
}

Write-Host "Sprint 4.2B phase '$Phase' zakończona. Protected splits nie zostały otwarte."
