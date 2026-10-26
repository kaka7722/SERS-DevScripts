@echo off
REM SERS MakerHub NAS 管理菜单（双击运行）
chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0NAS管理菜单.ps1"
pause
