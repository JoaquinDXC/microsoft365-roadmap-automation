@echo off
REM Script de setup automático para M365 Roadmap Automation
REM Compatible con cmd.exe en Windows

REM IMPORTANT: Ensure we're in the correct directory
cd /d "%~dp0"

echo.
echo ====================================================
echo M365 Roadmap Automation - Setup Automático
echo ====================================================
echo.
echo Working Directory: %CD%
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no encontrado
    echo Por favor, instala Python desde https://www.python.org/downloads/
    echo Recuerda marcar "Add Python to PATH"
    pause
    exit /b 1
)

echo ✓ Python encontrado
python --version
echo.

REM Crear entorno virtual
echo Creando entorno virtual...
if exist venv (
    echo ✓ Entorno virtual ya existe
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: No se pudo crear el entorno virtual
        pause
        exit /b 1
    )
    echo ✓ Entorno virtual creado
)
echo.

REM Activar entorno virtual
echo Activando entorno virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: No se pudo activar el entorno virtual
    pause
    exit /b 1
)
echo ✓ Entorno virtual activado
echo.

REM Instalar dependencias
echo Instalando dependencias...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)
echo ✓ Dependencias instaladas
echo.

REM Copiar .env.example a .env si no existe
if exist .env (
    echo ✓ Archivo .env ya existe
) else (
    copy .env.example .env
    echo ✓ Archivo .env creado
    echo IMPORTANTE: Edita .env con tus credenciales
)
echo.

REM Validar configuración
echo Validando configuración...
python test_config.py
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Configuración inválida
    echo Por favor, edita el archivo .env con tus credenciales
    pause
    exit /b 1
)
echo.

REM Éxito
echo ====================================================
echo ✓ SETUP COMPLETADO
echo ====================================================
echo.
echo Próximos pasos:
echo 1. Edita el archivo .env con tus credenciales:
echo    - GEMINI_API_KEY (tu key de Google Gemini)
echo    - EMAIL_FROM (tu email de Office 365)
echo    - EMAIL_PASSWORD (contraseña de aplicación)
echo    - EMAIL_TO (destino del email)
echo.
echo 2. Para ejecutar la automatización:
echo    python main.py
echo.
echo 3. Para automatizar con Task Scheduler:
echo    Ver README.md sección "Ejecución Automática"
echo.
pause
