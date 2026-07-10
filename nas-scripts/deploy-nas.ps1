# 构建前端，并将最新前后端部署到 NAS（docker compose up -d --build）
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
. (Join-Path $ScriptDir "common.ps1")
Invoke-NasCli -Command "deploy"
