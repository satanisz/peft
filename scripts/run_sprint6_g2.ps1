$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) { throw "Brak środowiska .venv." }
Push-Location $ProjectRoot
try {
    & $Python -m peft_workshop.sprint6_g2_gate
    if ($LASTEXITCODE -ne 0) { throw "S6-G2 nie przeszedł." }
}
finally { Pop-Location }
