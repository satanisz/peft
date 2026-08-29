[CmdletBinding()]
param(
    [switch]$AllowDirty,
    [switch]$SkipTests,
    [switch]$SkipAdapterHashes
)

$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptRoot
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Brak .venv. Najpierw przygotuj środowisko zgodnie z docs/00_how_to_run.md."
}

$arguments = @("-m", "peft_workshop.sprint6_preflight")
if ($AllowDirty) { $arguments += "--allow-dirty" }
if ($SkipTests) { $arguments += "--skip-tests" }
if ($SkipAdapterHashes) { $arguments += "--skip-adapter-hashes" }

& $pythonPath @arguments
if ($LASTEXITCODE -ne 0) {
    throw "S6-G0 nie przeszło. Protected evidence pozostaje zamknięte."
}

Write-Host "S6-G0 PASS. Następny dozwolony krok: authoring i review shadow-challenge-v1."
