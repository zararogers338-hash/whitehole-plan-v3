@echo off
cd /d "%~dp0"
python launcher.py run
if errorlevel 1 pause
