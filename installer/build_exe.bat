@echo off
REM ===== Genera dist\DeliciousFoodCostos\DeliciousFoodCostos.exe (requiere Python + internet UNA vez) =====
chcp 65001 >nul
cd /d "%~dp0\.."
python -m pip install -r installer\requirements-build.txt
python -m PyInstaller --noconfirm --onedir --console --name DeliciousFoodCostos --paths backend backend\server.py --hidden-import seed --hidden-import costing --hidden-import reports --hidden-import exports --hidden-import entities --hidden-import db
if errorlevel 1 (echo Error al generar el ejecutable & pause & exit /b 1)
xcopy /E /I /Y config dist\DeliciousFoodCostos\config
xcopy /E /I /Y database dist\DeliciousFoodCostos\database
xcopy /E /I /Y public dist\DeliciousFoodCostos\public
mkdir dist\DeliciousFoodCostos\data 2>nul
echo.
echo Listo: dist\DeliciousFoodCostos\DeliciousFoodCostos.exe
echo Para crear el INSTALADOR (Setup.exe) abra installer\instalador.iss con Inno Setup y pulse Compilar.
pause
