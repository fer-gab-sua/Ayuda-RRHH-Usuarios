from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User

from .models import TipoDocumento, Documento, Inasistencia, HistorialDocumento


@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre', 'descripcion']
    list_editable = ['activo']
    ordering = ['nombre']

    fieldsets = (
        (None, {
            'fields': ('nombre', 'descripcion', 'activo')
        }),
    )


class HistorialDocumentoInline(admin.TabularInline):
    model = HistorialDocumento
    extra = 0
    readonly_fields = ['fecha', 'usuario']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = [
        'titulo', 'empleado_info', 'tipo_documento', 'estado_display', 
        'fecha_subida', 'fecha_revision', 'revisado_por'
    ]
    list_filter = [
        'estado', 'tipo_documento', 'fecha_subida', 'fecha_revision'
    ]
    search_fields = [
        'titulo', 'empleado__user__first_name', 'empleado__user__last_name', 
        'empleado__legajo', 'descripcion'
    ]
    readonly_fields = [
        'empleado', 'fecha_subida', 'nombre_archivo_display', 'puede_editar'
    ]
    
    fieldsets = (
        ('Información del Documento', {
            'fields': ('titulo', 'tipo_documento', 'descripcion', 'empleado')
        }),
        ('Archivo', {
            'fields': ('archivo', 'nombre_archivo_display')
        }),
        ('Fechas del Documento', {
            'fields': ('fecha_desde', 'fecha_hasta'),
            'description': 'Período que cubre el documento (opcional)'
        }),
        ('Estado y Revisión', {
            'fields': ('estado', 'observaciones_rrhh', 'revisado_por', 'fecha_revision')
        }),
        ('Relaciones', {
            'fields': ('inasistencia',),
            'classes': ('collapse',)
        }),
        ('Información del Sistema', {
            'fields': ('fecha_subida', 'puede_editar'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [HistorialDocumentoInline]
    
    actions = ['aprobar_documentos', 'rechazar_documentos', 'solicitar_aclaracion']

    def empleado_info(self, obj):
        if obj.empleado:
            return format_html(
                '<strong>{}</strong><br><small>Legajo: {}</small>',
                obj.empleado.user.get_full_name() or obj.empleado.user.username,
                obj.empleado.legajo or 'N/A'
            )
        return 'Sin empleado'
    empleado_info.short_description = 'Empleado'

    def estado_display(self, obj):
        colors = {
            'pendiente': '#fbbf24',
            'aprobado': '#10b981', 
            'rechazado': '#ef4444',
            'requiere_aclaracion': '#3b82f6'
        }
        icons = {
            'pendiente': 'clock',
            'aprobado': 'check',
            'rechazado': 'times',
            'requiere_aclaracion': 'question'
        }
        
        color = colors.get(obj.estado, '#6b7280')
        icon = icons.get(obj.estado, 'circle')
        
        return format_html(
            '<span style="color: {}"><i class="fas fa-{}"></i> {}</span>',
            color, icon, obj.get_estado_display()
        )
    estado_display.short_description = 'Estado'

    def nombre_archivo_display(self, obj):
        if obj.archivo:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                obj.archivo.url, obj.nombre_archivo
            )
        return 'Sin archivo'
    nombre_archivo_display.short_description = 'Archivo'

    def save_model(self, request, obj, form, change):
        # Si se está cambiando el estado y hay un usuario logueado
        if change and 'estado' in form.changed_data:
            obj.revisado_por = request.user
            obj.fecha_revision = timezone.now()
        
        super().save_model(request, obj, form, change)
        
        # Crear registro en el historial
        if change and ('estado' in form.changed_data or 'observaciones_rrhh' in form.changed_data):
            HistorialDocumento.objects.create(
                documento=obj,
                usuario=request.user,
                estado_anterior=form.initial.get('estado', ''),
                estado_nuevo=obj.estado,
                observaciones=obj.observaciones_rrhh
            )

    def aprobar_documentos(self, request, queryset):
        updated = 0
        for documento in queryset:
            if documento.estado in ['pendiente', 'requiere_aclaracion']:
                documento.estado = 'aprobado'
                documento.revisado_por = request.user
                documento.fecha_revision = timezone.now()
                documento.save()
                
                # Crear historial
                HistorialDocumento.objects.create(
                    documento=documento,
                    usuario=request.user,
                    estado_anterior=documento.estado,
                    estado_nuevo='aprobado',
                    observaciones='Aprobado masivamente desde el admin'
                )
                updated += 1
        
        self.message_user(request, f'{updated} documentos aprobados exitosamente.')
    aprobar_documentos.short_description = 'Aprobar documentos seleccionados'

    def rechazar_documentos(self, request, queryset):
        updated = 0
        for documento in queryset:
            if documento.estado in ['pendiente', 'requiere_aclaracion']:
                documento.estado = 'rechazado'
                documento.revisado_por = request.user
                documento.fecha_revision = timezone.now()
                documento.save()
                
                # Crear historial
                HistorialDocumento.objects.create(
                    documento=documento,
                    usuario=request.user,
                    estado_anterior=documento.estado,
                    estado_nuevo='rechazado',
                    observaciones='Rechazado masivamente desde el admin'
                )
                updated += 1
        
        self.message_user(request, f'{updated} documentos rechazados.')
    rechazar_documentos.short_description = 'Rechazar documentos seleccionados'

    def solicitar_aclaracion(self, request, queryset):
        updated = 0
        for documento in queryset:
            if documento.estado in ['pendiente']:
                documento.estado = 'requiere_aclaracion'
                documento.revisado_por = request.user
                documento.fecha_revision = timezone.now()
                documento.save()
                
                # Crear historial
                HistorialDocumento.objects.create(
                    documento=documento,
                    usuario=request.user,
                    estado_anterior=documento.estado,
                    estado_nuevo='requiere_aclaracion',
                    observaciones='Solicitud de aclaración desde el admin'
                )
                updated += 1
        
        self.message_user(request, f'{updated} documentos marcados como "requiere aclaración".')
    solicitar_aclaracion.short_description = 'Solicitar aclaración para documentos seleccionados'


@admin.register(Inasistencia)
class InasistenciaAdmin(admin.ModelAdmin):
    list_display = [
        'empleado_info', 'fecha_desde', 'fecha_hasta', 'tipo', 
        'estado_display', 'documentos_count', 'fecha_creacion'
    ]
    list_filter = ['estado', 'tipo', 'fecha_desde', 'fecha_creacion']
    search_fields = [
        'empleado__user__first_name', 'empleado__user__last_name', 
        'empleado__legajo', 'motivo'
    ]
    date_hierarchy = 'fecha_desde'
    
    fieldsets = (
        ('Información del Empleado', {
            'fields': ('empleado',)
        }),
        ('Fechas de Inasistencia', {
            'fields': ('fecha_desde', 'fecha_hasta')
        }),
        ('Detalles', {
            'fields': ('tipo', 'motivo', 'observaciones_rrhh')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Información del Sistema', {
            'fields': ('creado_por', 'fecha_creacion'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['creado_por', 'fecha_creacion']
    
    actions = ['marcar_como_justificada', 'marcar_como_injustificada']

    def empleado_info(self, obj):
        if obj.empleado:
            return format_html(
                '<strong>{}</strong><br><small>Legajo: {}</small>',
                obj.empleado.user.get_full_name() or obj.empleado.user.username,
                obj.empleado.legajo or 'N/A'
            )
        return 'Sin empleado'
    empleado_info.short_description = 'Empleado'

    def estado_display(self, obj):
        colors = {
            'pendiente': '#fbbf24',
            'justificada': '#10b981',
            'injustificada': '#ef4444'
        }
        icons = {
            'pendiente': 'clock',
            'justificada': 'check',
            'injustificada': 'times'
        }
        
        color = colors.get(obj.estado, '#6b7280')
        icon = icons.get(obj.estado, 'circle')
        
        return format_html(
            '<span style="color: {}"><i class="fas fa-{}"></i> {}</span>',
            color, icon, obj.get_estado_display()
        )
    estado_display.short_description = 'Estado'

    def documentos_count(self, obj):
        count = obj.documentos.count()
        if count > 0:
            admin_url = reverse('admin:documentos_documento_changelist')
            return format_html(
                '<a href="{}?inasistencia={}">{} documentos</a>',
                admin_url, obj.id, count
            )
        return 'Sin documentos'
    documentos_count.short_description = 'Documentos Justificativos'

    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)

    def marcar_como_justificada(self, request, queryset):
        updated = queryset.update(estado='justificada')
        self.message_user(request, f'{updated} inasistencias marcadas como justificadas.')
    marcar_como_justificada.short_description = 'Marcar como justificada'

    def marcar_como_injustificada(self, request, queryset):
        updated = queryset.update(estado='injustificada')
        self.message_user(request, f'{updated} inasistencias marcadas como injustificadas.')
    marcar_como_injustificada.short_description = 'Marcar como injustificada'


@admin.register(HistorialDocumento)
class HistorialDocumentoAdmin(admin.ModelAdmin):
    list_display = ['documento', 'usuario', 'fecha']
    list_filter = ['fecha']
    search_fields = ['documento__titulo', 'usuario__username']
    readonly_fields = ['documento', 'usuario', 'fecha']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


# Personalización del admin
admin.site.site_header = 'Portal RRHH - Administración'
admin.site.site_title = 'Portal RRHH'
admin.site.index_title = 'Panel de Administración'
