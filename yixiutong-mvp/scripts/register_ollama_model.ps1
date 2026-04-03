$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptRoot
$workspaceRoot = Split-Path -Parent $projectRoot
$manifestPath = Join-Path $workspaceRoot "models\\local-llm\\download_manifest.json"
$ollamaRoot = Join-Path $workspaceRoot "models\\ollama"
$modelfilePath = Join-Path $ollamaRoot "Modelfile.yixiutong-qwen3b"
$startScript = Join-Path $scriptRoot "start_ollama.ps1"

if (-not (Test-Path -LiteralPath $manifestPath)) {
  throw "Missing local model manifest. Run scripts/download_local_model.ps1 first."
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$ggufPath = [string]$manifest.gguf_file

if ([string]::IsNullOrWhiteSpace($ggufPath) -or -not (Test-Path -LiteralPath $ggufPath)) {
  throw "The GGUF file recorded in the manifest does not exist."
}

New-Item -ItemType Directory -Force -Path $ollamaRoot | Out-Null

$modelfile = @(
  "FROM $ggufPath"
  'TEMPLATE """{{ if .Messages }}'
  '{{- if .System }}<|im_start|>system'
  ''
  '{{ .System }}<|im_end|>'
  ''
  '{{ end }}{{- range .Messages }}'
  '{{- if eq .Role "user" }}<|im_start|>user'
  ''
  '{{ .Content }}<|im_end|>'
  ''
  '{{- else if eq .Role "assistant" }}<|im_start|>assistant'
  ''
  '{{ .Content }}<|im_end|>'
  ''
  '{{- end }}'
  '{{- end }}<|im_start|>assistant'
  ''
  '{{- else }}'
  '{{- if .System }}<|im_start|>system'
  ''
  '{{ .System }}<|im_end|>'
  ''
  '{{ end }}{{ if .Prompt }}<|im_start|>user'
  ''
  '{{ .Prompt }}<|im_end|>'
  ''
  '{{ end }}<|im_start|>assistant'
  ''
  '{{- end }}"""'
  "PARAMETER temperature 0.1"
  "PARAMETER num_ctx 4096"
  'PARAMETER stop "<|im_start|>"'
  'PARAMETER stop "<|im_end|>"'
  "SYSTEM You are the local fallback model for the Yixiutong aviation agent. Stay concise and use supplied evidence."
) -join [Environment]::NewLine

Set-Content -LiteralPath $modelfilePath -Value $modelfile -Encoding utf8

$env:OLLAMA_MODELS = $ollamaRoot

if (-not (Test-Path -LiteralPath $startScript)) {
  throw "Missing helper script: start_ollama.ps1"
}

& $startScript | Write-Output

$ollamaExe = $env:YIXIUTONG_OLLAMA_EXE
if ([string]::IsNullOrWhiteSpace($ollamaExe)) {
  $command = Get-Command ollama -ErrorAction SilentlyContinue
  if ($null -eq $command) {
    throw "Ollama CLI is not available in PATH and YIXIUTONG_OLLAMA_EXE was not set."
  }
  $ollamaExe = $command.Source
}

& $ollamaExe create yixiutong-qwen3b -f $modelfilePath
Write-Output "Registered Ollama model: yixiutong-qwen3b"
Write-Output "OLLAMA_MODELS=$ollamaRoot"
