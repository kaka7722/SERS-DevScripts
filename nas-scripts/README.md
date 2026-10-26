# NAS 启动 / 停止 / 部署脚本

> 用于管理 NAS（群晖 DSM，DHCP 分配局域网地址）上的 SERS MakerHub 服务。
> NAS 地址自动管理：菜单选 **9. 重新探测 NAS IP**（或 `nas-cli.py detect`）扫描网段并
> 写入 `nas-host.conf`，之后所有命令自动使用——NAS 重启换 IP 后一键恢复，不用改脚本。
> 本机 `~/.ssh/sers_nas` SSH 密钥已授权到 NAS：**所有脚本免密一键执行**；
> 仅当密钥文件缺失时才回退到交互式密码输入。

## 一键入口

双击 **`NAS管理菜单.bat`** —— 菜单里选数字即可：部署 / 快速部署 / 启动 / 停止 / 重启 / 状态 / 日志 / SSH 隧道。
也可以单独双击 `deploy-nas.ps1` 等脚本直接执行对应动作。

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
| `NAS管理菜单.bat` / `NAS管理菜单.ps1` | **一键入口**：双击出菜单，数字键选操作（标题显示当前 NAS 地址，免密） |
| `setup-env.ps1` | 自动创建 Python 虚拟环境并安装依赖 |
| `nas-cli.py` | 核心 CLI，负责连接 NAS、打包、上传、执行 Docker 命令 |
| `common.ps1` | 公共函数（环境初始化 + 密钥免密 / 密码回退） |
| `deploy-nas.ps1` | 构建前端并部署最新前后端到 NAS |
| `deploy-nas-skip-build.ps1` | 跳过前端构建，直接用现有 dist 部署 |
| `start-nas.ps1` | 启动 NAS 服务 |
| `stop-nas.ps1` | 停止 NAS 服务 |
| `restart-nas.ps1` | 重启 NAS 服务 |
| `logs-nas.ps1` | 查看实时日志 |
| `status-nas.ps1` | 查看容器状态 |
| `open-local-tunnel.ps1` | SSH 隧道把 NAS 映射到 localhost（Web Serial 需要安全上下文） |

---

## 使用方法

### 1. 首次初始化

右键 PowerShell 运行一次（之后不用再运行）：

```powershell
cd "C:\Users\Dikun\Desktop\SERS_Dev_Scripts\NAS开启关闭前后端"
.\setup-env.ps1
```

### 2. 日常使用（免密一键）

双击 **`NAS管理菜单.bat`** 选 1（完整部署）或 2（快速部署）；或直接双击单个脚本：

```powershell
.\deploy-nas.ps1      # 完整部署（构建 + 上传 + 重建容器）
.\deploy-nas-skip-build.ps1   # 快速部署（跳过构建）
.\start-nas.ps1      # 启动
.\stop-nas.ps1       # 停止
.\restart-nas.ps1    # 重启
.\logs-nas.ps1       # 日志
.\status-nas.ps1     # 状态
```

> NAS 整机重启后：容器不会自启，双击菜单选 3（启动）即可；
> 若镜像/数据有变动，选 1（部署）会连同重建。

---

## 验证是否更新成功

部署完成后打开（把 `<NAS_IP>` 换成 `nas-host.conf` 里记录的地址，当前为
`192.168.5.13`；NAS 重启换 IP 后先运行菜单选 9 重新探测）：

- 前端：`http://<NAS_IP>:8080`（HTTPS 反代：`https://<NAS_IP>:8443`）
- 后端健康检查：`http://<NAS_IP>:5000/api/health`

如果页面还是旧版，请强制刷新浏览器缓存：`Ctrl + F5`。
