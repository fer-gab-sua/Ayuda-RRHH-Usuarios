#!/bin/bash
echo "========================================"
echo "Instalando dependencias para Python 3.10"
echo "Compatible con PythonAnywhere"
echo "========================================"

echo ""
echo "Verificando version de Python..."
python3 --version

echo ""
echo "¿Desea continuar con la instalacion? (s/n)"
read continuar

if [[ "$continuar" == "s" || "$continuar" == "S" ]]; then
    echo ""
    echo "Actualizando pip..."
    python3 -m pip install --upgrade pip
    
    echo ""
    echo "Instalando dependencias desde requirements.txt..."
    pip3 install -r requirements.txt
    
    echo ""
    echo "========================================"
    echo "Instalacion completada"
    echo "========================================"
    echo ""
    echo "Para verificar que todo funciona correctamente:"
    echo "1. python3 manage.py check"
    echo "2. python3 manage.py runserver"
    echo ""
else
    echo "Instalacion cancelada."
fi
