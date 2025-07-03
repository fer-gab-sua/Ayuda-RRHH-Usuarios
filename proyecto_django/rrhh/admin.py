from django.contrib import admin
from .models import Empleado, ReciboSueldo, TipoSolicitud, Solicitud, Documento, Notificacion


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'dni', 'puesto', 'departamento', 'fecha_ingreso']
    list_filter = ['departamento', 'puesto', 'fecha_ingreso']
    search_fields = ['user__first_name', 'user__last_name', 'dni']
    readonly_fields = ['user']


@admin.register(ReciboSueldo)
class ReciboSueldoAdmin(admin.ModelAdmin):
    list_display = ['empleado', 'periodo', 'fecha', 'estado', 'fecha_firma']
    list_filter = ['estado', 'fecha', 'periodo']
    search_fields = ['empleado__user__first_name', 'empleado__user__last_name', 'periodo']
    readonly_fields = ['fecha_firma']


@admin.register(TipoSolicitud)
class TipoSolicitudAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo']
    list_filter = ['activo']


@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ['empleado', 'tipo', 'fecha_desde', 'fecha_hasta', 'estado', 'fecha_solicitud']
    list_filter = ['estado', 'tipo', 'fecha_solicitud']
    search_fields = ['empleado__user__first_name', 'empleado__user__last_name', 'tipo__nombre']
    readonly_fields = ['fecha_solicitud']
    
    def save_model(self, request, obj, form, change):
        if change and 'estado' in form.changed_data:
            from django.utils import timezone
            obj.fecha_respuesta = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'empleado', 'tipo', 'fecha_subida']
    list_filter = ['tipo', 'fecha_subida']
    search_fields = ['nombre', 'empleado__user__first_name', 'empleado__user__last_name']
    readonly_fields = ['fecha_subida']


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'empleado', 'tipo', 'leida', 'fecha_creacion']
    list_filter = ['tipo', 'leida', 'fecha_creacion']
    search_fields = ['titulo', 'empleado__user__first_name', 'empleado__user__last_name']
    readonly_fields = ['fecha_creacion']
