# 🏢 Sistema de RRHH - Ayuda Usuarios

Sistema completo de gestión de recursos humanos desarrollado en Django, compatible con **Python 3.10** y optimizado para despliegue en **PythonAnywhere**.

## 🚀 Características Principales

- ✅ **Gestión de Empleados**: Perfiles completos, domicilios, obra social
- ✅ **Recibos de Sueldo**: Carga, visualización y firma digital
- ✅ **Generación de PDFs**: Recibos profesionales con formato empresarial
- ✅ **Panel de RRHH**: Administración centralizada de empleados
- ✅ **Documentos**: Carga y gestión de documentos por empleado
- ✅ **Notificaciones**: Sistema de avisos y comunicaciones
- ✅ **Solicitudes**: Vacaciones, días de estudio, etc.
- ✅ **Autenticación**: Login seguro con cambio obligatorio de contraseña
- ✅ **Responsive**: Interfaz adaptada a móviles y tablets

## 🔧 Tecnologías

- **Backend**: Django 4.2.16 (LTS)
- **Frontend**: Bootstrap 5 + Crispy Forms
- **Base de Datos**: SQLite (incluida)
- **PDFs**: ReportLab + PyPDF2
- **Excel**: Pandas + NumPy + OpenPyXL
- **Imágenes**: Pillow
- **Configuración**: Python-decouple

## 📋 Requisitos

- **Python 3.10** (compatible con PythonAnywhere)
- **Sistema Operativo**: Windows, Linux, macOS
- **Memoria**: 512MB RAM mínimo
- **Espacio**: 100MB libres

## 🚀 Instalación Local

### Opción 1: Instalación Automática (Windows)
```bash
# Clonar repositorio
git clone https://github.com/fer-gab-sua/Ayuda-RRHH-Usuarios.git
cd Ayuda-RRHH-Usuarios

# Ejecutar instalador automático
instalar_dependencias.bat
```

### Opción 2: Instalación Manual
```bash
# Clonar repositorio
git clone https://github.com/fer-gab-sua/Ayuda-RRHH-Usuarios.git
cd Ayuda-RRHH-Usuarios

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias (versiones optimizadas para Python 3.10)
pip install -r requirements.txt

# Configurar base de datos
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver
```

## 🌐 Despliegue en PythonAnywhere

**¡Despliegue completo con TODAS las funcionalidades!**

Sigue la guía detallada: [DEPLOY_PYTHONANYWHERE.md](DEPLOY_PYTHONANYWHERE.md)

Resumen rápido:
```bash
# En PythonAnywhere Bash Console:
cd ~
git clone https://github.com/tu-usuario/Ayuda-RRHH-Usuarios.git
cd Ayuda-RRHH-Usuarios

mkvirtualenv --python=/usr/bin/python3.10 rrhh-env
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

## ✅ Verificación del Sistema

```bash
# Verificar que todo funciona correctamente
python verificar_sistema.py
```

Este script verifica:
- ✅ Dependencias instaladas
- ✅ Configuración de Django
- ✅ Funciones de PDF
- ✅ Conectividad de base de datos

## 📁 Estructura del Proyecto

```
Ayuda-RRHH-Usuarios/
├── apps/
│   ├── empleados/          # Gestión de empleados
│   ├── recibos/            # Recibos de sueldo y PDFs
│   ├── rrhh/              # Panel administrativo RRHH
│   ├── documentos/        # Gestión de documentos
│   ├── notificaciones/    # Sistema de notificaciones
│   └── solicitudes/       # Solicitudes de empleados
├── static/                # Archivos estáticos (CSS, JS, imágenes)
├── templates/             # Plantillas HTML
├── media/                 # Archivos subidos (firmas, PDFs)
├── proyecto_rrhh/         # Configuración principal Django
├── requirements.txt       # Dependencias (Python 3.10 compatible)
├── DEPLOY_PYTHONANYWHERE.md  # Guía de despliegue
├── verificar_sistema.py   # Script de verificación
└── db.sqlite3            # Base de datos SQLite
```

## 👥 Usuarios y Permisos

### Tipos de Usuario
1. **Empleado**: Acceso a su perfil, recibos y documentos
2. **RRHH**: Acceso completo a gestión de empleados
3. **Superusuario**: Acceso completo al sistema

### Credenciales por Defecto
- **Usuario**: Tu número de documento
- **Contraseña**: Últimos 6 dígitos del documento
- **Cambio obligatorio**: Se requiere cambiar la contraseña en el primer login

## 🔧 Configuraciones Importantes

### Variables de Entorno (.env)
```env
# Para PythonAnywhere
PYTHONANYWHERE_DOMAIN=tu-usuario.pythonanywhere.com

# Email (opcional)
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-password-app

# Desarrollo
DEBUG=False
```

### Configuración Automática
El sistema detecta automáticamente el entorno:
- **Local**: DEBUG=True, SQLite local
- **PythonAnywhere**: DEBUG=False, configuración optimizada
- **Render**: DEBUG=False, configuración para Render

## 📊 Funcionalidades Detalladas

### 🧑‍💼 Gestión de Empleados
- Perfiles completos con foto
- Datos laborales y personales
- Domicilios y obra social
- Historial de actividades
- Activación/desactivación

### 💰 Recibos de Sueldo
- Carga masiva desde Excel
- Generación de PDFs profesionales
- Firma digital de recibos
- Formato empresarial personalizable
- Descarga individual o masiva

### 📋 Panel RRHH
- Vista consolidada de empleados
- Gestión de recibos por lotes
- Reportes y estadísticas
- Administración de documentos

### 📄 Sistema de Documentos
- Carga por empleado
- Categorización automática
- Visualización en línea
- Control de acceso

## 🚨 Troubleshooting

### Problemas Comunes

**Error: "Could not find a version that satisfies the requirement"**
```bash
# Usar Python 3.10 específicamente
python3.10 -m pip install -r requirements.txt
```

**Error: "Import Error" en librerías**
```bash
# Verificar instalación
python verificar_sistema.py

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

**Error: "Static files not found"**
```bash
python manage.py collectstatic --noinput
```

### Logs y Debugging
```bash
# Ver logs en desarrollo
python manage.py runserver --verbosity=2

# En PythonAnywhere
tail -f /var/log/tu-usuario.pythonanywhere.com.error.log
```

## 🔄 Actualizaciones

```bash
# Actualizar desde Git
git pull origin main

# Instalar nuevas dependencias
pip install -r requirements.txt

# Aplicar migraciones
python manage.py migrate

# Recopilar estáticos
python manage.py collectstatic --noinput
```

## 📞 Soporte

- **Documentación**: Ver archivos .md en el repositorio
- **Issues**: Crear issue en GitHub
- **Wiki**: Información adicional en el wiki del proyecto

## 📝 Licencia

Este proyecto está bajo licencia MIT. Ver archivo LICENSE para más detalles.

## 🎉 ¡Listo para Producción!

Este sistema está completamente preparado para:
- ✅ Despliegue en PythonAnywhere
- ✅ Uso en producción con empleados reales
- ✅ Todas las funcionalidades habilitadas
- ✅ Compatibilidad completa con Python 3.10
- ✅ Interfaz profesional y responsive

¡Tu sistema de RRHH está listo para usar! 🚀
