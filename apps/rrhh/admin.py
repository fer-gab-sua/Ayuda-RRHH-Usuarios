from django.contrib import admin
from .models import CargaMasivaRecibos, LogProcesamientoRecibo

@admin.register(CargaMasivaRecibos)
class CargaMasivaRecibosAdmin(admin.ModelAdmin):
    list_display = ['periodo', 'anio', 'estado', 'fecha_carga', 'usuario_carga', 'total_empleados', 'recibos_generados']
    list_filter = ['estado', 'periodo', 'anio', 'fecha_carga']
    search_fields = ['periodo', 'anio', 'usuario_carga__username']
    readonly_fields = ['fecha_carga', 'fecha_procesamiento', 'total_empleados', 'recibos_generados']
    ordering = ['-fecha_carga']

@admin.register(LogProcesamientoRecibo)
class LogProcesamientoReciboAdmin(admin.ModelAdmin):
    list_display = ['legajo_empleado', 'nombre_empleado', 'estado', 'fecha_procesamiento', 'carga_masiva']
    list_filter = ['estado', 'fecha_procesamiento', 'carga_masiva__periodo']
    search_fields = ['legajo_empleado', 'nombre_empleado']
    readonly_fields = ['fecha_procesamiento']
    ordering = ['-fecha_procesamiento']
