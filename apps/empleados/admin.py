from django.contrib import admin
from .models import Empleado, FamiliarEmpleado, ActividadEmpleado, DomicilioEmpleado, ObraSocialEmpleado, SolicitudCambio

class FamiliarInline(admin.TabularInline):
    model = FamiliarEmpleado
    extra = 0

class ActividadInline(admin.TabularInline):
    model = ActividadEmpleado
    extra = 0
    readonly_fields = ['fecha']

class DomicilioInline(admin.StackedInline):
    model = DomicilioEmpleado
    extra = 0

class ObraSocialInline(admin.StackedInline):
    model = ObraSocialEmpleado
    extra = 0

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ['legajo', 'user', 'puesto', 'departamento', 'fecha_contrato', 'debe_cambiar_password']
    list_filter = ['departamento', 'tipo_contrato', 'fecha_contrato', 'debe_cambiar_password', 'es_rrhh']
    search_fields = ['legajo', 'user__first_name', 'user__last_name', 'user__email']
    inlines = [FamiliarInline, ActividadInline, DomicilioInline, ObraSocialInline]
    actions = ['marcar_cambio_password', 'desmarcar_cambio_password']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user', 'legajo', 'foto_perfil', 'es_rrhh')
        }),
        ('Datos Personales', {
            'fields': ('dni', 'cuil', 'fecha_nacimiento', 'telefono')
        }),
        ('Información Laboral', {
            'fields': ('puesto', 'departamento', 'supervisor', 'tipo_contrato', 'salario', 'fecha_contrato')
        }),
        ('Datos de Emergencia', {
            'fields': ('contacto_emergencia', 'telefono_emergencia', 'relacion_emergencia')
        }),
        ('Firma Digital', {
            'fields': ('firma_imagen', 'firma_pin')
        }),
        ('Seguridad', {
            'fields': ('debe_cambiar_password',),
            'description': 'Configuraciones de seguridad y acceso'
        }),
    )
    
    def marcar_cambio_password(self, request, queryset):
        """Acción para marcar empleados que deben cambiar contraseña"""
        updated = queryset.update(debe_cambiar_password=True)
        self.message_user(request, f'{updated} empleado(s) marcado(s) para cambio obligatorio de contraseña.')
    marcar_cambio_password.short_description = "Marcar para cambio obligatorio de contraseña"
    
    def desmarcar_cambio_password(self, request, queryset):
        """Acción para desmarcar empleados que ya no necesitan cambiar contraseña"""
        updated = queryset.update(debe_cambiar_password=False)
        self.message_user(request, f'{updated} empleado(s) desmarcado(s) del cambio obligatorio de contraseña.')
    desmarcar_cambio_password.short_description = "Desmarcar cambio obligatorio de contraseña"

@admin.register(FamiliarEmpleado)
class FamiliarEmpleadoAdmin(admin.ModelAdmin):
    list_display = ['apellido', 'nombre', 'empleado', 'parentesco', 'fecha_nacimiento']
    list_filter = ['parentesco']
    search_fields = ['apellido', 'nombre', 'empleado__user__first_name', 'empleado__user__last_name']

@admin.register(ActividadEmpleado)
class ActividadEmpleadoAdmin(admin.ModelAdmin):
    list_display = ['empleado', 'descripcion', 'fecha']
    list_filter = ['fecha']
    search_fields = ['empleado__user__first_name', 'empleado__user__last_name', 'descripcion']
    readonly_fields = ['fecha']


@admin.register(DomicilioEmpleado)
class DomicilioEmpleadoAdmin(admin.ModelAdmin):
    list_display = ['empleado', 'calle', 'numero', 'localidad', 'provincia']
    search_fields = ['empleado__user__first_name', 'empleado__user__last_name', 'calle', 'localidad']
    list_filter = ['provincia', 'localidad']


@admin.register(ObraSocialEmpleado)
class ObraSocialEmpleadoAdmin(admin.ModelAdmin):
    list_display = ['empleado', 'nombre', 'fecha_alta']
    search_fields = ['empleado__user__first_name', 'empleado__user__last_name', 'nombre']
    list_filter = ['nombre']


@admin.register(SolicitudCambio)
class SolicitudCambioAdmin(admin.ModelAdmin):
    list_display = ['empleado', 'tipo', 'estado', 'fecha_solicitud', 'fecha_resolucion', 'tiene_archivo_adjunto']
    list_filter = ['tipo', 'estado', 'fecha_solicitud']
    search_fields = ['empleado__user__first_name', 'empleado__user__last_name']
    readonly_fields = ['fecha_solicitud', 'datos_antiguos', 'datos_nuevos']
    
    fieldsets = (
        ('Información General', {
            'fields': ('empleado', 'tipo', 'estado', 'fecha_solicitud', 'fecha_resolucion')
        }),
        ('Declaración Jurada', {
            'fields': ('declaracion_jurada',)
        }),
        ('Archivos', {
            'fields': ('pdf_declaracion', 'archivo_adjunto'),
            'description': 'PDF firmado y archivo adjunto (si existe)'
        }),
        ('Datos', {
            'fields': ('datos_antiguos', 'datos_nuevos'),
            'classes': ('collapse',)
        }),
        ('Revisión de RRHH', {
            'fields': ('observaciones_rrhh', 'revisado_por')
        }),
    )
    
    def tiene_archivo_adjunto(self, obj):
        return "✅ Sí" if obj.archivo_adjunto else "❌ No"
    tiene_archivo_adjunto.short_description = "Archivo adjunto"
