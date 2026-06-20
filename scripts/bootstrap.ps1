<#
[INPUT]: 依赖 {requirements、vendor package.json 与本机环境} 的 {一键安装需求}
[OUTPUT]: 对外提供 {profile 化 bootstrap 安装与 smoke 验证}
[POS]: {scripts} 的 {Windows 安装入口}，把 clone 后的手工安装收敛成一条命令
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
#>

param(
  [ValidateSet("core", "showcase", "generate-cli", "generate-official", "assemble", "publish", "all")]
  [string]$Profile = "core",
  [switch]$SkipSmoke
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$VenvDir = Join-Path $Root ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\\python.exe"
$PipExe = Join-Path $VenvDir "Scripts\\pip.exe"
$VendorDir = Join-Path $Root "adapters\\douyin-upload-vendor"

function Ensure-Command($Name) {
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Missing required command: $Name"
  }
}

function Ensure-Venv() {
  Ensure-Command python
  if (-not (Test-Path $PythonExe)) {
    python -m venv $VenvDir
  }
  & $PythonExe -m pip install --upgrade pip | Out-Null
  & $PipExe install -r (Join-Path $Root "requirements.txt") | Out-Null
}

function Run-Doctor($DoctorProfile) {
  & $PythonExe (Join-Path $Root "scripts\\doctor.py") --profile $DoctorProfile
}

function Install-Vendor() {
  Ensure-Command node
  Ensure-Command npm
  Push-Location $VendorDir
  try {
    npm install
  }
  finally {
    Pop-Location
  }
}

function Run-Smoke() {
  $outDir = Join-Path $env:TEMP ("autodouyin-bootstrap-smoke-" + [guid]::NewGuid().ToString())
  & $PythonExe (Join-Path $Root "scripts\\run_pipeline.py") --brief (Join-Path $Root "examples\\brief\\minimal-douyin-video.json") --output-dir $outDir
  & $PythonExe (Join-Path $Root "scripts\\validate_artifacts.py") --dir $outDir
}

Ensure-Venv

if ($Profile -in @("publish", "all")) {
  Install-Vendor
}

Run-Doctor $Profile

if (-not $SkipSmoke -and $Profile -in @("core", "showcase", "generate-cli", "generate-official", "assemble", "all")) {
  Run-Smoke
}

Write-Output "bootstrap complete: $Profile"
