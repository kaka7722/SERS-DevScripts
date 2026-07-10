# SERS MakerHub 本地开发脚本

这些脚本用于在本地快速启动/关闭 SERS MakerHub 的前后端服务。

## 使用前准备

首次运行 PowerShell 脚本时，可能需要调整执行策略：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 脚本说明

| 脚本 | 作用 |
|---|---|
| `start-all.ps1` | 同时启动后端和前端 |
| `stop-all.ps1` | 同时关闭后端和前端 |
| `start-backend.ps1` | 单独启动后端（http://localhost:5000） |
| `stop-backend.ps1` | 单独关闭后端 |
| `start-frontend.ps1` | 单独启动前端（http://localhost:5173） |
| `stop-frontend.ps1` | 单独关闭前端 |

## 使用方法

在 `SERS_Dev_Scripts` 文件夹中，右键对应的 `.ps1` 脚本，选择“使用 PowerShell 运行”。

- 启动：`start-all.ps1`
- 关闭：`stop-all.ps1`

## 注意

- 启动脚本会打开独立的 PowerShell 窗口显示服务日志。
- 关闭脚本通过端口查找并终止对应进程（后端 5000，前端 5173/5174/5175）。
- SSH 远程启停脚本暂缺，如需可后续补充。
