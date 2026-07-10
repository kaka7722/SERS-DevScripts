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
import getpass
import argparse
import paramiko
from scp import SCPClient

# 避免 Windows GBK 终端输出 Docker 彩色/特殊字符时报错
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

NAS_HOST = "192.168.10.232"
NAS_PORT = 2222
NAS_USER = "coolwing"
REMOTE_DIR = "/volume1/docker/sers-makerhub"

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
}
EXCLUDE_SUFFIXES = (".log", ".tar.gz", ".tmp")


def get_password():
    pw = os.environ.get("NAS_PASSWORD", "")
    if pw:
        return pw
    if sys.stdin.isatty():
        return getpass.getpass(f"请输入 NAS ({NAS_USER}) 密码: ")
    print("错误：未设置 NAS_PASSWORD 环境变量，且当前非交互式终端。")
    sys.exit(1)


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
    ssh.connect(
        hostname=NAS_HOST,
        port=NAS_PORT,
        username=NAS_USER,
        password=password,
        look_for_keys=False,
        allow_agent=False,
        timeout=30,
    )
    return ssh


def run_command(ssh, command, print_output=True):
    print(f"\n执行: {command}")
    stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
    if print_output:
        for line in iter(stdout.readline, ""):
            print(line, end="")
    return stdout.channel.recv_exit_status()


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

            deploy_cmd = (
                f"cd {REMOTE_DIR} && "
                "docker compose down && "
                "rm -rf backend frontend/dist && "
                "tar -xzf deploy.tar.gz && "
                "rm -f deploy.tar.gz && "
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
        choices=["deploy", "start", "stop", "restart", "logs", "status"],
        help="要执行的操作",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="deploy 时跳过前端构建（使用现有 dist）",
    )
    args = parser.parse_args()

    password = get_password()

    if args.command == "deploy":
        cmd_deploy(password, skip_build=args.skip_build)
    else:
        cmd_simple(password, args.command)


if __name__ == "__main__":
    main()
