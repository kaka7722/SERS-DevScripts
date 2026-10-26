# 通过 SSH 本地端口转发，把 NAS 的前后端映射到 localhost
# 这样可以用 http://localhost:8080 访问 NAS，满足 Web Serial API 的安全上下文要求

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
# NAS 地址与 nas-cli.py 同源：优先读 nas-host.conf（detect 命令写入），回退默认值
$NasHost = "192.168.5.13"
$ConfPath = Join-Path $ScriptDir "nas-host.conf"
if (Test-Path $ConfPath) {
    $ConfIp = (Get-Content $ConfPath -Raw).Trim()
    if ($ConfIp) { $NasHost = $ConfIp }
}
$NasPort = 2222
$NasUser = "coolwing"

# 2026-10：本机 ~/.ssh/sers_nas 密钥已授权到 NAS，优先免密建立隧道；
# 只有密钥缺失时才回退到密码提示（与 common.ps1 的认证逻辑一致）。
$KeyPath = Join-Path $env:USERPROFILE ".ssh\sers_nas"
if (Test-Path $KeyPath) {
    Write-Host "使用本机密钥免密建立隧道..." -ForegroundColor Cyan
    $tunnelCmd = "ssh -i `"$KeyPath`" -p $NasPort -L 8080:${NasHost}:8080 -L 5000:${NasHost}:5000 ${NasUser}@${NasHost}"
} else {
    Write-Host "即将打开 SSH 隧道窗口，请在弹出的窗口中输入 NAS 密码。" -ForegroundColor Cyan
    $tunnelCmd = "ssh -p $NasPort -L 8080:${NasHost}:8080 -L 5000:${NasHost}:5000 ${NasUser}@${NasHost}"
}
Write-Host "隧道建立后，会自动打开 Edge 浏览器访问 http://localhost:8080" -ForegroundColor Cyan
Write-Host ""

# 在新窗口中建立 SSH 隧道（转发本地 8080/5000 到 NAS 的 8080/5000）
Start-Process powershell -ArgumentList "-NoExit", "-Command", $tunnelCmd

# 等待用户输入密码并建立隧道
Write-Host "等待 5 秒让隧道建立..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 用 Edge 打开 localhost:8080
Start-Process "msedge" -ArgumentList "http://localhost:8080"

Write-Host ""
Write-Host "Edge 已打开。如果页面还没加载，请再刷新一次。" -ForegroundColor Green
Write-Host "用完之后，关闭 SSH 隧道窗口即可断开。" -ForegroundColor Gray
