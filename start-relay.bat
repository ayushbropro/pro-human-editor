@echo off
title I am pro human editor - relay
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "%~dp0relay.py"
  pause
  exit /b
)
where python >nul 2>nul
if %errorlevel%==0 (
  python "%~dp0relay.py"
  pause
  exit /b
)
echo Python was not found on this PC.
echo.
echo Install it free from https://www.python.org/downloads/
echo During install, tick "Add python.exe to PATH".
echo Then double-click this file again.
echo.
pause
