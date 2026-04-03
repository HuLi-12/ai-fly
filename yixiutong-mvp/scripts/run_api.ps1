$ErrorActionPreference = "Stop"

& (Join-Path $PSScriptRoot "demo_bootstrap.ps1") | Out-Host

$workspaceRoot = Split-Path -Parent $PSScriptRoot | Split-Path -Parent
$projectRoot = Join-Path $workspaceRoot "yixiutong-mvp"
$runtimeRoot = Join-Path $workspaceRoot "runtime"
$logDir = Join-Path $runtimeRoot "logs\launcher"
$logPath = Join-Path $logDir "backend.log"
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

if (-not (Test-Path -LiteralPath $pythonExe)) {
  throw "Missing virtual environment Python: $pythonExe"
}

Set-Location $projectRoot
Write-Output "Backend log: $logPath"
$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $pythonExe -m uvicorn app.main:app --app-dir apps/api --host 127.0.0.1 --port 8000 --reload *>&1 | Tee-Object -FilePath $logPath -Append
$exitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorActionPreference

if ($exitCode -ne 0) {
  throw "Backend exited with code $exitCode. Check $logPath"
}
