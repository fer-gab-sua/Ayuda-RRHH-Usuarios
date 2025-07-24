#!/usr/bin/env python
"""
Script para marcar a todos los empleados existentes para que cambien su contraseña
en el primer login (debe_cambiar_password = True)
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_rrhh.settings')
django.setup()

from apps.empleados.models import Empleado
from django.db import transaction


def actualizar_cambio_password():
    """Actualiza el campo debe_cambiar_password para todos los empleados"""
    try:
        with transaction.atomic():
            # Obtener todos los empleados
            empleados = Empleado.objects.all()
            total = empleados.count()
            
            print(f"🔄 Actualizando {total} empleados para que cambien su contraseña en el primer login...")
            print("=" * 70)
            
            # Actualizar todos los empleados
            actualizados = empleados.update(debe_cambiar_password=True)
            
            print(f"✅ Se actualizaron {actualizados} empleados exitosamente")
            print(f"📋 Ahora todos los empleados deberán cambiar su contraseña en el primer login")
            
            return True
            
    except Exception as e:
        print(f"❌ Error al actualizar empleados: {e}")
        return False


def main():
    """Función principal"""
    print("🚀 Actualizando empleados para primer cambio de contraseña...")
    print("=" * 70)
    
    # Confirmar antes de proceder
    respuesta = input("\n¿Proceder con la actualización? (s/N): ")
    if respuesta.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Operación cancelada por el usuario")
        return
    
    if actualizar_cambio_password():
        print("\n🎉 Proceso completado exitosamente!")
        print("\n🔑 IMPORTANTE:")
        print("   - Todos los empleados deberán cambiar su contraseña en el primer login")
        print("   - El sistema los redirigirá automáticamente al cambio de contraseña")
    else:
        print("\n❌ El proceso falló. Revisa los errores anteriores.")


if __name__ == "__main__":
    main()
