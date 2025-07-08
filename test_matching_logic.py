#!/usr/bin/env python
"""
Script para probar la nueva lógica de matching de recibos.
Este script simula el proceso de carga masiva y verificar que:
1. Solo se crean recibos para empleados que se encuentran en el PDF
2. No se crean recibos para empleados que no se encuentran
3. Los logs reflejan correctamente los resultados
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

def test_matching_logic():
    """Función para probar la lógica de matching"""
    
    print("=== TEST: Lógica de Matching de Recibos ===\n")
    
    # 1. Verificar empleados existentes
    empleados = Empleado.objects.all()
    print(f"Total empleados en sistema: {empleados.count()}")
    
    for emp in empleados[:5]:  # Mostrar solo los primeros 5
        print(f"  - Legajo: {emp.legajo}, Nombre: {emp.user.get_full_name()}")
    
    if empleados.count() > 5:
        print(f"  ... y {empleados.count() - 5} más\n")
    else:
        print()
    
    # 2. Verificar cargas masivas existentes
    cargas = CargaMasivaRecibos.objects.all().order_by('-fecha_carga')
    print(f"Total cargas masivas: {cargas.count()}")
    
    if cargas.exists():
        ultima_carga = cargas.first()
        print(f"Última carga: {ultima_carga.periodo} {ultima_carga.anio}")
        print(f"  - Estado: {ultima_carga.estado}")
        print(f"  - Empleados totales: {ultima_carga.total_empleados}")
        print(f"  - Recibos generados: {ultima_carga.recibos_generados}")
        print(f"  - Validado: {'Sí' if ultima_carga.validado else 'No'}")
        print(f"  - Visible empleados: {'Sí' if ultima_carga.visible_empleados else 'No'}")
        
        # 3. Verificar logs de la última carga
        logs = LogProcesamientoRecibo.objects.filter(carga_masiva=ultima_carga)
        print(f"\nLogs de procesamiento: {logs.count()}")
        
        estados = logs.values_list('estado', flat=True)
        for estado in set(estados):
            count = logs.filter(estado=estado).count()
            print(f"  - {estado}: {count}")
        
        # 4. Verificar recibos generados
        recibos = ReciboSueldo.objects.filter(
            periodo=ultima_carga.periodo,
            anio=ultima_carga.anio
        )
        print(f"\nRecibos creados para este período: {recibos.count()}")
        
        estados_recibos = recibos.values_list('estado', flat=True)
        for estado in set(estados_recibos):
            count = recibos.filter(estado=estado).count()
            print(f"  - {estado}: {count}")
        
        # 5. Verificar empleados sin recibo (deberían ser los que no se encontraron)
        empleados_con_recibo = recibos.values_list('empleado_id', flat=True)
        empleados_sin_recibo = empleados.exclude(id__in=empleados_con_recibo)
        
        print(f"\nEmpleados SIN recibo creado: {empleados_sin_recibo.count()}")
        for emp in empleados_sin_recibo[:5]:
            # Verificar si hay log de "no encontrado" para este empleado
            log_no_encontrado = logs.filter(
                legajo_empleado=emp.legajo,
                estado='no_encontrado'
            ).first()
            
            if log_no_encontrado:
                print(f"  ✓ {emp.legajo} ({emp.user.get_full_name()}) - Correctamente NO creado")
            else:
                print(f"  ✗ {emp.legajo} ({emp.user.get_full_name()}) - ERROR: Sin log de no encontrado")
        
        # 6. Verificar logs "no_encontrado" sin recibo correspondiente
        logs_no_encontrado = logs.filter(estado='no_encontrado')
        print(f"\nLogs 'no_encontrado': {logs_no_encontrado.count()}")
        
        for log in logs_no_encontrado[:5]:
            # Verificar que NO exista recibo para este empleado
            recibo_existe = recibos.filter(empleado__legajo=log.legajo_empleado).exists()
            if not recibo_existe:
                print(f"  ✓ {log.legajo_empleado} - Correctamente NO tiene recibo")
            else:
                print(f"  ✗ {log.legajo_empleado} - ERROR: Tiene recibo pero está en log no_encontrado")
        
        print(f"\n=== RESUMEN ===")
        print(f"Empleados totales: {empleados.count()}")
        print(f"Logs 'exitoso': {logs.filter(estado='exitoso').count()}")
        print(f"Logs 'no_encontrado': {logs.filter(estado='no_encontrado').count()}")
        print(f"Logs 'error': {logs.filter(estado='error').count()}")
        print(f"Recibos creados: {recibos.count()}")
        print(f"Empleados sin recibo: {empleados_sin_recibo.count()}")
        
        # Verificar consistencia
        logs_exitosos = logs.filter(estado='exitoso').count()
        if recibos.count() == logs_exitosos:
            print(f"✓ CONSISTENCIA: Recibos creados = Logs exitosos")
        else:
            print(f"✗ INCONSISTENCIA: Recibos ({recibos.count()}) ≠ Logs exitosos ({logs_exitosos})")
            
        if empleados_sin_recibo.count() == logs.filter(estado='no_encontrado').count():
            print(f"✓ CONSISTENCIA: Empleados sin recibo = Logs no_encontrado")
        else:
            print(f"✗ INCONSISTENCIA: Empleados sin recibo ({empleados_sin_recibo.count()}) ≠ Logs no_encontrado ({logs.filter(estado='no_encontrado').count()})")
    
    else:
        print("No hay cargas masivas para probar. Crear una carga primero.\n")

if __name__ == "__main__":
    test_matching_logic()
