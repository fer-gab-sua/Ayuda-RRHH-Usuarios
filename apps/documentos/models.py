from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from apps.empleados.models import Empleado


class TipoDocumento(models.Model):
    """Tipos de documentos que se pueden subir"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documentos"
        ordering = ['nombre']


class Inasistencia(models.Model):
    """Registro de inasistencias de empleados"""
    TIPO_CHOICES = [
        ('enfermedad', 'Enfermedad'),
        ('personal', 'Motivos Personales'),
        ('familiar', 'Familiar'),
        ('estudio', 'Estudio'),
        ('otro', 'Otro'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente Justificación'),
        ('justificada', 'Justificada'),
        ('injustificada', 'Injustificada'),
    ]
    
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='inasistencias')
    fecha_desde = models.DateField()
    fecha_hasta = models.DateField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    motivo = models.TextField(blank=True, help_text="Descripción del motivo de la inasistencia")
    observaciones_rrhh = models.TextField(blank=True, help_text="Observaciones del área de RRHH")
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='inasistencias_creadas')
    fecha_modificacion = models.DateTimeField(auto_now=True)
    modificado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='inasistencias_modificadas')
    
    @property
    def dias_inasistencia(self):
        """Calcular días de inasistencia"""
        delta = self.fecha_hasta - self.fecha_desde
        return delta.days + 1
    
    @property
    def puede_ser_justificada(self):
        """Verificar si la inasistencia puede ser justificada con documentos"""
        return self.estado == 'pendiente'
    
    def __str__(self):
        return f"{self.empleado.user.get_full_name()} - {self.fecha_desde} al {self.fecha_hasta} ({self.get_tipo_display()})"
    
    class Meta:
        verbose_name = "Inasistencia"
        verbose_name_plural = "Inasistencias"
        ordering = ['-fecha_desde']


class Documento(models.Model):
    """Documentos subidos por empleados"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Revisión'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('requiere_aclaracion', 'Requiere Aclaración'),
    ]
    
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='documentos')
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.CASCADE)
    inasistencia = models.ForeignKey(Inasistencia, on_delete=models.CASCADE, null=True, blank=True, 
                                   help_text="Inasistencia que justifica este documento (opcional)")
    
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    archivo = models.FileField(upload_to='documentos/%Y/%m/')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    
    # Fechas relacionadas al documento (ej: período que cubre el certificado médico)
    fecha_desde = models.DateField(null=True, blank=True, help_text="Fecha desde la cual es válido el documento")
    fecha_hasta = models.DateField(null=True, blank=True, help_text="Fecha hasta la cual es válido el documento")
    
    # Feedback de RRHH
    observaciones_rrhh = models.TextField(blank=True, help_text="Observaciones del área de RRHH")
    revisado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='documentos_revisados')
    fecha_revision = models.DateTimeField(null=True, blank=True)
    
    # Auditoría
    fecha_subida = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    @property
    def nombre_archivo(self):
        """Obtener solo el nombre del archivo sin la ruta"""
        if self.archivo:
            return self.archivo.name.split('/')[-1]
        return ""
    
    @property
    def puede_editar(self):
        """Verificar si el documento puede ser editado"""
        return self.estado in ['pendiente', 'requiere_aclaracion']
    
    @property
    def justifica_inasistencia(self):
        """Verificar si este documento justifica una inasistencia"""
        return self.inasistencia is not None
    
    def __str__(self):
        return f"{self.titulo} - {self.empleado.user.get_full_name()} ({self.get_estado_display()})"
    
    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ['-fecha_subida']


class HistorialDocumento(models.Model):
    """Historial de cambios en documentos"""
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='historial')
    estado_anterior = models.CharField(max_length=20)
    estado_nuevo = models.CharField(max_length=20)
    observaciones = models.TextField(blank=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.documento.titulo} - {self.estado_anterior} → {self.estado_nuevo}"
    
    class Meta:
        verbose_name = "Historial de Documento"
        verbose_name_plural = "Historial de Documentos"
        ordering = ['-fecha']