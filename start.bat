@echo off
chcp 65001 >nul
title AI Campus Companion - Local Acceptance Server
cd /d "%~dp0"

echo ============================================================
echo   AI Campus Learning Companion - Local Acceptance Server
echo ============================================================
echo.

set "PYEXE="
where python >nul 2>nul
if not errorlevel 1 set "PYEXE=python"
if not defined PYEXE (
  where python3 >nul 2>nul
  if not errorlevel 1 set "PYEXE=python3"
)

if not defined PYEXE (
  echo [ERROR] Python 3.8+ was not found in PATH.
  echo.
  echo   Fix: install Python from https://www.python.org/downloads/
  echo        and CHECK "Add Python to PATH" during setup.
  echo   Alternative: open a terminal here and run: python launch.py
  echo.
  pause
  exit /b 1
)

echo Using interpreter: %PYEXE%
echo.
"%PYEXE%" launch.py

echo.
echo [Server stopped] Press any key to close this window.
pause >nul
