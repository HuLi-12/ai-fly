param(
  [switch]$NoBrowser,
  [int]$ApiPort = 8000,
  [int]$WebPort = 5173
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = Split-Path -Parent $projectRoot
$runtimeRoot = Join-Path $workspaceRoot "runtime"
$logDir = Join-Path $runtimeRoot "logs\launcher"
$apiScript = Join-Path $PSScriptRoot "run_api.ps1"
$webScript = Join-Path $PSScriptRoot "run_web.ps1"
$ollamaScript = Join-Path $PSScriptRoot "start_ollama.ps1"
$apiUrl = "http://127.0.0.1:$ApiPort/api/v1/system/self-check"
$webUrl = "http://127.0.0.1:$WebPort"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Test-HttpReady {
  param(
    [Parameter(Mandatory = $true)][string]$Url,
    [int]$TimeoutSeconds = 3
  )

  try {
    Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSeconds | Out-Null
    return $true
  } catch {
    return $false
  }
}

function Wait-HttpReady {
  param(
    [Parameter(Mandatory = $true)][string]$Url,
    [Parameter(Mandatory = $true)][string]$Name,
    [int]$WaitSeconds = 60
  )

  $deadline = (Get-Date).AddSeconds($WaitSeconds)
  while ((Get-Date) -lt $deadline) {
    if (Test-HttpReady -Url $Url -TimeoutSeconds 3) {
      Write-Output "$Name is ready: $Url"
      return
    }
    Start-Sleep -Seconds 2
  }
  throw "$Name did not become ready within $WaitSeconds seconds. Check logs under $logDir"
}

function Start-ServiceWindow {
  param(
    [Parameter(Mandatory = $true)][string]$Name,
    [Parameter(Mandatory = $true)][string]$ScriptPath,
    [Parameter(Mandatory = $true)][string]$WorkingDirectory
  )

  Start-Process -FilePath "powershell.exe" `
    -ArgumentList @(
      "-NoProfile",
      "-NoExit",
      "-ExecutionPolicy", "Bypass",
      "-Command", "& { `$Host.UI.RawUI.WindowTitle = '$Name'; & '$ScriptPath' }"
    ) `
    -WorkingDirectory $WorkingDirectory | Out-Null
}

Write-Output "Preparing Yixiutong launcher..."
& (Join-Path $PSScriptRoot "demo_bootstrap.ps1") | Out-Host
& $ollamaScript | Out-Host

if (-not (Test-HttpReady -Url $apiUrl)) {
  Write-Output "Starting backend window..."
  Start-ServiceWindow -Name "Yixiutong API" -ScriptPath $apiScript -WorkingDirectory $projectRoot
  Wait-HttpReady -Url $apiUrl -Name "Backend API" -WaitSeconds 90
} else {
  Write-Output "Backend API already running: $apiUrl"
}

if (-not (Test-HttpReady -Url $webUrl)) {
  Write-Output "Starting frontend window..."
  Start-ServiceWindow -Name "Yixiutong Web" -ScriptPath $webScript -WorkingDirectory (Join-Path $projectRoot "apps\web")
  Wait-HttpReady -Url $webUrl -Name "Frontend" -WaitSeconds 90
} else {
  Write-Output "Frontend already running: $webUrl"
}

Write-Output ""
Write-Output "Yixiutong is ready."
Write-Output "Frontend: $webUrl"
Write-Output "Backend self-check: $apiUrl"
Write-Output "Launcher logs: $logDir"

if (-not $NoBrowser) {
  Start-Process $webUrl | Out-Null
}
