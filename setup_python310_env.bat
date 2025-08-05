@echo off
echo 🚀 Configurando entorno virtual con Python 3.10...
echo ============================================================

REM Verificar si Python 3.10 está disponible
py -3.10 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 3.10 no encontrado
    echo 💡 Opciones para instalar Python 3.10:
    echo    1. Desde Microsoft Store: python 3.10
    echo    2. Desde python.org: https://www.python.org/downloads/release/python-31011/
    echo    3. Con winget: winget install Python.Python.3.10
    pause
    exit /b 1
)

echo ✅ Python 3.10 encontrado
py -3.10 --version

REM Eliminar entorno virtual existente
if exist venv (
    echo 🗑️  Eliminando entorno virtual existente...
    rmdir /s /q venv
)

REM Crear entorno virtual con Python 3.10
echo 📦 Creando entorno virtual con Python 3.10...
py -3.10 -m venv venv

if %errorlevel% neq 0 (
    echo ❌ Error creando entorno virtual
    pause
    exit /b 1
)

echo ✅ Entorno virtual creado

REM Activar entorno virtual
echo 🔧 Activando entorno virtual...
call venv\Scripts\activate.bat

REM Actualizar pip
echo 📈 Actualizando pip...
python -m pip install --upgrade pip

REM Verificar versión
echo ✅ Versión de Python en venv:
python --version

REM Instalar dependencias
echo 📦 Instalando dependencias...
pip install -r requirements.txt

if %errorlevel% eq 0 (
    echo ✅ Dependencias instaladas exitosamente
) else (
    echo ❌ Error instalando dependencias
)

echo.
echo 🎉 Configuración completa!
echo ============================================================
echo Para usar el entorno virtual:
echo   1. Activar: venv\Scripts\activate.bat
echo   2. Ejecutar: python manage.py runserver
echo   3. Desactivar: deactivate
echo.
echo 🌐 Ahora tu entorno local usa las mismas versiones que PythonAnywhere!
pause
