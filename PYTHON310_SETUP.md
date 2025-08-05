# 🐍 Configuración de Python 3.10 para PythonAnywhere

Este repositorio está configurado para funcionar con **Python 3.10**, la misma versión que se usa en PythonAnywhere.

## 📋 Instalación rápida

### Opción 1: Script automático (Recomendado)
```powershell
# 1. Ejecutar instalador automático
python instalar_python310.py

# 2. Configurar entorno virtual
.\setup_python310_env.ps1
```

### Opción 2: Manual con PowerShell
```powershell
# 1. Instalar Python 3.10
winget install Python.Python.3.10

# 2. Configurar entorno
.\setup_python310_env.ps1
```

### Opción 3: Manual con CMD
```cmd
# 1. Instalar Python 3.10 (una de estas opciones):
# - Microsoft Store: python 3.10
# - Winget: winget install Python.Python.3.10
# - Descargar: https://www.python.org/downloads/release/python-31011/

# 2. Configurar entorno
setup_python310_env.bat
```

## 🔧 Verificación

Después de la instalación, verifica que todo funcione:

```powershell
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Verificar versión (debe ser 3.10.x)
python --version

# Ejecutar el proyecto
python manage.py runserver
```

## 📦 Dependencias incluidas

El `requirements.txt` incluye todas las dependencias compatibles con Python 3.10:

- **Django 4.2.16** - Framework web
- **reportlab 4.2.5** - Generación de PDFs
- **pandas 2.0.3** - Análisis de datos
- **numpy 1.24.4** - Computación numérica
- **Pillow 10.4.0** - Manejo de imágenes
- **openpyxl 3.1.5** - Archivos Excel

## 🌐 Compatibilidad con PythonAnywhere

✅ **Misma versión de Python** (3.10)  
✅ **Mismas versiones de dependencias**  
✅ **Misma base de datos** (SQLite)  
✅ **Configuración automática de entorno**  

## 🚨 Solución de problemas

### Error: Python 3.10 no encontrado
```powershell
# Verificar instalaciones disponibles
py --list

# Si no aparece 3.10, instalar manualmente:
# 1. Microsoft Store: buscar "Python 3.10"
# 2. O desde: https://www.python.org/downloads/release/python-31011/
```

### Error al crear entorno virtual
```powershell
# Eliminar entorno existente
Remove-Item -Recurse -Force venv

# Crear nuevamente
py -3.10 -m venv venv
```

### Error instalando dependencias
```powershell
# Actualizar pip primero
python -m pip install --upgrade pip

# Instalar una por una si hay problemas
pip install Django==4.2.16
pip install reportlab==4.2.5
# etc...
```

## 📚 Comandos útiles

```powershell
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Desactivar entorno virtual
deactivate

# Instalar nueva dependencia
pip install paquete==version

# Exportar dependencias actuales
pip freeze > requirements.txt

# Ejecutar servidor de desarrollo
python manage.py runserver

# Hacer migraciones
python manage.py makemigrations
python manage.py migrate
```

---

🎉 **¡Listo!** Ahora tu entorno local funciona exactamente igual que PythonAnywhere.
