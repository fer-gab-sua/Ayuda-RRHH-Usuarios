# Portal RH - Sistema de Recursos Humanos

Este es un sistema de gestión de recursos humanos desarrollado en Django, basado en los templates HTML originales.

## Características

- **Dashboard principal** con resumen de actividades
- **Gestión de perfil** de empleado con foto y datos personales
- **Recibos de sueldo** con sistema de firma digital
- **Solicitudes** (vacaciones, días de estudio, etc.)
- **Subida de certificados** y documentos
- **Sistema de notificaciones** en tiempo real
- **Panel de administración** para RH

## Instalación

1. **Activar el entorno virtual:**
   ```bash
   # El entorno ya está creado en venv/
   venv\Scripts\activate  # En Windows
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Aplicar migraciones:**
   ```bash
   python manage.py migrate
   ```

4. **Crear datos de ejemplo:**
   ```bash
   python manage.py crear_datos_ejemplo
   ```

## Usuarios de ejemplo

### Usuario empleado:
- **Usuario:** fernando
- **Contraseña:** fernando123

### Usuario administrador:
- **Usuario:** admin
- **Contraseña:** admin123

## Ejecutar el servidor

```bash
python manage.py runserver
```

El sistema estará disponible en: http://127.0.0.1:8000/

## Panel de administración

Accede al panel de administración en: http://127.0.0.1:8000/admin/

Desde aquí puedes:
- Gestionar empleados
- Subir recibos de sueldo
- Crear notificaciones
- Aprobar/rechazar solicitudes
- Administrar tipos de solicitud

## Estructura del proyecto

```
proyecto_django/
├── rrhh/                   # Aplicación principal
│   ├── models.py          # Modelos de base de datos
│   ├── views.py           # Vistas (lógica de negocio)
│   ├── forms.py           # Formularios
│   ├── urls.py            # URLs de la aplicación
│   └── admin.py           # Configuración del admin
├── templates/             # Templates HTML
│   ├── base.html         # Template base
│   ├── registration/     # Templates de login
│   └── rrhh/            # Templates de la aplicación
├── static/               # Archivos estáticos
│   ├── css/             # Estilos CSS
│   └── img/             # Imágenes
├── media/               # Archivos subidos por usuarios
└── portal_rh/          # Configuración del proyecto
    ├── settings.py     # Configuración principal
    └── urls.py         # URLs principales
```

## Modelos de datos

### Empleado
- Datos personales y laborales
- Relación one-to-one con User de Django
- Foto de perfil

### ReciboSueldo
- Archivos PDF de recibos
- Estados: pendiente, firmado, disconformidad
- Sistema de firma con fecha y observaciones

### Solicitud
- Diferentes tipos de solicitudes
- Estados: pendiente, aprobada, rechazada
- Fechas desde/hasta y motivos

### Documento
- Documentos importantes y certificados
- Categorización por tipos
- Subida de archivos

### Notificacion
- Sistema de notificaciones para empleados
- Tipos: info, alerta, recordatorio
- Control de leído/no leído

## Funcionalidades principales

### Para empleados:
- Ver y firmar recibos de sueldo
- Actualizar perfil personal
- Enviar solicitudes (vacaciones, permisos, etc.)
- Subir certificados y documentos
- Ver notificaciones

### Para administradores (RH):
- Gestionar todos los empleados
- Subir recibos de sueldo
- Aprobar/rechazar solicitudes
- Enviar notificaciones
- Administrar documentos

## Próximas mejoras

- [ ] Notificaciones por email
- [ ] Exportación de reportes
- [ ] Calendario de vacaciones
- [ ] Integración con sistemas de nómina
- [ ] API REST para integración con otros sistemas
- [ ] Historial de cambios en perfil
- [ ] Firma digital con certificados

## Tecnologías utilizadas

- **Backend:** Django 5.2.3
- **Base de datos:** SQLite (fácil de cambiar a PostgreSQL/MySQL)
- **Frontend:** HTML, CSS, JavaScript
- **Archivos:** Pillow para manejo de imágenes
- **Autenticación:** Sistema de auth integrado de Django
