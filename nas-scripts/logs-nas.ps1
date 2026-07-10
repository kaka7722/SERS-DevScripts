# 查看 NAS 上 SERS MakerHub 的 Docker 实时日志（按 Ctrl+C 退出）
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
. (Join-Path $ScriptDir "common.ps1")
Invoke-NasCli -Command "logs"
