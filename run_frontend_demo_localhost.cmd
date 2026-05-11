@echo off
setlocal
powershell -ExecutionPolicy Bypass -File "%~dp0frontend_demo\run_localhost.ps1" %*
