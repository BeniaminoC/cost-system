@echo off
chcp 65001 >nul
title Delicious Food - Sistema de Costos
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo No se encontro Python 3.9 o superior. Instalelo desde python.org o use el instalador .exe
  pause & exit /b 1
)
python backend\server.py
pause
