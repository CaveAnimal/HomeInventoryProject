@echo off
REM Wrapper to run the PowerShell start script from cmd or PowerShell by typing start.cmd or start
REM Note: 'start' is a shell builtin in PowerShell and Cmd; to run this file type start.cmd or .\start.cmd
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*
