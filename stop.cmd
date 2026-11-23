@echo off
REM Wrapper to run the PowerShell stop script from cmd or PowerShell by typing stop.cmd or stop
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop.ps1" %*
