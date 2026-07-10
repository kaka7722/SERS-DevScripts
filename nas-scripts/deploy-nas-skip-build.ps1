# 不重新构建前端，直接用现有 dist 部署到 NAS
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
. (Join-Path $ScriptDir "common.ps1")
Invoke-NasCli -Command "deploy" -ExtraArgs @("--skip-build")
