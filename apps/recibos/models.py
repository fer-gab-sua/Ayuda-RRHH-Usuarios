from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from apps.empleados.models import Empleado

class ReciboSueldo(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Firma'),
        ('observado', 'Observado por Empleado'),
        ('respondido', 'Observación Respondida por RRHH'),
        ('firmado', 'Firmado'),
        ('vencido', 'Vencido'),
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
    
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='recibos_sueldo')
    periodo = models.CharField(max_length=20, choices=PERIODO_CHOICES)
    anio = models.IntegerField()
    fecha_emision = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateTimeField()  # Fecha límite para firmar
    fecha_firma = models.DateTimeField(null=True, blank=True)
    
    # Archivos
    archivo_pdf = models.FileField(upload_to='recibos_sueldo/', help_text='PDF del recibo original')
    archivo_firmado = models.FileField(upload_to='recibos_firmados/', blank=True, null=True, help_text='PDF firmado digitalmente')
    
    # Estado y observaciones
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    observaciones_empleado = models.TextField(blank=True, help_text='Observaciones del empleado sobre el recibo')
    fecha_observacion = models.DateTimeField(null=True, blank=True, help_text='Fecha cuando el empleado hizo la observación')
    observaciones_rrhh = models.TextField(blank=True, help_text='Respuesta de RRHH a las observaciones')
    fecha_respuesta_rrhh = models.DateTimeField(null=True, blank=True, help_text='Fecha de respuesta de RRHH')
    respondido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='observaciones_respondidas')
    
    # Datos del recibo
    sueldo_bruto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    descuentos = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sueldo_neto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Metadatos
    subido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='recibos_subidos')
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Recibo de Sueldo"
        verbose_name_plural = "Recibos de Sueldo"
        ordering = ['-anio', '-periodo']
        unique_together = ['empleado', 'periodo', 'anio']
    
    def __str__(self):
        return f"{self.empleado.user.get_full_name()} - {self.get_periodo_display()} {self.anio}"
    
    @property
    def esta_vencido(self):
        """Verifica si el recibo está vencido para firmar"""
        return timezone.now() > self.fecha_vencimiento and self.estado == 'pendiente'
    
    @property
    def puede_ver(self):
        """Verifica si el empleado puede ver este recibo"""
        # Obtener el recibo anterior (cronológicamente)
        recibo_anterior = ReciboSueldo.objects.filter(
            empleado=self.empleado,
            anio__lt=self.anio
        ).first()
        
        if not recibo_anterior:
            # Si no hay recibo anterior, este mismo año buscar por período
            recibo_anterior = ReciboSueldo.objects.filter(
                empleado=self.empleado,
                anio=self.anio,
                periodo__lt=self.periodo
            ).order_by('-anio', '-periodo').first()
        
        # Si no hay recibo anterior, puede ver este
        if not recibo_anterior:
            return True
            
        # Solo puede ver si el anterior está firmado
        return recibo_anterior.estado == 'firmado'
    
    @property
    def puede_firmar(self):
        """Verifica si el recibo puede ser firmado"""
        if not self.puede_ver:
            return False
            
        if self.esta_vencido:
            return False
            
        # Solo puede firmar si está pendiente o si fue observado y RRHH ya respondió
        if self.estado == 'pendiente':
            return True
        elif self.estado == 'respondido':
            return True
            
        return False
    
    @property
    def puede_observar(self):
        """Verifica si el empleado puede hacer una observación"""
        if not self.puede_ver:
            return False
            
        # Solo puede observar si está pendiente o respondido (no si ya está observado esperando respuesta)
        return self.estado in ['pendiente', 'respondido']
    
    @property
    def tiene_observaciones_pendientes(self):
        """Verifica si tiene observaciones esperando respuesta de RRHH"""
        return self.estado == 'observado'
    
    def get_orden_periodo(self):
        """Obtiene el número de orden del período para comparaciones"""
        periodos_orden = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        return periodos_orden.get(self.periodo, 0)
    
    @property
    def nombre_archivo(self):
        """Nombre del archivo para descarga"""
        return f"recibo_{self.periodo}_{self.anio}_{self.empleado.legajo}.pdf"


class FirmaRecibo(models.Model):
    """Registro de firmas de recibos para auditoría"""
    recibo = models.OneToOneField(ReciboSueldo, on_delete=models.CASCADE, related_name='firma_auditoria')
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha_firma = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    tipo_firma = models.CharField(max_length=20, choices=[
        ('conforme', 'Conforme'),
        ('observado', 'Con Observaciones Previas'),
    ])
    observaciones = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Firma de Recibo"
        verbose_name_plural = "Firmas de Recibos"
        ordering = ['-fecha_firma']
    
    def __str__(self):
        return f"Firma de {self.empleado.user.get_full_name()} - {self.recibo}"
