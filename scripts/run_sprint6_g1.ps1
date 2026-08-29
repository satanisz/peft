param(
    [ValidateSet("author", "gate", "all")]
    [string]$Phase = "all"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Brak środowiska .venv."
}

Push-Location $ProjectRoot
try {
    if ($Phase -in @("author", "all")) {
        & $Python -m peft_workshop.shadow_challenge
        if ($LASTEXITCODE -ne 0) { throw "Authoring/audit shadow challenge nie przeszedł." }
    }
    if ($Phase -in @("gate", "all")) {
        & $Python -m peft_workshop.sprint6_g1_gate
        if ($LASTEXITCODE -ne 0) { throw "Bramka G1 wykryła błąd authoringu lub integralności." }
    }
}
finally {
    Pop-Location
}
