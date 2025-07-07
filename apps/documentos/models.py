from django.db import models
from apps.empleados.models import Empleado

class Documento(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]
    
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200)
    archivo = models.FileField(upload_to='documentos/')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_subida = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.nombre} - {self.empleado.user.get_full_name()}"
    
    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"