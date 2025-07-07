#!/usr/bin/env python
"""
Script para verificar las solicitudes de cambio de domicilio en la base de datos
"""

import os
import sys
import django

# Configurar Django
sys.path.append('d:\\Repositorys\\Ayuda-RRHH-Usuarios')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_rrhh.settings')
django.setup()

from apps.empleados.models import SolicitudCambio, Empleado

def verificar_solicitudes():
    print("=== VERIFICACIÓN DE SOLICITUDES DE CAMBIO ===")
    
    # Contar solicitudes
    total_solicitudes = SolicitudCambio.objects.count()
    solicitudes_domicilio = SolicitudCambio.objects.filter(tipo='domicilio').count()
    solicitudes_pendientes = SolicitudCambio.objects.filter(estado='pendiente').count()
    
    print(f"Total de solicitudes: {total_solicitudes}")
    print(f"Solicitudes de domicilio: {solicitudes_domicilio}")
    print(f"Solicitudes pendientes: {solicitudes_pendientes}")
    
    # Listar solicitudes de domicilio
    print("\n=== SOLICITUDES DE DOMICILIO ===")
    for solicitud in SolicitudCambio.objects.filter(tipo='domicilio').order_by('-fecha_solicitud'):
        print(f"ID: {solicitud.id}")
        print(f"Empleado: {solicitud.empleado.user.get_full_name()}")
        print(f"Estado: {solicitud.estado}")
        print(f"Fecha: {solicitud.fecha_solicitud}")
        print(f"Datos antiguos: {solicitud.datos_antiguos}")
        print(f"Datos nuevos: {solicitud.datos_nuevos}")
        print(f"Tiene PDF: {'Sí' if solicitud.pdf_declaracion else 'No'}")
        print("-" * 50)
    
    # Verificar empleados con domicilio
    print("\n=== EMPLEADOS CON DOMICILIO ===")
    empleados_con_domicilio = Empleado.objects.filter(domicilio__isnull=False)
    print(f"Empleados con domicilio registrado: {empleados_con_domicilio.count()}")
    
    for empleado in empleados_con_domicilio:
        print(f"{empleado.user.get_full_name()}: {empleado.domicilio}")

if __name__ == "__main__":
    verificar_solicitudes()
