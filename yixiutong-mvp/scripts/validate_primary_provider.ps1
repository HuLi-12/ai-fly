param(
  [Parameter(Mandatory = $true)]
  [string]$ApiKey,
  [string]$BaseUrl = "https://api.openai.com/v1"
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptRoot
$workspaceRoot = Split-Path -Parent $projectRoot
$reportPath = Join-Path $workspaceRoot "runtime\\logs\\primary_provider_validation.json"
$pythonExe = Join-Path $projectRoot ".venv\\Scripts\\python.exe"

if (-not (Test-Path -LiteralPath $pythonExe)) {
  throw "Missing virtual environment Python at $pythonExe"
}

$env:PYTHONPATH = Join-Path $projectRoot "apps\\api"

& $pythonExe (Join-Path $projectRoot "scripts\\validate_primary_provider.py") --base-url $BaseUrl --api-key $ApiKey --output $reportPath
