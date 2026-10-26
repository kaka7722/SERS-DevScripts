# SERS MakerHub NAS 管理菜单（一键入口）
# 本机 ~/.ssh/sers_nas 密钥已授权 ⇒ 全程免密；密钥缺失时按提示输入密码。

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
. (Join-Path $ScriptDir "common.ps1")

# NAS 地址与 nas-cli.py 同源：优先读 nas-host.conf（detect 命令写入），回退默认值
$NasHost = "192.168.5.13"
$ConfPath = Join-Path $ScriptDir "nas-host.conf"
if (Test-Path $ConfPath) {
    $ConfIp = (Get-Content $ConfPath -Raw).Trim()
    if ($ConfIp) { $NasHost = $ConfIp }
}

function Show-Menu {
    Clear-Host
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   SERS MakerHub NAS 管理（$NasHost）" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  1. 部署（重新构建前端 + 上传 + 重建容器）"
    Write-Host "  2. 快速部署（跳过构建，用现有 dist）"
    Write-Host "  3. 启动服务"
    Write-Host "  4. 停止服务"
    Write-Host "  5. 重启服务"
    Write-Host "  6. 查看容器状态"
    Write-Host "  7. 实时日志（Ctrl+C 退出）"
    Write-Host "  8. SSH 隧道 + 浏览器（Web Serial 用 localhost 访问）"
    Write-Host "  9. 重新探测 NAS IP（NAS 重启后地址变了用）"
    Write-Host "  0. 退出"
    Write-Host "========================================" -ForegroundColor Cyan
}

while ($true) {
    Show-Menu
    $choice = Read-Host "请选择"
    switch ($choice) {
        "1" { Invoke-NasCli -Command "deploy"; Pause }
        "2" { Invoke-NasCli -Command "deploy" -ExtraArgs @("--skip-build"); Pause }
        "3" { Invoke-NasCli -Command "start"; Pause }
        "4" { Invoke-NasCli -Command "stop"; Pause }
        "5" { Invoke-NasCli -Command "restart"; Pause }
        "6" { Invoke-NasCli -Command "status"; Pause }
        "7" { Invoke-NasCli -Command "logs" }
        "8" { & (Join-Path $ScriptDir "open-local-tunnel.ps1"); Pause }
        "9" { Invoke-NasCli -Command "detect"; Pause }
        "0" { exit 0 }
        default { Write-Host "无效选项，请重新输入。" -ForegroundColor Yellow; Start-Sleep -Seconds 1 }
    }
}
