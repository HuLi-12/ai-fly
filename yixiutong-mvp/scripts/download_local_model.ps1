$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptRoot
$workspaceRoot = Split-Path -Parent $projectRoot
$runtimeRoot = Join-Path $workspaceRoot "runtime"
$cacheRoot = Join-Path $runtimeRoot "cache"
$tempRoot = Join-Path $runtimeRoot "temp"

New-Item -ItemType Directory -Force -Path $cacheRoot | Out-Null
New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $cacheRoot "hf") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $cacheRoot "transformers") | Out-Null

$env:HF_HOME = Join-Path $cacheRoot "hf"
$env:TRANSFORMERS_CACHE = Join-Path $cacheRoot "transformers"
$env:TEMP = $tempRoot
$env:TMP = $tempRoot
$env:PYTHONUTF8 = "1"
$env:PYTHONPATH = Join-Path $projectRoot "apps\\api"

& (Join-Path $projectRoot ".venv\\Scripts\\python.exe") "scripts/download_local_model.py"
