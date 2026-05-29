@echo off
setlocal
set "ROOT=%~dp0alz_backend"
"%ROOT%\.venv\Scripts\python.exe" "%ROOT%\scripts\build_cerebrasense_control_tower.py" --frontend-payload-path "%~dp0frontend_demo\data\research_mode.json" %*
