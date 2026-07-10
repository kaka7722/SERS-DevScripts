# 查看 NAS 上 SERS MakerHub 的容器运行状态
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
. (Join-Path $ScriptDir "common.ps1")
Invoke-NasCli -Command "status"
