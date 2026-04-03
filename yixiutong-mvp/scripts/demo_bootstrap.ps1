$ErrorActionPreference = "Stop"

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot | Split-Path -Parent
$ProjectRoot = Join-Path $WorkspaceRoot "yixiutong-mvp"
$RuntimeRoot = Join-Path $WorkspaceRoot "runtime"
$ModelsRoot = Join-Path $WorkspaceRoot "models"

$env:PIP_CACHE_DIR = Join-Path $RuntimeRoot "cache\\pip"
$env:npm_config_cache = Join-Path $RuntimeRoot "cache\\npm"
$env:HF_HOME = Join-Path $RuntimeRoot "cache\\hf"
$env:TRANSFORMERS_CACHE = Join-Path $RuntimeRoot "cache\\transformers"
$env:TEMP = Join-Path $RuntimeRoot "temp"
$env:TMP = Join-Path $RuntimeRoot "temp"
$env:PYTHONPATH = Join-Path $ProjectRoot "apps\\api"
$env:OLLAMA_MODELS = Join-Path $ModelsRoot "ollama"
$env:PYTHONUTF8 = "1"
$preferredOllamaExe = "D:\\develop_tool\\ollama\\Ollama\\ollama.exe"

if (Test-Path -LiteralPath $preferredOllamaExe) {
  $env:YIXIUTONG_OLLAMA_EXE = $preferredOllamaExe
  $ollamaBin = Split-Path -Parent $preferredOllamaExe
  if (-not (($env:PATH -split ";") -contains $ollamaBin)) {
    $env:PATH = "$ollamaBin;$env:PATH"
  }
}

Write-Output "Workspace root: $WorkspaceRoot"
Write-Output "Project root: $ProjectRoot"
Write-Output "PIP cache: $env:PIP_CACHE_DIR"
Write-Output "npm cache: $env:npm_config_cache"
Write-Output "HF cache: $env:HF_HOME"
Write-Output "TRANSFORMERS cache: $env:TRANSFORMERS_CACHE"
Write-Output "OLLAMA models: $env:OLLAMA_MODELS"
Write-Output "Ollama exe: $env:YIXIUTONG_OLLAMA_EXE"
Write-Output "PYTHONPATH: $env:PYTHONPATH"
