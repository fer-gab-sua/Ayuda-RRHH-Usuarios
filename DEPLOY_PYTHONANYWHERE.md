# � Guía de Despliegue en PythonAnywhere - COMPLETA

Esta guía te ayudará a desplegar tu sistema de RRHH en PythonAnywhere con **TODAS las funcionalidades** habilitadas.

## 🔧 Requisitos Previos

- Cuenta en PythonAnywhere (gratuita o pagada)
- Python 3.10 (disponible en PythonAnywhere)
- Tu repositorio debe estar en GitHub

## 📁 Paso 1: Preparar los Archivos

1. **Versiones Compatible**: El `requirements.txt` ya está configurado con versiones compatibles con Python 3.10
2. **Base de Datos**: Usaremos SQLite (incluida en el repositorio)
3. **Variables de Entorno**: Crear archivo `.env` basado en `.env.example`

## 🚀 Paso 2: Clonar el Repositorio en PythonAnywhere

1. Abrir una consola Bash en PythonAnywhere
2. Ejecutar:
```bash
cd ~
git clone https://github.com/tu-usuario/Ayuda-RRHH-Usuarios.git
cd Ayuda-RRHH-Usuarios
```

### **Paso 3: Crear entorno virtual**
```bash
# Crear entorno virtual con Python 3.10
mkvirtualenv --python=/usr/bin/python3.10 rrhh-env

# Activar el entorno
workon rrhh-env

# Verificar versión
python --version  # Debe mostrar Python 3.10.x

# Instalar dependencias
pip install -r requirements.txt
```

### **Paso 4: Configurar la base de datos**
```bash
# Ya tienes la base de datos SQLite en el repo, pero por si acaso:
python manage.py makemigrations
python manage.py migrate

# Crear superusuario (opcional, si no tienes uno)
python manage.py createsuperuser

# Recopilar archivos estáticos
python manage.py collectstatic --noinput
```

### **Paso 5: Configurar Web App**
1. En el Dashboard, ir a **"Web"**
2. Click **"Add a new web app"**
3. Seleccionar **"Manual configuration"**
4. Seleccionar **"Python 3.10"**
5. Confirmar la creación

### **Paso 6: Configurar WSGI**
1. En la pestaña **"Web"**, encontrar **"WSGI configuration file"**
2. Click en el enlace para editarlo
3. **BORRAR TODO** el contenido existente
4. **PEGAR** este código (cambiar `tu-username` por tu usuario real):

```python
import os
import sys

# Agregar el directorio del proyecto al path
path = '/home/tu-username/Ayuda-RRHH-Usuarios'  # CAMBIAR tu-username
if path not in sys.path:
    sys.path.insert(0, path)

# Configurar Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'proyecto_rrhh.settings'

# Activar el entorno virtual
activate_this = '/home/tu-username/.virtualenvs/rrhh-env/bin/activate_this.py'  # CAMBIAR tu-username
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

5. **Guardar** el archivo (Ctrl+S)

### **Paso 7: Configurar archivos estáticos**
En la pestaña **"Web"**, en la sección **"Static files"**:

1. **Primera entrada** (Static files):
   - **URL**: `/static/`
   - **Directory**: `/home/tu-username/Ayuda-RRHH-Usuarios/staticfiles/`

2. **Segunda entrada** (Media files):
   - **URL**: `/media/`
   - **Directory**: `/home/tu-username/Ayuda-RRHH-Usuarios/media/`

3. Click **"Save"** después de cada entrada

### **Paso 8: Configurar settings para tu dominio**
1. Volver a la **Bash Console**
2. Editar settings.py:

```bash
cd ~/Ayuda-RRHH-Usuarios
nano proyecto_rrhh/settings.py
```

3. En las líneas que dicen `tu-username`, cambiar por tu usuario real:
   - Línea ~28: `ALLOWED_HOSTS = ['tu-username.pythonanywhere.com']`
   - Línea ~29: `CSRF_TRUSTED_ORIGINS = ['https://tu-username.pythonanywhere.com']`
   - Líneas ~32-35: Las rutas de MEDIA_ROOT y STATIC_ROOT

4. Guardar: `Ctrl+X`, luego `Y`, luego `Enter`

### **Paso 9: Recargar la aplicación**
1. Volver a la pestaña **"Web"**
2. Click en el botón verde **"Reload tu-username.pythonanywhere.com"**
3. Esperar a que termine

### **Paso 10: Probar la aplicación**
1. Click en el enlace `https://tu-username.pythonanywhere.com`
2. ¡Debería funcionar! 🎉

## 🔧 Comandos útiles para mantenimiento

### Actualizar código desde GitHub:
```bash
workon rrhh-env
cd ~/Ayuda-RRHH-Usuarios
git pull origin main
python manage.py migrate  # Si hay nuevas migraciones
python manage.py collectstatic --noinput  # Si hay nuevos archivos estáticos
# Luego recargar en la pestaña Web
```

### Ver logs de errores:
```bash
tail -f /var/log/tu-username.pythonanywhere.com.error.log
```

### Acceder a la shell de Django:
```bash
workon rrhh-env
cd ~/Ayuda-RRHH-Usuarios
python manage.py shell
```

## ⚠️ Puntos importantes:
- **Cambiar `tu-username`** por tu usuario real de PythonAnywhere en TODOS los lugares
- La base de datos SQLite ya está incluida en el repositorio
- Los archivos media (firmas, fotos) se mantienen en PythonAnywhere
- El sistema detecta automáticamente que está en PythonAnywhere y usa la configuración correcta

## 🆘 Si algo no funciona:
1. Revisar los logs de error
2. Verificar que todas las rutas tengan tu username correcto
3. Asegurarse de que el entorno virtual esté activado
4. Recargar la aplicación web después de cualquier cambio

¡La aplicación debería funcionar perfectamente con todas las funcionalidades!
