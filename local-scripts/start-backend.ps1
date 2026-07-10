# 启动 SERS MakerHub 后端
$ProjectRoot = "C:\Users\Dikun\Desktop\control\2025-12-13Deepseek\2025-12-24Deepseek"
$BackendDir = Join-Path $ProjectRoot "sers-makerhub-backend"

# 检查端口是否被占用
$conn = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -First 1
if ($conn) {
    Write-Host "端口 5000 已被占用 (PID: $($conn.OwningProcess))" -ForegroundColor Yellow
    Write-Host "请先运行 stop-backend.ps1，再重新启动。" -ForegroundColor Yellow
    exit 1
}

Write-Host "正在启动 SERS MakerHub 后端 (http://localhost:5000)..." -ForegroundColor Green
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$BackendDir'; node server.js"
Write-Host "后端已在新窗口启动。" -ForegroundColor Green
