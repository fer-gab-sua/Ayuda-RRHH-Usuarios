from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ReciboSueldo, FirmaRecibo

@admin.register(ReciboSueldo)
class ReciboSueldoAdmin(admin.ModelAdmin):
    list_display = ['empleado', 'periodo', 'anio', 'estado', 'fecha_emision', 'fecha_vencimiento', 'sueldo_neto', 'acciones']
    list_filter = ['estado', 'anio', 'periodo', 'fecha_emision']
    search_fields = ['empleado__user__first_name', 'empleado__user__last_name', 'empleado__legajo']
    readonly_fields = ['fecha_emision', 'fecha_subida', 'fecha_firma', 'esta_vencido']
    
    fieldsets = (
        ('Información General', {
            'fields': ('empleado', 'periodo', 'anio', 'estado')
        }),
        ('Fechas', {
            'fields': ('fecha_emision', 'fecha_vencimiento', 'fecha_firma', 'fecha_subida')
        }),
        ('Archivos', {
            'fields': ('archivo_pdf', 'archivo_firmado')
        }),
        ('Datos del Recibo', {
            'fields': ('sueldo_bruto', 'descuentos', 'sueldo_neto'),
            'classes': ('collapse',)
        }),
        ('Observaciones', {
            'fields': ('observaciones_empleado', 'observaciones_rrhh'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('subido_por', 'esta_vencido'),
            'classes': ('collapse',)
        }),
    )
    
    def acciones(self, obj):
        """Mostrar acciones disponibles para el recibo"""
        if obj.archivo_pdf:
            return format_html(
                '<a href="{}" target="_blank" class="btn btn-sm btn-primary">Ver PDF</a>',
                obj.archivo_pdf.url
            )
        return "Sin archivo"
    
    acciones.short_description = "Acciones"
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related('empleado', 'empleado__user', 'subido_por')
    
    def save_model(self, request, obj, form, change):
        """Asignar usuario que sube el recibo"""
        if not change:  # Si es nuevo
            obj.subido_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(FirmaRecibo)
class FirmaReciboAdmin(admin.ModelAdmin):
    list_display = ['recibo', 'empleado', 'fecha_firma', 'tipo_firma', 'ip_address']
    list_filter = ['tipo_firma', 'fecha_firma']
    search_fields = ['empleado__user__first_name', 'empleado__user__last_name', 'recibo__periodo', 'recibo__anio']
    readonly_fields = ['fecha_firma', 'ip_address', 'user_agent']
    
    fieldsets = (
        ('Información de la Firma', {
            'fields': ('recibo', 'empleado', 'fecha_firma', 'tipo_firma')
        }),
        ('Detalles Técnicos', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related('recibo', 'empleado', 'empleado__user')
    
    def has_add_permission(self, request):
        """Las firmas no se crean manualmente desde el admin"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Las firmas no se pueden editar"""
        return False
