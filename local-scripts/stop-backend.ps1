# 关闭 SERS MakerHub 后端
$killed = @()
$conn = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -First 1
if ($conn) {
    $pids = @($conn.OwningProcess) | Sort-Object -Unique
    foreach ($procId in $pids) {
        if ($killed -notcontains $procId) {
            try {
                Stop-Process -Id $procId -Force
                Write-Host "已终止后端进程 PID $procId" -ForegroundColor Green
                $killed += $procId
            } catch {
                Write-Host "无法终止后端进程 PID $procId：$_" -ForegroundColor Red
            }
        }
    }
}

if ($killed.Count -eq 0) {
    Write-Host "未找到占用端口 5000 的后端进程。" -ForegroundColor Gray
} else {
    Write-Host "后端已关闭。" -ForegroundColor Green
}
