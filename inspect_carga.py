#!/usr/bin/env python
"""
Script para inspeccionar la carga masiva existente y luego crear una nueva para probar la lógica corregida.
"""

import os
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_rrhh.settings')
django.setup()

from apps.empleados.models import Empleado
from apps.rrhh.models import CargaMasivaRecibos, LogProcesamientoRecibo
from apps.recibos.models import ReciboSueldo
from django.contrib.auth.models import User

def inspect_current_carga():
    """Inspeccionar la carga actual y sus errores"""
    
    print("=== INSPECCIÓN DE CARGA ACTUAL ===\n")
    
    # Obtener la carga existente
    carga = CargaMasivaRecibos.objects.first()
    if not carga:
        print("No hay cargas masivas")
        return
    
    print(f"Carga: {carga.periodo} {carga.anio}")
    print(f"Estado: {carga.estado}")
    print(f"Errores de procesamiento:")
    print(carga.errores_procesamiento)
    print("\n" + "="*50 + "\n")
    
    # Mostrar todos los logs
    logs = LogProcesamientoRecibo.objects.filter(carga_masiva=carga)
    print(f"LOGS DE PROCESAMIENTO ({logs.count()}):")
    
    for log in logs:
        print(f"  Legajo: {log.legajo_empleado}")
        print(f"  Empleado: {log.nombre_empleado}")
        print(f"  Estado: {log.estado}")
        print(f"  Mensaje: {log.mensaje}")
        print("  " + "-"*40)
    
    print(f"\n=== ANÁLISIS ===")
    
    # Verificar recibos creados
    recibos = ReciboSueldo.objects.filter(
        periodo=carga.periodo,
        anio=carga.anio
    )
    
    print(f"Recibos creados: {recibos.count()}")
    for recibo in recibos:
        print(f"  - {recibo.empleado.legajo} ({recibo.empleado.user.get_full_name()}) - Estado: {recibo.estado}")
    
    # Empleados sin recibo
    empleados_con_recibo = recibos.values_list('empleado_id', flat=True)
    empleados_sin_recibo = Empleado.objects.exclude(id__in=empleados_con_recibo)
    
    print(f"\nEmpleados sin recibo: {empleados_sin_recibo.count()}")
    for emp in empleados_sin_recibo:
        print(f"  - {emp.legajo} ({emp.user.get_full_name()})")

def clean_current_carga():
    """Limpiar la carga actual para hacer pruebas limpias"""
    
    print("\n=== LIMPIANDO CARGA ACTUAL ===\n")
    
    # Obtener la carga existente
    carga = CargaMasivaRecibos.objects.first()
    if not carga:
        print("No hay cargas masivas para limpiar")
        return
    
    # Eliminar recibos
    recibos = ReciboSueldo.objects.filter(
        periodo=carga.periodo,
        anio=carga.anio
    )
    recibos_count = recibos.count()
    recibos.delete()
    print(f"Eliminados {recibos_count} recibos")
    
    # Eliminar logs
    logs = LogProcesamientoRecibo.objects.filter(carga_masiva=carga)
    logs_count = logs.count()
    logs.delete()
    print(f"Eliminados {logs_count} logs")
    
    # Eliminar carga
    carga.delete()
    print(f"Eliminada carga masiva")
    
    print("Limpieza completada ✓")

if __name__ == "__main__":
    inspect_current_carga()
    
    # Preguntar si quiere limpiar
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'clean':
        clean_current_carga()
    else:
        print("\nPara limpiar la carga actual, ejecuta:")
        print("python test_matching_logic.py clean")
