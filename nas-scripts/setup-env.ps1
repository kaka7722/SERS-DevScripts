# 初始化 NAS 管理脚本所需的 Python 虚拟环境
# 只需要在第一次使用时运行一次

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VenvDir = Join-Path $ScriptDir ".venv"

Write-Host "正在准备 NAS 管理脚本运行环境..." -ForegroundColor Cyan

if (Test-Path "$VenvDir\Scripts\python.exe") {
    Write-Host "虚拟环境已存在：$VenvDir" -ForegroundColor Green
    exit 0
}

Write-Host "创建 Python 虚拟环境..." -ForegroundColor Yellow
python -m venv $VenvDir

Write-Host "安装依赖 paramiko、scp..." -ForegroundColor Yellow
& (Join-Path $VenvDir "Scripts\pip.exe") install --upgrade pip | Out-Null
& (Join-Path $VenvDir "Scripts\pip.exe") install paramiko scp

Write-Host "环境准备完成。" -ForegroundColor Green
