@echo off
setlocal

REM One-click runtime environment debug launcher
REM Optional arg1: steps count, default 2
set STEPS=%~1
if "%STEPS%"=="" set STEPS=2

set SCRIPT_DIR=%~dp0
set CLIENT_GRPC_DIR=%SCRIPT_DIR%\..\..\..
for %%I in ("%CLIENT_GRPC_DIR%") do set CLIENT_GRPC_DIR=%%~fI

set WORKSPACE_ROOT=%CLIENT_GRPC_DIR%\..\..\..
for %%I in ("%WORKSPACE_ROOT%") do set WORKSPACE_ROOT=%%~fI

set VENV_PY=%WORKSPACE_ROOT%\.venv\Scripts\python.exe
set DEBUG_SCRIPT=%CLIENT_GRPC_DIR%\dev_test\debug_backend_bridge.py

echo [INFO] client_gRPC dir: %CLIENT_GRPC_DIR%
echo [INFO] workspace root: %WORKSPACE_ROOT%
echo [INFO] steps: %STEPS%
echo [INFO] debug script: %DEBUG_SCRIPT%

if exist "%VENV_PY%" (
    echo [INFO] using venv python: %VENV_PY%
    "%VENV_PY%" "%DEBUG_SCRIPT%" --steps %STEPS%
) else (
    echo [WARN] venv python not found, fallback to py -3
    py -3 "%DEBUG_SCRIPT%" --steps %STEPS%
)

set EXIT_CODE=%ERRORLEVEL%
echo [INFO] finished with exit code: %EXIT_CODE%
exit /b %EXIT_CODE%
