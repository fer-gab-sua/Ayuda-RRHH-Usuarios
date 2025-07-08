from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class CargaMasivaRecibos(models.Model):
    """Modelo para gestionar la carga masiva de recibos"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Procesamiento'),
        ('procesando', 'Procesando'),
        ('completado', 'Completado'),
        ('error', 'Error en el Procesamiento'),
    ]
    
    PERIODO_CHOICES = [
        ('enero', 'Enero'),
        ('febrero', 'Febrero'),
        ('marzo', 'Marzo'),
        ('abril', 'Abril'),
        ('mayo', 'Mayo'),
        ('junio', 'Junio'),
        ('julio', 'Julio'),
        ('agosto', 'Agosto'),
        ('septiembre', 'Septiembre'),
        ('octubre', 'Octubre'),
        ('noviembre', 'Noviembre'),
        ('diciembre', 'Diciembre'),
    ]
    
    # Información del período
    periodo = models.CharField(max_length=20, choices=PERIODO_CHOICES)
    anio = models.IntegerField()
    
    # Archivo y procesamiento
    archivo_pdf = models.FileField(upload_to='recibos_masivos/', help_text='PDF con todos los recibos del período')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_carga = models.DateTimeField(auto_now_add=True)
    fecha_procesamiento = models.DateTimeField(null=True, blank=True)
    
    # Usuario que hizo la carga
    usuario_carga = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cargas_recibos')
    
    # Resultados del procesamiento
    total_empleados = models.IntegerField(default=0, help_text='Total de empleados en el sistema')
    recibos_generados = models.IntegerField(default=0, help_text='Recibos generados exitosamente')
    errores_procesamiento = models.TextField(blank=True, help_text='Errores durante el procesamiento')
    
    # Configuración de vencimiento
    dias_vencimiento = models.IntegerField(default=30, help_text='Días para vencimiento desde la fecha de carga')
    
    # Validación y visibilidad
    validado = models.BooleanField(default=False, help_text='Si la carga fue validada por RRHH')
    fecha_validacion = models.DateTimeField(null=True, blank=True, help_text='Fecha cuando fue validada la carga')
    validado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cargas_validadas', help_text='Usuario que validó la carga')
    visible_empleados = models.BooleanField(default=False, help_text='Si los recibos son visibles para los empleados')
    
    class Meta:
        verbose_name = "Carga Masiva de Recibos"
        verbose_name_plural = "Cargas Masivas de Recibos"
        unique_together = ['periodo', 'anio']
        ordering = ['-fecha_carga']
    
    def __str__(self):
        return f"Recibos {self.get_periodo_display()} {self.anio} - {self.get_estado_display()}"
    
    @property
    def fecha_vencimiento_calculada(self):
        """Calcula la fecha de vencimiento para los recibos"""
        from datetime import timedelta
        return self.fecha_carga + timedelta(days=self.dias_vencimiento)
    
    @property
    def puede_validar(self):
        """Verifica si la carga puede ser validada"""
        return self.estado == 'completado' and not self.validado
    
    @property
    def puede_hacer_visible(self):
        """Verifica si los recibos pueden hacerse visibles"""
        return self.validado and not self.visible_empleados
    
    @property
    def puede_eliminar(self):
        """Verifica si la carga puede ser eliminada"""
        return not self.validado
    
    def get_recibos_generados(self):
        """Obtiene los recibos generados por esta carga"""
        from apps.recibos.models import ReciboSueldo
        return ReciboSueldo.objects.filter(
            periodo=self.periodo,
            anio=self.anio,
            subido_por=self.usuario_carga
        )


class LogProcesamientoRecibo(models.Model):
    """Log detallado del procesamiento de cada recibo individual"""
    carga_masiva = models.ForeignKey(CargaMasivaRecibos, on_delete=models.CASCADE, related_name='logs_procesamiento')
    legajo_empleado = models.CharField(max_length=20)
    nombre_empleado = models.CharField(max_length=200)
    estado = models.CharField(max_length=25, choices=[
        ('exitoso', 'Procesado Exitosamente'),
        ('error', 'Error en Procesamiento'),
        ('empleado_no_encontrado', 'Empleado No Encontrado'),
        ('datos_invalidos', 'Datos Inválidos'),
        ('no_encontrado', 'Recibo No Encontrado en PDF'),
    ])
    mensaje = models.TextField(help_text='Mensaje detallado del procesamiento')
    fecha_procesamiento = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Log de Procesamiento"
        verbose_name_plural = "Logs de Procesamiento"
        ordering = ['-fecha_procesamiento']
    
    def __str__(self):
        return f"{self.legajo_empleado} - {self.get_estado_display()}"
