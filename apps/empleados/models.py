from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Empleado(models.Model):
    TIPO_CONTRATO_CHOICES = [
        ('tiempo_completo', 'Tiempo completo'),
        ('tiempo_parcial', 'Tiempo parcial'),
        ('freelance', 'Freelance'),
    ]
    
    PARENTESCO_CHOICES = [
        ('esposo/a', 'Esposo/a'),
        ('hijo/a', 'Hijo/a'),
        ('padre/madre', 'Padre/Madre'),
        ('hermano/a', 'Hermano/a'),
        ('otro', 'Otro'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    es_rrhh = models.BooleanField(default=False, verbose_name="¿Es RRHH?", help_text="Marcar si este usuario pertenece al área de RRHH y debe acceder al panel de gestión RRHH.")
    legajo = models.CharField(max_length=20, unique=True)
    numero_legajo = models.IntegerField(null=True, blank=True, help_text="Número de legajo para facilitar búsquedas")
    dni = models.CharField(max_length=20)
    cuil = models.CharField(max_length=15, blank=True)  # Nuevo campo CUIL
    fecha_nacimiento = models.DateField(null=True, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    foto_perfil = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    
    # Información laboral
    puesto = models.CharField(max_length=100, blank=True)
    departamento = models.CharField(max_length=100, blank=True)
    supervisor = models.CharField(max_length=100, blank=True)
    tipo_contrato = models.CharField(max_length=20, choices=TIPO_CONTRATO_CHOICES, default='tiempo_completo')
    salario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fecha_contrato = models.DateField(null=True, blank=True)
    
    # Datos de emergencia
    contacto_emergencia = models.CharField(max_length=100, blank=True)
    telefono_emergencia = models.CharField(max_length=20, blank=True)
    relacion_emergencia = models.CharField(max_length=50, blank=True)
    
    # Firma digital
    firma_imagen = models.ImageField(upload_to='firmas/', blank=True, null=True)
    firma_pin = models.CharField(max_length=6, blank=True)
    
    # Control de contraseña
    debe_cambiar_password = models.BooleanField(default=False, verbose_name="Debe cambiar contraseña", 
                                               help_text="Marcar si el usuario debe cambiar su contraseña en el próximo login")
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.legajo}"
    
    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"

class FamiliarEmpleado(models.Model):
    PARENTESCO_CHOICES = [
        ('esposo/a', 'Esposo/a'),
        ('hijo/a', 'Hijo/a'),
        ('padre/madre', 'Padre/Madre'),
        ('hermano/a', 'Hermano/a'),
        ('otro', 'Otro'),
    ]
    
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='familiares')
    apellido = models.CharField(max_length=100)
    nombre = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    dni = models.CharField(max_length=20)
    parentesco = models.CharField(max_length=20, choices=PARENTESCO_CHOICES)
    
    def __str__(self):
        return f"{self.apellido}, {self.nombre} - {self.get_parentesco_display()}"
    
    class Meta:
        verbose_name = "Familiar"
        verbose_name_plural = "Familiares"

class ActividadEmpleado(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='actividades')
    descripcion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.empleado.user.get_full_name()} - {self.descripcion[:50]}"
    
    class Meta:
        verbose_name = "Actividad"
        verbose_name_plural = "Actividades"
        ordering = ['-fecha']


class DomicilioEmpleado(models.Model):
    empleado = models.OneToOneField(Empleado, on_delete=models.CASCADE, related_name='domicilio')
    calle = models.CharField(max_length=100, blank=True)
    numero = models.CharField(max_length=10, blank=True)
    piso = models.CharField(max_length=10, blank=True)
    depto = models.CharField(max_length=10, blank=True)
    barrio = models.CharField(max_length=100, blank=True)
    localidad = models.CharField(max_length=100, blank=True)
    provincia = models.CharField(max_length=100, blank=True)
    codigo_postal = models.CharField(max_length=10, blank=True)
    entre_calles = models.CharField(max_length=200, blank=True)
    observaciones = models.TextField(blank=True)
    
    def __str__(self):
        direccion_completa = f"{self.calle} {self.numero}"
        if self.piso:
            direccion_completa += f", Piso {self.piso}"
        if self.depto:
            direccion_completa += f", Depto {self.depto}"
        if self.localidad:
            direccion_completa += f", {self.localidad}"
        return direccion_completa or "Domicilio sin dirección"
    
    class Meta:
        verbose_name = "Domicilio"
        verbose_name_plural = "Domicilios"


class ObraSocialEmpleado(models.Model):
    empleado = models.OneToOneField(Empleado, on_delete=models.CASCADE, related_name='obra_social')
    nombre = models.CharField(max_length=100, blank=True)
    fecha_alta = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.nombre}" if self.nombre else "Obra social sin datos"
    
    class Meta:
        verbose_name = "Obra Social"
        verbose_name_plural = "Obras Sociales"


class SolicitudCambio(models.Model):
    TIPO_CHOICES = [
        ('domicilio', 'Cambio de Domicilio'),
        ('obra_social', 'Cambio de Obra Social'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_revision', 'En Revisión'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]
    
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='solicitudes_cambio')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    datos_antiguos = models.JSONField()  # Guardar los datos actuales antes del cambio
    datos_nuevos = models.JSONField()    # Los nuevos datos solicitados
    declaracion_jurada = models.TextField()  # Texto de la declaración jurada
    pdf_declaracion = models.FileField(upload_to='declaraciones_juradas/', blank=True, null=True)  # PDF firmado
    archivo_adjunto = models.FileField(upload_to='adjuntos_solicitudes/', blank=True, null=True)  # PDF adjunto opcional
    observaciones_rrhh = models.TextField(blank=True)  # Comentarios de RRHH
    revisado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes_revisadas')
    
    def __str__(self):
        return f"{self.empleado.user.get_full_name()} - {self.get_tipo_display()} - {self.get_estado_display()}"
    
    class Meta:
        verbose_name = "Solicitud de Cambio"
        verbose_name_plural = "Solicitudes de Cambio"
        ordering = ['-fecha_solicitud']
