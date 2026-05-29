@echo off
setlocal
set "WORKSPACE=%~dp0.."
pushd "%WORKSPACE%"
".\alz_backend\.venv\Scripts\python.exe" ".\alz_backend\scripts\build_cerebrasense_control_tower.py" --frontend-payload-path ".\frontend_demo\data\research_mode.json" %*
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%
