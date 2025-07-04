from django.db import models
from django.contrib.auth.models import User

class Notificacion(models.Model):
    TIPOS_NOTIFICACION = [
        ('INFO', 'Información'),
        ('AVISO', 'Aviso'),
        ('URGENTE', 'Urgente'),
        ('RECIBO', 'Recibo disponible'),
        ('DOCUMENTO', 'Documento'),
        ('SOLICITUD', 'Solicitud'),
    ]
    
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPOS_NOTIFICACION, default='INFO')
    destinatario = models.ForeignKey('empleados.Empleado', on_delete=models.CASCADE, related_name='notificaciones')
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_leida = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
    
    def __str__(self):
        return f"{self.titulo} - {self.destinatario.user.username}"
    
    def marcar_como_leida(self):
        """Marca la notificación como leída"""
        from django.utils import timezone
        self.leida = True
        self.fecha_leida = timezone.now()
        self.save()