@echo off
rem 开发启动: 双击运行 Qpdf (规格 §6.1)
cd /d "%~dp0"
".venv\Scripts\python.exe" "app\main.py"
if errorlevel 1 pause
