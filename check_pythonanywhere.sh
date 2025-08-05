#!/bin/bash

# 🚀 Script de verificación para despliegue en PythonAnywhere
# Ejecutar DESPUÉS de clonar el repositorio y activar el entorno virtual

echo "🔍 Verificando configuración para PythonAnywhere..."
echo "=================================="

# Verificar estructura del proyecto
echo "📁 Verificando estructura del proyecto..."
if [ -f "manage.py" ]; then
    echo "✅ manage.py encontrado"
else
    echo "❌ manage.py NO encontrado - verifica que estés en el directorio correcto"
    exit 1
fi

if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt encontrado"
else
    echo "❌ requirements.txt NO encontrado"
    exit 1
fi

if [ -f "proyecto_rrhh/settings.py" ]; then
    echo "✅ settings.py encontrado"
else
    echo "❌ settings.py NO encontrado"
    exit 1
fi

if [ -f "db.sqlite3" ]; then
    echo "✅ Base de datos SQLite encontrada"
else
    echo "⚠️  Base de datos SQLite NO encontrada - se creará con las migraciones"
fi

# Verificar Python y dependencias
echo ""
echo "🐍 Verificando Python y entorno virtual..."
python_version=$(python --version 2>&1)
echo "Python: $python_version"

if python -c "import django" 2>/dev/null; then
    django_version=$(python -c "import django; print(django.get_version())")
    echo "✅ Django $django_version instalado"
else
    echo "❌ Django NO instalado - ejecuta: pip install -r requirements.txt"
    exit 1
fi

# Verificar configuración de Django
echo ""
echo "⚙️  Verificando configuración de Django..."
if python manage.py check --deploy 2>/dev/null; then
    echo "✅ Configuración de Django válida"
else
    echo "⚠️  Hay advertencias en la configuración (normal para desarrollo)"
fi

# Verificar migraciones
echo ""
echo "🗄️  Verificando migraciones..."
if python manage.py showmigrations 2>/dev/null | grep -q "\[ \]"; then
    echo "⚠️  Hay migraciones pendientes - ejecuta: python manage.py migrate"
else
    echo "✅ Migraciones aplicadas"
fi

# Verificar archivos estáticos
echo ""
echo "📦 Verificando archivos estáticos..."
if [ -d "static" ]; then
    echo "✅ Directorio static encontrado"
else
    echo "⚠️  Directorio static NO encontrado"
fi

if [ -d "staticfiles" ]; then
    echo "✅ Directorio staticfiles encontrado"
else
    echo "⚠️  Directorio staticfiles NO encontrado - ejecuta: python manage.py collectstatic"
fi

echo ""
echo "📋 RESUMEN DE PASOS PENDIENTES:"
echo "=================================="
echo "1. Cambiar 'tu-username' por tu usuario real en:"
echo "   - wsgi_pythonanywhere.py"
echo "   - proyecto_rrhh/settings.py (si es necesario)"
echo ""
echo "2. En PythonAnywhere Web App, configurar:"
echo "   - WSGI: usar el contenido de wsgi_pythonanywhere.py"
echo "   - Static files: /static/ → /home/tu-username/Ayuda-RRHH-Usuarios/staticfiles/"
echo "   - Media files: /media/ → /home/tu-username/Ayuda-RRHH-Usuarios/media/"
echo ""
echo "3. Ejecutar si es necesario:"
echo "   - python manage.py migrate"
echo "   - python manage.py collectstatic --noinput"
echo "   - python manage.py createsuperuser"
echo ""
echo "✅ ¡Tu aplicación está lista para PythonAnywhere!"
echo "📖 Lee DEPLOY_PYTHONANYWHERE.md para instrucciones detalladas"
