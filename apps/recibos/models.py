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
        ('no_encontrado', 'Recibo No Encontrado'),
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
    
    TIPO_RECIBO_CHOICES = [
        ('sueldo', 'Sueldo'),
        ('sac_1', 'SAC 1'),
        ('sac_2', 'SAC 2'),
    ]
    
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='recibos_sueldo')
    periodo = models.CharField(max_length=20, choices=PERIODO_CHOICES)
    anio = models.IntegerField()
    tipo_recibo = models.CharField(max_length=10, choices=TIPO_RECIBO_CHOICES, default='sueldo')
    fecha_emision = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateTimeField()  # Fecha límite para firmar
    fecha_firma = models.DateTimeField(null=True, blank=True)
    
    # Archivos
    archivo_pdf = models.FileField(upload_to='recibos_sueldo/', help_text='PDF del recibo original para firmar')
    archivo_pdf_centromedica = models.FileField(upload_to='recibos_centromedica/', blank=True, null=True, help_text='PDF firmado por Centromédica que el empleado visualiza')
    archivo_firmado = models.FileField(upload_to='recibos_firmados/', blank=True, null=True, help_text='PDF firmado digitalmente por el empleado')
    
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
        ordering = ['anio', 'periodo']  # Orden cronológico correcto
        unique_together = ['empleado', 'periodo', 'anio', 'tipo_recibo']
    
    def __str__(self):
        return f"{self.empleado.user.get_full_name()} - {self.get_tipo_recibo_display()} {self.get_periodo_display()} {self.anio}"
    
    @property
    def esta_vencido(self):
        """Verifica si el recibo está vencido para firmar"""
        # Solo está vencido si es pendiente y pasó la fecha de vencimiento
        if self.estado != 'pendiente':
            return False
        return timezone.now() > self.fecha_vencimiento
    
    @property
    def puede_ver(self):
        """Verifica si el empleado puede ver este recibo"""
        # Verificar si la carga masiva está visible para empleados
        if self.subido_por:
            from apps.rrhh.models import CargaMasivaRecibos
            carga_masiva = CargaMasivaRecibos.objects.filter(
                periodo=self.periodo,
                anio=self.anio,
                usuario_carga=self.subido_por
            ).first()
            
            if carga_masiva and not carga_masiva.visible_empleados:
                return False
        
        # Los recibos no encontrados no son visibles hasta que RRHH los revise y corrija
        if self.estado == 'no_encontrado':
            return False
        
        # Obtener todos los recibos del empleado y ordenarlos cronológicamente
        recibos_ordenados = ReciboSueldo.objects.filter(
            empleado=self.empleado
        ).extra(
            select={'orden': 'anio * 100 + CASE '
                           'WHEN periodo = "enero" THEN 1 '
                           'WHEN periodo = "febrero" THEN 2 '
                           'WHEN periodo = "marzo" THEN 3 '
                           'WHEN periodo = "abril" THEN 4 '
                           'WHEN periodo = "mayo" THEN 5 '
                           'WHEN periodo = "junio" THEN 6 '
                           'WHEN periodo = "julio" THEN 7 '
                           'WHEN periodo = "agosto" THEN 8 '
                           'WHEN periodo = "septiembre" THEN 9 '
                           'WHEN periodo = "octubre" THEN 10 '
                           'WHEN periodo = "noviembre" THEN 11 '
                           'WHEN periodo = "diciembre" THEN 12 '
                           'ELSE 0 END'}
        ).order_by('orden')
        
        # Convertir a lista para poder iterar
        recibos_list = list(recibos_ordenados)
        
        try:
            # Encontrar la posición del recibo actual
            posicion_actual = recibos_list.index(self)
            
            # Si es el primer recibo, puede verlo
            if posicion_actual == 0:
                return True
                
            # Si hay un recibo anterior, verificar que esté firmado
            recibo_anterior = recibos_list[posicion_actual - 1]
            return recibo_anterior.estado == 'firmado'
            
        except ValueError:
            # Si no se encuentra el recibo en la lista, puede verlo (caso excepcional)
            return True
    
    @property
    def puede_firmar(self):
        """Verifica si el recibo puede ser firmado"""
        # Primero debe poder verlo
        if not self.puede_ver:
            return False
            
        # No puede firmar si está vencido
        if self.esta_vencido:
            return False
            
        # No puede firmar si ya está firmado
        if self.estado == 'firmado':
            return False
            
        # Verificar que no tenga observaciones pendientes en otros recibos
        if self.empleado.recibos_sueldo.filter(estado='observado').exists():
            return False
            
        # Solo puede firmar si está pendiente o si fue observado y RRHH ya respondió
        return self.estado in ['pendiente', 'respondido']
    
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
    
    def empleado_tiene_observaciones_pendientes(self):
        """Verifica si el empleado tiene observaciones pendientes en cualquier recibo"""
        return self.empleado.recibos_sueldo.filter(estado='observado').exists()
    
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
        tipo_archivo = self.tipo_recibo.replace('_', '')  # sac1, sac2, sueldo
        return f"recibo_{tipo_archivo}_{self.periodo}_{self.anio}_{self.empleado.legajo}.pdf"


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
