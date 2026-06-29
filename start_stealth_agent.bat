@echo off
echo ===================================================
echo   Sentinela - Inicializando Agente Stealth (OODA)
echo ===================================================
echo.
echo Este comando ira acionar o run_sa_instagram_stealth.py
echo Pressione Ctrl+C a qualquer momento para cancelar.
echo.

cd /d "%~dp0"
python scripts\run_sa_instagram_stealth.py

pause
