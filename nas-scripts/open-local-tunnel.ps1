# 通过 SSH 本地端口转发，把 NAS 的前后端映射到 localhost
# 这样可以用 http://localhost:8080 访问 NAS，满足 Web Serial API 的安全上下文要求

$NasHost = "192.168.10.232"
$NasPort = 2222
$NasUser = "coolwing"

Write-Host "即将打开 SSH 隧道窗口，请在弹出的窗口中输入 NAS 密码。" -ForegroundColor Cyan
Write-Host "隧道建立后，会自动打开 Edge 浏览器访问 http://localhost:8080" -ForegroundColor Cyan
Write-Host ""

# 在新窗口中建立 SSH 隧道（转发本地 8080/5000 到 NAS 的 8080/5000）
$tunnelCmd = "ssh -p $NasPort -L 8080:${NasHost}:8080 -L 5000:${NasHost}:5000 ${NasUser}@${NasHost}"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $tunnelCmd

# 等待用户输入密码并建立隧道
Write-Host "等待 5 秒让隧道建立..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 用 Edge 打开 localhost:8080
Start-Process "msedge" -ArgumentList "http://localhost:8080"

Write-Host ""
Write-Host "Edge 已打开。如果页面还没加载，请再刷新一次。" -ForegroundColor Green
Write-Host "用完之后，关闭 SSH 隧道窗口即可断开。" -ForegroundColor Gray
