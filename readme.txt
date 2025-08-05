# 🏢 Sistema de RRHH - Ayuda Usuarios

Sistema completo de gestión de Recursos Humanos desarrollado con Django 5.2.4

## 🚀 Despliegue Rápido

### PythonAnywhere (Recomendado)
1. Lee `DEPLOY_PYTHONANYWHERE.md` para instrucciones completas
2. Ejecuta `bash check_pythonanywhere.sh` para verificar configuración
3. ¡Listo en minutos!

## 📊 Diagrama de Base de Datos
https://dbdiagram.io/d/685cb75af413ba3508ece8f0

## ✨ Características

### 👥 Gestión de Empleados
- Registro completo de empleados con fotos
- Activación/desactivación de empleados
- Gestión de perfiles y datos personales
- Sistema de firmas digitales

### 📋 Gestión de RRHH
- Panel administrativo completo
- Carga masiva de recibos de sueldo
- Gestión de documentación
- Sistema de notificaciones

### 📄 Documentos y Solicitudes
- Subida de documentos por empleados
- Aprobación/rechazo por RRHH
- Solicitudes de vacaciones y permisos
- Certificados laborales

### 🔐 Seguridad
- Autenticación robusta
- Permisos por roles
- Cambio obligatorio de contraseña
- Middleware de seguridad

## 🛠️ Tecnologías

- **Backend:** Django 5.2.4
- **Frontend:** Bootstrap 5, jQuery
- **Base de datos:** SQLite3
- **PDFs:** ReportLab
- **Excel:** openpyxl, pandas
- **Imágenes:** Pillow

## 📁 Estructura del Proyecto

```
apps/
├── empleados/     # Gestión de empleados
├── rrhh/          # Panel administrativo
├── documentos/    # Gestión documental  
├── solicitudes/   # Solicitudes y permisos
├── notificaciones/# Sistema de alertas
└── recibos/       # Recibos de sueldo

templates/         # Plantillas HTML
static/           # Archivos estáticos
media/            # Archivos subidos
```

## 🔧 Instalación Local

```bash
# Clonar repositorio
git clone https://github.com/fer-gab-sua/Ayuda-RRHH-Usuarios.git
cd Ayuda-RRHH-Usuarios

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver
```

## 🌐 URLs Principales

- `/empleados/` - Portal de empleados
- `/rrhh/` - Panel administrativo
- `/admin/` - Django Admin

## 👤 Usuarios de Prueba

La base de datos incluye usuarios de prueba. Consulta con el administrador para credenciales.

## 🔄 Actualizaciones

```bash
# Activar entorno
workon rrhh-env  # PythonAnywhere
# venv\Scripts\activate  # Local

# Actualizar código
git pull origin main

# Aplicar migraciones
python manage.py migrate

# Recopilar estáticos
python manage.py collectstatic --noinput

# Recargar aplicación (PythonAnywhere)
```

## 📞 Soporte

Para soporte técnico o consultas sobre el sistema, contactar al administrador del proyecto.

---
**Desarrollado con ❤️ para mejorar la gestión de RRHH**

