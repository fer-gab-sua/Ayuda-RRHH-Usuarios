from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Empleado(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dni = models.CharField(max_length=20, unique=True)
    fecha_nacimiento = models.DateField()
    telefono = models.CharField(max_length=20)
    direccion = models.TextField()
    ciudad = models.CharField(max_length=100)
    codigo_postal = models.CharField(max_length=10)
    telefono_emergencia = models.CharField(max_length=20)
    contacto_emergencia = models.CharField(max_length=100)
    foto_perfil = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    
    # Datos laborales
    fecha_ingreso = models.DateField()
    puesto = models.CharField(max_length=100)
    departamento = models.CharField(max_length=100)
    salario = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class ReciboSueldo(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente de Firma'),
        ('firmado', 'Firmado'),
        ('disconformidad', 'Firmado en Disconformidad'),
    ]
    
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha = models.DateField()
    periodo = models.CharField(max_length=20)  # Ej: "Mayo 2024"
    archivo = models.FileField(upload_to='recibos/')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    observaciones = models.TextField(blank=True)
    fecha_firma = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-fecha']
    
    def __str__(self):
        return f"Recibo {self.periodo} - {self.empleado}"


class TipoSolicitud(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre


class Solicitud(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]
    
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    tipo = models.ForeignKey(TipoSolicitud, on_delete=models.CASCADE)
    fecha_desde = models.DateField()
    fecha_hasta = models.DateField(blank=True, null=True)
    motivo = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha_solicitud = models.DateTimeField(default=timezone.now)
    fecha_respuesta = models.DateTimeField(blank=True, null=True)
    observaciones_respuesta = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-fecha_solicitud']
    
    def __str__(self):
        return f"{self.tipo.nombre} - {self.empleado} ({self.fecha_desde})"


class Documento(models.Model):
    TIPOS = [
        ('personal', 'Documento Personal'),
        ('laboral', 'Documento Laboral'),
        ('certificado', 'Certificado'),
    ]
    
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    archivo = models.FileField(upload_to='documentos/')
    fecha_subida = models.DateTimeField(default=timezone.now)
    descripcion = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-fecha_subida']
    
    def __str__(self):
        return f"{self.nombre} - {self.empleado}"


class Notificacion(models.Model):
    TIPOS = [
        ('info', 'Información'),
        ('alerta', 'Alerta'),
        ('recordatorio', 'Recordatorio'),
    ]
    
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPOS, default='info')
    importante = models.BooleanField(default=False)
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.titulo} - {self.empleado}"
