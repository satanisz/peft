[CmdletBinding()]
param(
    [ValidateSet("prepare", "diagnostic", "gate")]
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

function Invoke-Guard {
    param(
        [string]$Data,
        [string]$Predictions,
        [string]$Output,
        [string]$Report,
        [string]$SeverityMode
    )
    Invoke-Python -Arguments @(
        "-m", "peft_workshop.q2_guard",
        "--data", $Data,
        "--predictions", $Predictions,
        "--output", $Output,
        "--report", $Report,
        "--severity-mode", $SeverityMode
    )
}

function Invoke-Prepare {
    Invoke-Python -Arguments @("-m", "peft_workshop.cli", "validate-data", "--data", $diagnosticData)
    Invoke-Python -Arguments @("-m", "peft_workshop.sprint4_2a_analysis")
    foreach ($seed in $matrix.seeds) {
        Invoke-Guard `
            -Data $matrix.allowed_validation.original `
            -Predictions $seed.original_validation_output `
            -Output "results/sprint4_2a/$($seed.name)_original_validation_guarded.jsonl" `
            -Report "results/sprint4_2a/$($seed.name)_original_validation_guard_report.json" `
            -SeverityMode "legacy_report_only"
        Invoke-Guard `
            -Data $matrix.allowed_validation.boundary `
            -Predictions $seed.boundary_validation_output `
            -Output "results/sprint4_2a/$($seed.name)_boundary_validation_guarded.jsonl" `
            -Report "results/sprint4_2a/$($seed.name)_boundary_validation_guard_report.json" `
            -SeverityMode "enforce_status_policy_v1"
    }
    Invoke-Python -Arguments @("-m", "peft_workshop.sprint4_2a_gate")
}

function Assert-IndependentReviewApproved {
    $review = Get-Content -Raw -LiteralPath $reviewPath | ConvertFrom-Json
    if (-not $review.reviewer_independent_from_authoring -or
        $review.summary.reviewed_case_count -lt 30 -or
        $review.summary.approved_case_count -ne 30 -or
        $review.summary.critical_error_count -ne 0 -or
        -not $review.summary.approved_for_q2_validation) {
        throw "Diagnostic inference pozostaje zablokowane do niezależnego review 30/30 przypadków."
    }
}

function Test-CompletedDiagnostic {
    param($Seed, [string]$MetricsPath)
    $resolvedMetrics = Join-Path $projectRoot $MetricsPath
    if (-not (Test-Path -LiteralPath $resolvedMetrics)) {
        return $false
    }
    $metrics = Get-Content -Raw -LiteralPath $resolvedMetrics | ConvertFrom-Json
    $seedConfig = Get-Content -Raw -LiteralPath (Join-Path $projectRoot $Seed.config) | ConvertFrom-Json
    return $metrics.aggregate.count -eq 30 -and
        $metrics.metadata.adapter_id -eq $seedConfig.id -and
        -not $metrics.metadata.protected_split_authorized
}

function Invoke-Diagnostic {
    Assert-IndependentReviewApproved
    foreach ($seed in $matrix.seeds) {
        $predictions = "results/sprint4_2a/$($seed.name)_diagnostic.jsonl"
        $metrics = "results/sprint4_2a/$($seed.name)_diagnostic_metrics.json"
        if (Test-CompletedDiagnostic -Seed $seed -MetricsPath $metrics) {
            Write-Host "SKIP: $($seed.name) diagnostic jest kompletne."
        } else {
            Invoke-Python -Arguments @(
                "-m", "peft_workshop.adapter_inference",
                "--config", $seed.config,
                "--data", $diagnosticData,
                "--output", $predictions
            )
            Invoke-Python -Arguments @(
                "-m", "peft_workshop.cli", "evaluate", $predictions,
                "--data", $diagnosticData,
                "--output", $metrics
            )
        }
        Invoke-Guard `
            -Data $diagnosticData `
            -Predictions $predictions `
            -Output "results/sprint4_2a/$($seed.name)_diagnostic_guarded.jsonl" `
            -Report "results/sprint4_2a/$($seed.name)_diagnostic_guard_report.json" `
            -SeverityMode "enforce_status_policy_v1"
    }
    Invoke-Python -Arguments @("-m", "peft_workshop.sprint4_2a_gate")
}

switch ($Phase) {
    "prepare" { Invoke-Prepare }
    "diagnostic" { Invoke-Diagnostic }
    "gate" { Invoke-Python -Arguments @("-m", "peft_workshop.sprint4_2a_gate") }
}

Write-Host "Sprint 4.2A phase '$Phase' zakończona. Protected splits nie zostały otwarte."
