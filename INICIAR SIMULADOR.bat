@echo off
REM ==========================================
REM  GOLF SIMULATOR - Doble click para iniciar
REM ==========================================
REM Para que no se vea la consola, usar:
REM   pythonw.exe launcher.py
REM O crear acceso directo con "Run: Minimized"

cd /d "%~dp0"

REM Intentar con pythonw (sin consola)
where pythonw >nul 2>&1
if %errorlevel%==0 (
    start "" pythonw.exe launcher.py
) else (
    python launcher.py
)
