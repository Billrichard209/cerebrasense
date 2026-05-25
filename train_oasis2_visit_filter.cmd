@echo off
setlocal
set "ROOT=%~dp0alz_backend"
"%ROOT%\.venv\Scripts\python.exe" "%ROOT%\scripts\train_oasis2.py" --config "%ROOT%\configs\oasis2_train_improved.yaml" --training-cohort visit_filter %*
