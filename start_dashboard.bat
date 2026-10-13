@echo off
title Spotify Stats Dashboard
cd /d "%~dp0"
echo Iniciando Spotify Stats Dashboard...
start "" "http://localhost:5000"
".venv\Scripts\python.exe" app.py
pause
