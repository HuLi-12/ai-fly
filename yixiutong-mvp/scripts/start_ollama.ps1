param(
  [string]$OllamaExe = "",
  [string]$BaseUrl = "http://127.0.0.1:11434",
  [int]$WaitSeconds = 45
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptRoot
$workspaceRoot = Split-Path -Parent $projectRoot
$ollamaModels = Join-Path $workspaceRoot "models\\ollama"

New-Item -ItemType Directory -Force -Path $ollamaModels | Out-Null

if ([string]::IsNullOrWhiteSpace($OllamaExe)) {
  if (-not [string]::IsNullOrWhiteSpace($env:YIXIUTONG_OLLAMA_EXE)) {
    $OllamaExe = $env:YIXIUTONG_OLLAMA_EXE
  } elseif (Test-Path -LiteralPath "D:\\develop_tool\\ollama\\Ollama\\ollama.exe") {
    $OllamaExe = "D:\\develop_tool\\ollama\\Ollama\\ollama.exe"
  } else {
    $command = Get-Command ollama -ErrorAction SilentlyContinue
    if ($null -ne $command) {
      $OllamaExe = $command.Source
    }
  }
}

if ([string]::IsNullOrWhiteSpace($OllamaExe) -or -not (Test-Path -LiteralPath $OllamaExe)) {
  throw "Ollama executable was not found. Set YIXIUTONG_OLLAMA_EXE or install Ollama."
}

$env:YIXIUTONG_OLLAMA_EXE = $OllamaExe
$env:OLLAMA_MODELS = $ollamaModels
$env:OLLAMA_HOST = ($BaseUrl -replace '^https?://', '').TrimEnd('/')

function Test-OllamaReady {
  try {
    Invoke-RestMethod -Uri "$BaseUrl/api/tags" -Method Get -TimeoutSec 3 | Out-Null
    return $true
  } catch {
    return $false
  }
}

if (Test-OllamaReady) {
  Write-Output "Ollama service already reachable at $BaseUrl"
  Write-Output "YIXIUTONG_OLLAMA_EXE=$OllamaExe"
  Write-Output "OLLAMA_MODELS=$ollamaModels"
  exit 0
}

Start-Process -FilePath $OllamaExe -ArgumentList "serve" -WorkingDirectory (Split-Path -Parent $OllamaExe) -WindowStyle Hidden | Out-Null

$deadline = (Get-Date).AddSeconds($WaitSeconds)
while ((Get-Date) -lt $deadline) {
  Start-Sleep -Seconds 1
  if (Test-OllamaReady) {
    Write-Output "Ollama service started at $BaseUrl"
    Write-Output "YIXIUTONG_OLLAMA_EXE=$OllamaExe"
    Write-Output "OLLAMA_MODELS=$ollamaModels"
    exit 0
  }
}

throw "Ollama service did not become reachable within $WaitSeconds seconds."
