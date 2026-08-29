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
$approvalPath = Join-Path $projectRoot "results\sprint6\protected_open_approval.json"
if (-not (Test-Path -LiteralPath $analyticalGatePath)) {
    throw "Brak zamrożonego kontraktu Sprintu 6."
}
$analyticalGate = Get-Content -Raw -LiteralPath $analyticalGatePath | ConvertFrom-Json
if ($analyticalGate.decision -ne "HOLD_PENDING_S6_PREFLIGHT_AND_OPERATOR_APPROVAL" -or $analyticalGate.protected_splits_opened) {
    throw "Zamrożony kontrakt Sprintu 6 został zmieniony; approval musi być osobnym artefaktem."
}
& $pythonPath -m peft_workshop.sprint6_open_approval --approval $approvalPath --require-approved --no-output
if ($LASTEXITCODE -ne 0) {
    throw "Brak poprawnego, osobnego approval Sol/high dla protected evidence."
}
$s6Gates = @(
    @{ Path = "results\sprint6\g0_preflight.json"; Decision = "S6_G0_PASS" },
    @{ Path = "results\sprint6\g1_shadow_freeze.json"; Decision = "S6_G1_PASS" },
    @{ Path = "results\sprint6\g2_technical_readiness.json"; Decision = "S6_G2_1_PASS" }
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
    frozen_evidence_contract_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $analyticalGatePath).Hash.ToLowerInvariant()
    protected_open_approval_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $approvalPath).Hash.ToLowerInvariant()
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
        $metrics.metadata.protected_split_authorized -and
        $metrics.metadata.prompt_contract -eq "v2" -and
        $metrics.metadata.max_new_tokens -eq 384
}

$datasets = @(
    @{ Name = "original_test"; Path = $matrix.protected_evaluation.original_test; Count = 100; ResultRoot = "results/sprint4" },
    @{ Name = "boundary_test"; Path = $matrix.protected_evaluation.boundary_test; Count = 120; ResultRoot = "results/sprint4" },
    @{ Name = "challenge"; Path = $matrix.protected_evaluation.challenge; Count = 20; ResultRoot = "results/sprint4" },
    @{ Name = "shadow_challenge"; Path = "data/shadow/shadow_challenge_v1.jsonl"; Count = 50; ResultRoot = "results/sprint6" }
)

foreach ($dataset in $datasets) {
    foreach ($seedSpec in $matrix.seeds) {
        $output = "$($dataset.ResultRoot)/$($seedSpec.name)_$($dataset.Name).jsonl"
        $metrics = "$($dataset.ResultRoot)/$($seedSpec.name)_$($dataset.Name)_metrics.json"
        if (Test-CompletedEvaluation -SeedSpec $seedSpec -MetricsPath $metrics -ExpectedCount $dataset.Count) {
            Write-Host "SKIP: $($seedSpec.name) / $($dataset.Name) jest kompletne."
            continue
        }
        Invoke-Python -Arguments @(
            "-m", "peft_workshop.adapter_inference",
            "--config", $seedSpec.config,
            "--data", $dataset.Path,
            "--output", $output,
            "--prompt-contract", "v2",
            "--max-new-tokens", "384",
            "--allow-protected-split"
        )
        Invoke-Python -Arguments @(
            "-m", "peft_workshop.cli", "evaluate", $output,
            "--data", $dataset.Path,
            "--output", $metrics
        )
    }
}

foreach ($seedSpec in $matrix.seeds) {
    Invoke-Python -Arguments @(
        "-m", "peft_workshop.q2_guard",
        "--data", "data/shadow/shadow_challenge_v1.jsonl",
        "--predictions", "results/sprint6/$($seedSpec.name)_shadow_challenge.jsonl",
        "--output", "results/sprint6/$($seedSpec.name)_shadow_challenge_guarded.jsonl",
        "--report", "results/sprint6/$($seedSpec.name)_shadow_challenge_guard_report.json",
        "--severity-mode", "enforce_status_policy_v1",
        "--decision-rules", "configs/shadow_deterministic_rules_v1.json"
    )
}

Invoke-Python -Arguments @("-m", "peft_workshop.sprint6_evidence_report")
Write-Host "Primary i shadow evidence wygenerowane bez retuningu. Wróć do Sol/high po analizę i manual review."
