# 启动 NAS 上的 SERS MakerHub 服务
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
. (Join-Path $ScriptDir "common.ps1")
Invoke-NasCli -Command "start"
