# 同时启动 SERS MakerHub 前后端
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

& "$ScriptDir\start-backend.ps1"
& "$ScriptDir\start-frontend.ps1"

Write-Host "启动命令已下发，请查看弹出的 PowerShell 窗口。" -ForegroundColor Cyan
