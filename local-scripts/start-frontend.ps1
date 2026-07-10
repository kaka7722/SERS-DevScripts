# 启动 SERS MakerHub 前端
$ProjectRoot = "C:\Users\Dikun\Desktop\control\2025-12-13Deepseek\2025-12-24Deepseek"
$FrontendDir = Join-Path $ProjectRoot "sers-makerhub-frontend-vue"

# 检查端口是否被占用
$conn = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | Select-Object -First 1
if ($conn) {
    Write-Host "端口 5173 已被占用 (PID: $($conn.OwningProcess))" -ForegroundColor Yellow
    Write-Host "请先运行 stop-frontend.ps1，再重新启动。" -ForegroundColor Yellow
    exit 1
}

Write-Host "正在启动 SERS MakerHub 前端 (http://localhost:5173)..." -ForegroundColor Green
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$FrontendDir'; npm run dev"
Write-Host "前端已在新窗口启动。" -ForegroundColor Green
