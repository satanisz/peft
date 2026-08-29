[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptRoot
Set-Location -LiteralPath $projectRoot
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
$matrix = Get-Content -Raw -LiteralPath (Join-Path $projectRoot "configs\sprint4_matrix_v1.json") | ConvertFrom-Json
$diagnosticData = "data/diagnostic/diagnostic_set_v1.jsonl"
$guardConfig = Get-Content -Raw -LiteralPath (Join-Path $projectRoot "configs\q2_decision_guard_v2.json") | ConvertFrom-Json
$decisionRules = $guardConfig.decision_rules

function Invoke-Python {
    param([string[]]$Arguments)
    & $pythonPath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Polecenie Python zakończyło się kodem ${LASTEXITCODE}: $($Arguments -join ' ')"
    }
}

foreach ($seed in $matrix.seeds) {
    $predictions = "results/sprint4_2b/$($seed.name)_diagnostic_v2.jsonl"
    if (-not (Test-Path -LiteralPath (Join-Path $projectRoot $predictions))) {
        throw "Brak predykcji prompt v2 dla $($seed.name). Najpierw zakończ Sprint 4.2B."
    }
    Invoke-Python -Arguments @(
        "-m", "peft_workshop.q2_guard",
        "--data", $diagnosticData,
        "--predictions", $predictions,
        "--output", "results/sprint4_2c/$($seed.name)_decision_guarded.jsonl",
        "--report", "results/sprint4_2c/$($seed.name)_decision_guard_report.json",
        "--severity-mode", "enforce_status_policy_v1",
        "--decision-rules", $decisionRules
    )
}

Invoke-Python -Arguments @("-m", "peft_workshop.sprint4_2c_report")
Write-Host "Sprint 4.2C zakończony. Nie wykonano inferencji ani nie otwarto protected splits."
