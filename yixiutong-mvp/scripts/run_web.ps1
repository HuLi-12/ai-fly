$ErrorActionPreference = "Stop"

& (Join-Path $PSScriptRoot "demo_bootstrap.ps1") | Out-Host

$workspaceRoot = Split-Path -Parent $PSScriptRoot | Split-Path -Parent
$projectRoot = Join-Path $workspaceRoot "yixiutong-mvp"
$webRoot = Join-Path $projectRoot "apps\web"
$runtimeRoot = Join-Path $workspaceRoot "runtime"
$logDir = Join-Path $runtimeRoot "logs\launcher"
$logPath = Join-Path $logDir "frontend.log"
$npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

if (-not (Test-Path -LiteralPath (Join-Path $webRoot "package.json"))) {
  throw "Missing frontend workspace: $webRoot"
}

if ($null -eq $npmCmd) {
  throw "npm.cmd was not found in PATH."
}

Set-Location $webRoot
Write-Output "Frontend log: $logPath"
$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $npmCmd.Source run dev -- --host 127.0.0.1 --port 5173 *>&1 | Tee-Object -FilePath $logPath -Append
$exitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorActionPreference

if ($exitCode -ne 0) {
  throw "Frontend exited with code $exitCode. Check $logPath"
}
