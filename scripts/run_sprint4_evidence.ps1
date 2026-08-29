[CmdletBinding()]
param(
    [switch]$ConfirmOpenProtectedSplits
)

$ErrorActionPreference = "Stop"
if (-not $ConfirmOpenProtectedSplits) {
    throw "Protected splits pozostają zamknięte. Użyj -ConfirmOpenProtectedSplits dopiero po review bramki pre-test."
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptRoot
Set-Location -LiteralPath $projectRoot
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
$matrix = Get-Content -Raw -LiteralPath (Join-Path $projectRoot "configs\sprint4_matrix_v1.json") | ConvertFrom-Json
$analyticalGatePath = Join-Path $projectRoot "configs\sprint6_evidence_gate_v1.json"
if (-not (Test-Path -LiteralPath $analyticalGatePath)) {
    throw "Brak bramki Sprintu 6 protected evidence. Wymagany review Sol/high."
}
$analyticalGate = Get-Content -Raw -LiteralPath $analyticalGatePath | ConvertFrom-Json
if (
    $analyticalGate.decision -ne "APPROVED_TO_OPEN_PROTECTED_SPLITS" -or
    $analyticalGate.protected_splits_opened -or
    $analyticalGate.m5_status -ne "M5_ACCEPTED_CONTENT_FREEZE_WITH_PROTECTED_HOLD"
) {
    throw "Bramka Sprintu 6 nie zezwala na otwarcie protected splits: $($analyticalGate.decision)"
}
$s6Gates = @(
    @{ Path = "results\sprint6\g0_preflight.json"; Decision = "S6_G0_PASS" },
    @{ Path = "results\sprint6\g1_shadow_freeze.json"; Decision = "S6_G1_PASS" },
    @{ Path = "results\sprint6\g2_technical_readiness.json"; Decision = "S6_G2_PASS" }
)
foreach ($requiredGate in $s6Gates) {
    $requiredGatePath = Join-Path $projectRoot $requiredGate.Path
    if (-not (Test-Path -LiteralPath $requiredGatePath)) {
        throw "Brak wymaganej bramki Sprintu 6: $($requiredGate.Path)"
    }
    $requiredGateResult = Get-Content -Raw -LiteralPath $requiredGatePath | ConvertFrom-Json
    if ($requiredGateResult.decision -ne $requiredGate.Decision) {
        throw "Bramka $($requiredGate.Path) nie ma oczekiwanej decyzji $($requiredGate.Decision)."
    }
}
$gatePath = Join-Path $projectRoot "results\sprint4\m4_pretest_summary.json"
if (-not (Test-Path -LiteralPath $gatePath)) {
    throw "Brak m4_pretest_summary.json. Najpierw ukończ trzy seedy i validation."
}
$gate = Get-Content -Raw -LiteralPath $gatePath | ConvertFrom-Json
if ($gate.decision -ne "READY_TO_OPEN_PROTECTED_SPLITS") {
    throw "Bramka pre-test nie zezwala na test: $($gate.decision)"
}
$failedGateChecks = @($gate.checks.PSObject.Properties | Where-Object { -not $_.Value })
if ($failedGateChecks.Count -gt 0) {
    throw "Raport pre-test zawiera niespełnione kryteria mimo decyzji READY."
}

$authorization = [ordered]@{
    authorized_at_utc = [DateTime]::UtcNow.ToString("o")
    pretest_summary_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $gatePath).Hash.ToLowerInvariant()
    matrix_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $projectRoot "configs\sprint4_matrix_v1.json")).Hash.ToLowerInvariant()
    analytical_gate_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $analyticalGatePath).Hash.ToLowerInvariant()
    s6_g0_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $projectRoot "results\sprint6\g0_preflight.json")).Hash.ToLowerInvariant()
    s6_g1_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $projectRoot "results\sprint6\g1_shadow_freeze.json")).Hash.ToLowerInvariant()
    s6_g2_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $projectRoot "results\sprint6\g2_technical_readiness.json")).Hash.ToLowerInvariant()
    git_commit = (& git rev-parse HEAD).Trim()
    explicit_operator_confirmation = $true
}
$authorization | ConvertTo-Json -Depth 4 | Set-Content -Encoding utf8 -LiteralPath (
    Join-Path $projectRoot "results\sprint4\protected_split_authorization.json"
)

function Invoke-Python {
    param([string[]]$Arguments)
    & $pythonPath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Polecenie Python zakończyło się kodem ${LASTEXITCODE}: $($Arguments -join ' ')"
    }
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
        $metrics.metadata.protected_split_authorized
}

$datasets = @(
    @{ Name = "original_test"; Path = $matrix.protected_evaluation.original_test; Count = 100 },
    @{ Name = "boundary_test"; Path = $matrix.protected_evaluation.boundary_test; Count = 120 },
    @{ Name = "challenge"; Path = $matrix.protected_evaluation.challenge; Count = 20 }
)

foreach ($seedSpec in $matrix.seeds) {
    foreach ($dataset in $datasets) {
        $output = "results/sprint4/$($seedSpec.name)_$($dataset.Name).jsonl"
        $metrics = "results/sprint4/$($seedSpec.name)_$($dataset.Name)_metrics.json"
        if (Test-CompletedEvaluation -SeedSpec $seedSpec -MetricsPath $metrics -ExpectedCount $dataset.Count) {
            Write-Host "SKIP: $($seedSpec.name) / $($dataset.Name) jest kompletne."
            continue
        }
        Invoke-Python -Arguments @(
            "-m", "peft_workshop.adapter_inference",
            "--config", $seedSpec.config,
            "--data", $dataset.Path,
            "--output", $output,
            "--allow-protected-split"
        )
        Invoke-Python -Arguments @(
            "-m", "peft_workshop.cli", "evaluate", $output,
            "--data", $dataset.Path,
            "--output", $metrics
        )
    }
}

Invoke-Python -Arguments @("-m", "peft_workshop.sprint4_evidence_report", "--matrix", "configs/sprint4_matrix_v1.json")
Write-Host "Protected evidence wygenerowane. Nie dostrajaj na testach; wróć do Sol/high po analizę M4."
