from django.db import models
from django.contrib.auth.models import User

class NotificacionManager(models.Manager):
    """Manager personalizado para notificaciones"""
    
    def crear_notificacion(self, destinatario, titulo, mensaje, tipo='INFO'):
        """Función helper para crear notificaciones fácilmente"""
        return self.create(
            destinatario=destinatario,
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo
        )
    
    def crear_notificacion_inasistencia(self, empleado, inasistencia):
        """Crear notificación específica para nueva inasistencia"""
        titulo = "Nueva inasistencia registrada"
        mensaje = f"Se ha registrado una inasistencia del {inasistencia.fecha_desde.strftime('%d/%m/%Y')} al {inasistencia.fecha_hasta.strftime('%d/%m/%Y')}. Puedes justificarla subiendo la documentación correspondiente."
        
        return self.crear_notificacion(
            destinatario=empleado,
            titulo=titulo,
            mensaje=mensaje,
            tipo='AVISO'
        )
    
    def crear_notificacion_documento_revisado(self, empleado, documento, estado):
        """Crear notificación cuando RRHH revisa un documento"""
        estados_titulo = {
            'aprobado': 'Documento aprobado',
            'rechazado': 'Documento rechazado',
            'requiere_aclaracion': 'Documento requiere aclaración'
        }
        
        titulo = estados_titulo.get(estado, 'Documento revisado')
        
        if estado == 'aprobado':
            mensaje = f"Tu documento '{documento.titulo}' ha sido aprobado por RRHH."
        elif estado == 'rechazado':
            mensaje = f"Tu documento '{documento.titulo}' ha sido rechazado. Revisa las observaciones de RRHH."
        elif estado == 'requiere_aclaracion':
            mensaje = f"Tu documento '{documento.titulo}' requiere aclaraciones. Por favor, revísalo y actualízalo."
        else:
            mensaje = f"Tu documento '{documento.titulo}' ha sido revisado por RRHH."
        
        return self.crear_notificacion(
            destinatario=empleado,
            titulo=titulo,
            mensaje=mensaje,
            tipo='DOCUMENTO'
        )

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
    
    objects = NotificacionManager()
    
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