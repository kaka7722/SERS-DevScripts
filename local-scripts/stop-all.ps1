# 同时关闭 SERS MakerHub 前后端
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

& "$ScriptDir\stop-backend.ps1"
& "$ScriptDir\stop-frontend.ps1"

Write-Host "前后端关闭命令已执行。" -ForegroundColor Cyan
