# 关闭 SERS MakerHub 前端
$ports = @(5173, 5174, 5175)
$killed = @()

foreach ($port in $ports) {
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conns) {
        $pids = $conns.OwningProcess | Sort-Object -Unique
        foreach ($procId in $pids) {
            if ($killed -notcontains $procId) {
                try {
                    Stop-Process -Id $procId -Force
                    Write-Host "已终止前端进程 PID $procId (端口 $port)" -ForegroundColor Green
                    $killed += $procId
                } catch {
                    Write-Host "无法终止前端进程 PID $procId：$_" -ForegroundColor Red
                }
            }
        }
    }
}

if ($killed.Count -eq 0) {
    Write-Host "未找到占用 5173/5174/5175 的前端进程。" -ForegroundColor Gray
} else {
    Write-Host "前端已关闭。" -ForegroundColor Green
}
