# NAS 启动 / 停止 / 部署脚本

> 用于管理绿联 DXP4800 上的 SERS MakerHub 服务。

## 为什么之前的 `update-nas.ps1` / `update-nas-tar.ps1` 更新后前端还是旧版本？

NAS 上的 Nginx 容器挂载的是 **`frontend/dist`** 目录，而不是前端源码目录。

之前的脚本只是把 `sers-makerhub-frontend-vue` 整个源码文件夹传了上去，**没有先执行 `npm run build`，也没有把构建产物 `dist/` 放到 NAS 的 `frontend/dist/` 位置**，所以网页看到的始终是旧版本。

现在这个 `deploy-nas.ps1` 会先：

1. 在本地执行 `npm run build` 生成最新的 `dist/`。
2. 只把**后端源码**和**前端 dist** 上传到 NAS。
3. 在 NAS 上解压到正确的 `backend/` 和 `frontend/dist/` 目录。
4. 执行 `docker compose up -d --build` 重新构建并启动。

---

## 文件说明

| 脚本 | 作用 |
|------|------|
| `setup-env.ps1` | 自动创建 Python 虚拟环境并安装依赖 |
| `nas-cli.py` | 核心 CLI，负责连接 NAS、打包、上传、执行 Docker 命令 |
| `common.ps1` | 公共函数（环境初始化 + 安全密码读取） |
| `deploy-nas.ps1` | 构建前端并部署最新前后端到 NAS |
| `deploy-nas-skip-build.ps1` | 跳过前端构建，直接用现有 dist 部署 |
| `start-nas.ps1` | 启动 NAS 服务 |
| `stop-nas.ps1` | 停止 NAS 服务 |
| `restart-nas.ps1` | 重启 NAS 服务 |
| `logs-nas.ps1` | 查看实时日志 |
| `status-nas.ps1` | 查看容器状态 |

---

## 使用方法

### 1. 首次初始化

右键 PowerShell 运行一次（之后不用再运行）：

```powershell
cd "C:\Users\Dikun\Desktop\SERS_Dev_Scripts\NAS开启关闭前后端"
.\setup-env.ps1
```

### 2. 部署最新版本

```powershell
.\deploy-nas.ps1
```

按提示输入 NAS 密码即可。

### 3. 常用管理

```powershell
.\start-nas.ps1      # 启动
.\stop-nas.ps1       # 停止
.\restart-nas.ps1    # 重启
.\logs-nas.ps1       # 日志
.\status-nas.ps1     # 状态
```

---

## 验证是否更新成功

部署完成后打开：

- 前端：`http://192.168.10.232:8080`
- 后端健康检查：`http://192.168.10.232:5000/api/health`

如果页面还是旧版，请强制刷新浏览器缓存：`Ctrl + F5`。
