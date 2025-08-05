@echo off
echo ========================================
echo Instalando dependencias para Python 3.10
echo Compatible con PythonAnywhere
echo ========================================

echo.
echo Verificando version de Python...
python --version

echo.
echo ¿Desea continuar con la instalacion? (S/N)
set /p continuar=

if /i "%continuar%"=="S" (
    echo.
    echo Actualizando pip...
    python -m pip install --upgrade pip
    
    echo.
    echo Instalando dependencias desde requirements.txt...
    pip install -r requirements.txt
    
    echo.
    echo ========================================
    echo Instalacion completada
    echo ========================================
    echo.
    echo Para verificar que todo funciona correctamente:
    echo 1. python manage.py check
    echo 2. python manage.py runserver
    echo.
) else (
    echo Instalacion cancelada.
)

pause
