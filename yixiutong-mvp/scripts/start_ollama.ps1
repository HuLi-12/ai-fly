param(
  [string]$OllamaExe = "",
  [string]$BaseUrl = "http://127.0.0.1:11434",
  [int]$WaitSeconds = 45,
  [string]$HttpsProxy = "",
  [string]$NoProxy = "127.0.0.1,localhost",
  [switch]$ForceRestart
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

function Get-ScopedEnvironmentValue {
  param([Parameter(Mandatory = $true)][string]$Name)

  $processValue = [Environment]::GetEnvironmentVariable($Name, "Process")
  if (-not [string]::IsNullOrWhiteSpace($processValue)) {
    return $processValue
  }

  foreach ($scope in @("User", "Machine")) {
    $value = [Environment]::GetEnvironmentVariable($Name, $scope)
    if (-not [string]::IsNullOrWhiteSpace($value)) {
      return $value
    }
  }

  return ""
}

function Resolve-ProxyFromRegistry {
  try {
    $settings = Get-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" -ErrorAction Stop
  } catch {
    return ""
  }

  if ($settings.ProxyEnable -ne 1 -or [string]::IsNullOrWhiteSpace($settings.ProxyServer)) {
    return ""
  }

  $proxyServer = [string]$settings.ProxyServer
  $segments = $proxyServer -split ';' | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

  foreach ($candidate in $segments) {
    $trimmed = $candidate.Trim()
    if ($trimmed -match '^https=(.+)$') {
      $value = $Matches[1].Trim()
      if ($value -notmatch '^[a-z]+://') {
        $value = "http://$value"
      }
      return $value
    }
  }

  foreach ($candidate in $segments) {
    $trimmed = $candidate.Trim()
    if ($trimmed -match '^http=(.+)$') {
      $value = $Matches[1].Trim()
      if ($value -notmatch '^[a-z]+://') {
        $value = "http://$value"
      }
      return $value
    }
  }

  $first = $segments | Select-Object -First 1
  if ([string]::IsNullOrWhiteSpace($first)) {
    return ""
  }

  if ($first -match '^[a-z]+://') {
    return $first.Trim()
  }

  if ($first -match '^[^=]+=(.+)$') {
    return "http://$($Matches[1].Trim())"
  }

  return "http://$($first.Trim())"
}

function Stop-OllamaProcesses {
  $processes = Get-Process | Where-Object { $_.ProcessName -like 'ollama*' }
  if ($null -eq $processes -or $processes.Count -eq 0) {
    return
  }

  $processes | Stop-Process -Force
  Start-Sleep -Seconds 2
}

function Test-OllamaReady {
  try {
    Invoke-RestMethod -Uri "$BaseUrl/api/tags" -Method Get -TimeoutSec 3 | Out-Null
    return $true
  } catch {
    return $false
  }
}

if ([string]::IsNullOrWhiteSpace($HttpsProxy)) {
  $HttpsProxy = Get-ScopedEnvironmentValue -Name "HTTPS_PROXY"
}

if ([string]::IsNullOrWhiteSpace($HttpsProxy)) {
  $HttpsProxy = Resolve-ProxyFromRegistry
}

if (-not [string]::IsNullOrWhiteSpace($HttpsProxy)) {
  $env:HTTPS_PROXY = $HttpsProxy
  [Environment]::SetEnvironmentVariable("HTTPS_PROXY", $HttpsProxy, "User")
}

if (-not [string]::IsNullOrWhiteSpace($NoProxy)) {
  $env:NO_PROXY = $NoProxy
  [Environment]::SetEnvironmentVariable("NO_PROXY", $NoProxy, "User")
}

if ($ForceRestart) {
  Stop-OllamaProcesses
}

if ((-not $ForceRestart) -and (Test-OllamaReady)) {
  Write-Output "Ollama service already reachable at $BaseUrl"
  Write-Output "YIXIUTONG_OLLAMA_EXE=$OllamaExe"
  Write-Output "OLLAMA_MODELS=$ollamaModels"
  if (-not [string]::IsNullOrWhiteSpace($HttpsProxy)) {
    Write-Output "HTTPS_PROXY=$HttpsProxy"
  }
  if (-not [string]::IsNullOrWhiteSpace($NoProxy)) {
    Write-Output "NO_PROXY=$NoProxy"
  }
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
    if (-not [string]::IsNullOrWhiteSpace($HttpsProxy)) {
      Write-Output "HTTPS_PROXY=$HttpsProxy"
    }
    if (-not [string]::IsNullOrWhiteSpace($NoProxy)) {
      Write-Output "NO_PROXY=$NoProxy"
    }
    exit 0
  }
}

throw "Ollama service did not become reachable within $WaitSeconds seconds."
