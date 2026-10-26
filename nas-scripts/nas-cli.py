#!/usr/bin/env python3
"""SERS MakerHub NAS 管理 CLI（Paramiko + SCP）

支持命令：
  deploy   构建前端并打包上传最新前后端到 NAS，重建 Docker 服务
  start    启动 NAS 上的服务
  stop     停止 NAS 上的服务
  restart  重启 NAS 上的服务
  logs     查看实时日志
  status   查看容器状态

密码读取优先级：
  1. 环境变量 NAS_PASSWORD
  2. 终端交互式输入（getpass）
"""

import os
import sys
import tarfile
import tempfile
import shutil
import subprocess
import time
import getpass
import argparse
import paramiko
from scp import SCPClient

# 避免 Windows GBK 终端输出 Docker 彩色/特殊字符时报错
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 2026-09-29 重要（Synology ACL 403 修复）：
# NAS 为 DSM ext4 + Windows ACL 共享文件夹，POSIX 显示 rwxrwxrwx 但内核 ACL 层
# 拒绝容器内 nginx worker（uid 101）遍历 bind-mounted 的 dist（stat/open 均 EACCES），
# chown/chmod/setfacl 均无效。已改为在远端 config/nginx.conf 首行加 `user root;`
# （config/ 不被本部署流程覆盖，故持久生效）。若前端再次出现 403，先检查该行是否还在。
# NAS 地址来源（DHCP 下 NAS 重启可能换 IP，2026-10-09 实测从 .2 漂到 .13）：
#   1. 同目录 nas-host.conf（纯文本，一行 IP）——`nas-cli.py detect` 自动探测写入
#   2. 缺省回退 DEFAULT_NAS_HOST
# DSM 侧做 DHCP 固定分配后可把 nas-host.conf 内容写死，不再依赖探测。
DEFAULT_NAS_HOST = "192.168.5.13"
NAS_PORT = 2222
NAS_USER = "coolwing"
REMOTE_DIR = "/volume1/docker/sers-makerhub"

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_nas_host():
    conf = os.path.join(_SCRIPT_DIR, "nas-host.conf")
    try:
        with open(conf, "r", encoding="utf-8") as f:
            ip = f.read().strip()
            if ip:
                return ip
    except OSError:
        pass
    return DEFAULT_NAS_HOST


NAS_HOST = _load_nas_host()

PROJECT_ROOT = r"C:\Users\Dikun\Desktop\control\2025-12-13Deepseek\2025-12-24Deepseek"
BACKEND_DIR = os.path.join(PROJECT_ROOT, "sers-makerhub-backend")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "sers-makerhub-frontend-vue")
FRONTEND_DIST = os.path.join(FRONTEND_DIR, "dist")

EXCLUDE_NAMES_ANYWHERE = {
    "node_modules",
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".pio",
    ".idea",
    ".vscode",
    # 2026-09-30 重要：用户上传的原始数据**绝不能**参与部署。
    # tar 不认 .gitignore，之前 backend/uploads/ 会被整体打包上传；
    # 配合下方的 `rm -rf backend`，任何在本地快照之后由用户新上传的文件
    # 都会在下次部署时被静默删除（本地看不到，因为 uploads/ 被 gitignore）。
    "uploads",
}
EXCLUDE_SUFFIXES = (".log", ".tar.gz", ".tmp")


def get_password():
    """密码来源优先级：环境变量 → （无专用密钥时才）交互提示 → 空（走密钥）

    2026-10：本机 ~/.ssh/sers_nas 公钥已授权到 NAS。原实现在非交互终端直接 exit(1)，
    自动化无法部署；而"先看 isatty 再提示"在 stdin 被当成 tty 的调用环境里会挂住等输入。
    现在改为：**只要有专用密钥就直接走密钥认证，绝不提示**。
    """
    pw = os.environ.get("NAS_PASSWORD", "")
    if pw:
        return pw
    if _key_path():
        return ""            # 有 sers_nas 密钥 → 密钥认证
    if sys.stdin.isatty():
        return getpass.getpass(f"请输入 NAS ({NAS_USER}) 密码: ")
    print("错误：既没有专用密钥，也没有 NAS_PASSWORD，且当前非交互式终端。")
    sys.exit(1)


def _key_path():
    """专用密钥（文件名非默认，paramiko 不会自动找）"""
    p = os.path.expanduser("~/.ssh/sers_nas")
    return p if os.path.isfile(p) else None


def should_exclude(name):
    if name in EXCLUDE_NAMES_ANYWHERE:
        return True
    if name.endswith(EXCLUDE_SUFFIXES):
        return True
    return False


def tar_filter(member):
    rel = member.name.replace("\\", "/")
    parts = rel.split("/")
    if any(should_exclude(part) for part in parts):
        return None
    return member


def build_frontend():
    print("=" * 60)
    print("正在构建前端生产包...")
    print(f"目录: {FRONTEND_DIR}")
    print("=" * 60)

    if not os.path.isdir(os.path.join(FRONTEND_DIR, "node_modules")):
        print("未检测到 node_modules，先执行 npm install...")
        result = subprocess.run(
            ["npm", "install"],
            cwd=FRONTEND_DIR,
            shell=True,
            text=True,
        )
        if result.returncode != 0:
            print("npm install 失败")
            sys.exit(1)

    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=FRONTEND_DIR,
        shell=True,
        text=True,
    )
    if result.returncode != 0:
        print("前端构建失败")
        sys.exit(1)

    if not os.path.isdir(FRONTEND_DIST):
        print(f"构建后未找到 {FRONTEND_DIST}")
        sys.exit(1)

    print("前端构建完成。\n")


def make_deploy_tar():
    fd, tar_path = tempfile.mkstemp(prefix="sers_deploy_", suffix=".tar.gz")
    os.close(fd)

    print(f"正在打包: {tar_path}")
    with tarfile.open(tar_path, "w:gz") as tar:
        # 后端源码 -> backend/
        print(f"  加入后端: {BACKEND_DIR}")
        tar.add(BACKEND_DIR, arcname="backend", filter=tar_filter)
        # 前端构建产物 -> frontend/dist/
        print(f"  加入前端 dist: {FRONTEND_DIST}")
        tar.add(FRONTEND_DIST, arcname="frontend/dist", filter=tar_filter)

    size_mb = os.path.getsize(tar_path) / 1024 / 1024
    print(f"打包完成，大小: {size_mb:.2f} MB")
    return tar_path


def connect_ssh(password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kwargs = dict(
        hostname=NAS_HOST,
        port=NAS_PORT,
        username=NAS_USER,
        allow_agent=False,
        timeout=30,
        # 2026-10：支持密钥登录（原 look_for_keys=False 只能密码登录，自动化无法使用）
        look_for_keys=True,
    )
    kp = _key_path()
    if kp:
        kwargs["key_filename"] = kp
    if password:
        kwargs["password"] = password
    try:
        ssh.connect(**kwargs)
    except paramiko.AuthenticationException:
        print("认证失败：SSH 密钥未授权，且没有可用密码。")
        print(f"  方案 A：把 {os.path.expanduser('~/.ssh/sers_nas.pub')} 内容追加到 NAS 的 ~/.ssh/authorized_keys")
        print("  方案 B：设置 NAS_PASSWORD 环境变量后再执行")
        sys.exit(1)
    return ssh


def run_command(ssh, command, print_output=True, timeout_s=900):
    """执行远端命令并实时回显。

    2026-10 修复两处会让自动化卡死的问题：
      1) 原先 `get_pty=True`：PTY 下命令（如 `docker compose ps`）结束后通道不一定立刻
         发 EOF，`readline()` 会一直阻塞（实测 status 卡死 >4 分钟无任何输出）。
         改为不带 PTY —— docker compose 的输出仍是逐行流式的，只是没有彩色/动画。
      2) 原先没有超时：一条卡住的命令会让脚本永久挂住。现在到点主动断开并返回非零。
    """
    print(f"\n执行: {command}")
    stdin, stdout, stderr = ssh.exec_command(command, get_pty=False, timeout=timeout_s)
    channel = stdout.channel
    channel.settimeout(1.0)
    deadline = time.time() + timeout_s
    buf = ""
    while True:
        if channel.recv_ready():
            buf += channel.recv(65536).decode("utf-8", "replace")
            *lines, buf = buf.split("\n")
            if print_output:
                for line in lines:
                    print(line)
        if channel.exit_status_ready() and not channel.recv_ready():
            break
        if time.time() > deadline:
            print(f"\n⚠️ 命令超过 {timeout_s}s 未结束，已放弃等待")
            channel.close()
            return 124
        time.sleep(0.05)
    if buf and print_output:
        print(buf)
    return channel.recv_exit_status()


def cmd_deploy(password, skip_build=False):
    if not skip_build:
        build_frontend()
    else:
        print("跳过前端构建，使用现有 dist。\n")

    if not os.path.isdir(BACKEND_DIR):
        print(f"后端目录不存在: {BACKEND_DIR}")
        sys.exit(1)
    if not os.path.isdir(FRONTEND_DIST):
        print(f"前端 dist 不存在: {FRONTEND_DIST}")
        sys.exit(1)

    tar_path = make_deploy_tar()
    try:
        ssh = connect_ssh(password)
        try:
            with SCPClient(ssh.get_transport()) as scp:
                print(f"\n上传到 NAS: {REMOTE_DIR}/deploy.tar.gz")
                scp.put(tar_path, remote_path=f"{REMOTE_DIR}/deploy.tar.gz")

            # 注意：这里**不能**用 `rm -rf backend`。
            # 那会把 NAS 上的 backend/uploads/（用户上传的光谱等原始数据）一并删除，
            # 且因为本地 uploads/ 被 gitignore，覆盖是静默的。
            # 改为「清空 backend 但保留 uploads」：
            deploy_cmd = (
                f"cd {REMOTE_DIR} && "
                "docker compose down && "
                "find backend -mindepth 1 -maxdepth 1 ! -name uploads -exec rm -rf {} + && "
                "rm -rf frontend/dist && "
                "tar -xzf deploy.tar.gz && "
                "rm -f deploy.tar.gz && "
                # 把 NAS 局域网 IP 注入后端环境：云桥下载地址分级裁决需要 NC_LAN_IP
                # 作为 NAS 侧内网地址，否则 Docker 容器读到的 MQTT_BROKER_URL 往往是
                # 容器内主机名，设备从公网入口打开时拿不到可访问的下载地址。
                f"for f in backend/.env.dxp4800 backend/.env.docker backend/.env.local backend/.env; do "
                f"  [ -f \"$f\" ] && sed -i '/^NC_LAN_IP=/d' \"$f\" && echo 'NC_LAN_IP={NAS_HOST}' >> \"$f\"; "
                "done && "
                # NAS 本机 6379 通常已被系统 Redis 占用，把容器 Redis 映射到 6380
                "sed -i 's/6379:6379/6380:6379/' docker-compose.yml && "
                "docker compose up -d --build --force-recreate"
            )
            exit_code = run_command(ssh, deploy_cmd)
            if exit_code != 0:
                print(f"\n部署失败，退出码: {exit_code}")
                sys.exit(1)

            print("\n" + "=" * 60)
            print("部署完成！")
            print(f"  前端: http://{NAS_HOST}:8080")
            print(f"  后端: http://{NAS_HOST}:5000/api/health")
            print("=" * 60)
        finally:
            ssh.close()
    finally:
        os.remove(tar_path)


def detect_nas_host():
    """扫描本机所在 /24 网段，找 2222(SSH)+5000(后端/DSM) 同时开放的 NAS，
    命中则写入 nas-host.conf 并返回 IP；找不到返回 None。"""
    import socket as _socket
    import concurrent.futures as _cf

    base = NAS_HOST.rsplit(".", 1)[0]          # 以当前配置所在网段为扫描范围
    probe_ports = (2222, 5000)

    def probe(ip):
        hits = []
        for port in probe_ports:
            s = _socket.socket()
            s.settimeout(0.4)
            try:
                s.connect((ip, port))
                hits.append(port)
            except OSError:
                pass
            finally:
                s.close()
        return ip, hits

    print(f"正在扫描 {base}.0/24 寻找 NAS（{probe_ports} 同时开放）…")
    with _cf.ThreadPoolExecutor(max_workers=128) as ex:
        for ip, hits in ex.map(probe, [f"{base}.{i}" for i in range(1, 255)]):
            if len(hits) == len(probe_ports):
                print(f"发现 NAS: {ip}")
                conf = os.path.join(_SCRIPT_DIR, "nas-host.conf")
                with open(conf, "w", encoding="utf-8") as f:
                    f.write(ip + "\n")
                print(f"已写入 {conf}（后续命令自动使用）")
                return ip
    return None


def cmd_simple(password, action):
    ssh = connect_ssh(password)
    try:
        if action == "start":
            code = run_command(ssh, f"cd {REMOTE_DIR} && docker compose up -d")
        elif action == "stop":
            code = run_command(ssh, f"cd {REMOTE_DIR} && docker compose down")
        elif action == "restart":
            code = run_command(ssh, f"cd {REMOTE_DIR} && docker compose down && docker compose up -d")
        elif action == "status":
            code = run_command(ssh, f"cd {REMOTE_DIR} && docker compose ps")
        elif action == "logs":
            code = run_command(ssh, f"cd {REMOTE_DIR} && docker compose logs -f --tail 100")
        else:
            print(f"未知操作: {action}")
            sys.exit(1)
        if code != 0:
            sys.exit(code)
    finally:
        ssh.close()


def main():
    parser = argparse.ArgumentParser(description="SERS MakerHub NAS 管理工具")
    parser.add_argument(
        "command",
        choices=["deploy", "start", "stop", "restart", "logs", "status", "detect"],
        help="要执行的操作（detect = 重新探测 NAS IP 并记忆，NAS 重启换 IP 后用）",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="deploy 时跳过前端构建（使用现有 dist）",
    )
    args = parser.parse_args()

    if args.command == "detect":
        if not detect_nas_host():
            print("未找到 NAS：请确认 NAS 已开机、与本机在同一网段。")
            sys.exit(1)
        return

    password = get_password()

    if args.command == "deploy":
        cmd_deploy(password, skip_build=args.skip_build)
    else:
        cmd_simple(password, args.command)


if __name__ == "__main__":
    main()
