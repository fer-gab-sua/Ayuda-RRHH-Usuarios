from django.contrib import admin
from .models import PerfilRRHH, AprobacionSolicitud, LogActividad


@admin.register(PerfilRRHH)
class PerfilRRHHAdmin(admin.ModelAdmin):
    list_display = ['user', 'departamento', 'puede_aprobar_solicitudes', 'puede_subir_recibos']
    list_filter = ['puede_aprobar_solicitudes', 'puede_subir_recibos', 'puede_gestionar_empleados']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']


@admin.register(AprobacionSolicitud)
class AprobacionSolicitudAdmin(admin.ModelAdmin):
    list_display = ['solicitud', 'aprobador', 'fecha_aprobacion']
    list_filter = ['fecha_aprobacion']
    search_fields = ['solicitud__empleado__user__first_name', 'aprobador__user__username']
    readonly_fields = ['fecha_aprobacion']


@admin.register(LogActividad)
class LogActividadAdmin(admin.ModelAdmin):
    list_display = ['usuario_rrhh', 'tipo_actividad', 'empleado_afectado', 'fecha']
    list_filter = ['tipo_actividad', 'fecha']
    search_fields = ['usuario_rrhh__user__username', 'descripcion']
    readonly_fields = ['fecha']
