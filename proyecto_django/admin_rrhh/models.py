from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from rrhh.models import Empleado


class PerfilRRHH(models.Model):
    """Modelo para identificar usuarios de RRHH"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    departamento = models.CharField(max_length=100, default='Recursos Humanos')
    puede_aprobar_solicitudes = models.BooleanField(default=True)
    puede_subir_recibos = models.BooleanField(default=True)
    puede_gestionar_empleados = models.BooleanField(default=True)
    
    def __str__(self):
        return f"RRHH - {self.user.get_full_name()}"


class AprobacionSolicitud(models.Model):
    """Historial de aprobaciones de solicitudes"""
    solicitud = models.ForeignKey('rrhh.Solicitud', on_delete=models.CASCADE)
    aprobador = models.ForeignKey(PerfilRRHH, on_delete=models.CASCADE)
    fecha_aprobacion = models.DateTimeField(default=timezone.now)
    comentarios = models.TextField(blank=True)
    
    def __str__(self):
        return f"Aprobación de {self.solicitud} por {self.aprobador}"


class LogActividad(models.Model):
    """Log de actividades administrativas"""
    TIPOS_ACTIVIDAD = [
        ('recibo_subido', 'Recibo Subido'),
        ('solicitud_aprobada', 'Solicitud Aprobada'),
        ('solicitud_rechazada', 'Solicitud Rechazada'),
        ('empleado_creado', 'Empleado Creado'),
        ('empleado_editado', 'Empleado Editado'),
        ('notificacion_enviada', 'Notificación Enviada'),
        ('documento_subido', 'Documento Subido'),
    ]
    
    usuario_rrhh = models.ForeignKey(PerfilRRHH, on_delete=models.CASCADE)
    tipo_actividad = models.CharField(max_length=30, choices=TIPOS_ACTIVIDAD)
    descripcion = models.TextField()
    fecha = models.DateTimeField(default=timezone.now)
    empleado_afectado = models.ForeignKey(Empleado, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.get_tipo_actividad_display()} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"
