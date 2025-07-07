#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_rrhh.settings')
django.setup()

from apps.empleados.models import SolicitudCambio

print("=== ANÁLISIS DE SOLICITUDES ===")

# Obtener todas las solicitudes
solicitudes = SolicitudCambio.objects.all().order_by('-fecha_solicitud')

print(f"Total de solicitudes: {solicitudes.count()}")
print()

for solicitud in solicitudes:
    print(f"ID: {solicitud.id}")
    print(f"Empleado: {solicitud.empleado.user.get_full_name()}")
    print(f"Tipo: '{solicitud.tipo}' -> {solicitud.get_tipo_display()}")
    print(f"Estado: '{solicitud.estado}' -> {solicitud.get_estado_display()}")
    print(f"Fecha: {solicitud.fecha_solicitud}")
    print(f"Datos nuevos: {solicitud.datos_nuevos}")
    print(f"Declaración jurada: {solicitud.declaracion_jurada[:100]}...")
    print("-" * 50)
    print()

# Verificar específicamente solicitudes de obra social
print("=== SOLICITUDES DE OBRA SOCIAL ===")
solicitudes_obra_social = SolicitudCambio.objects.filter(tipo='obra_social')
print(f"Solicitudes de obra social: {solicitudes_obra_social.count()}")

for solicitud in solicitudes_obra_social:
    print(f"ID: {solicitud.id}")
    print(f"Tipo: '{solicitud.tipo}'")
    print(f"Datos nuevos: {solicitud.datos_nuevos}")
    print()
