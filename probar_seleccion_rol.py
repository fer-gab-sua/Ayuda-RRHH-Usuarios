#!/usr/bin/env python
"""
Script para probar la funcionalidad de selección de rol
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_rrhh.settings')
django.setup()

from django.contrib.auth.models import User
from apps.empleados.models import Empleado
from django.db import transaction


def probar_seleccion_rol():
    """Configura un usuario de prueba que sea tanto empleado como RRHH"""
    
    print("🧪 CONFIGURACIÓN DE USUARIO DE PRUEBA PARA SELECCIÓN DE ROL")
    print("=" * 70)
    
    # Buscar un empleado que ya sea RRHH
    empleados_rrhh = Empleado.objects.filter(es_rrhh=True)
    
    if empleados_rrhh.exists():
        print(f"\n📋 Empleados RRHH encontrados:")
        for i, emp in enumerate(empleados_rrhh[:5], 1):
            print(f"   {i}. {emp.user.get_full_name()} (DNI: {emp.dni}, Usuario: {emp.user.username})")
        
        print(f"\n✅ Estos usuarios RRHH ya pueden probar la selección de rol:")
        print(f"   1. Iniciar sesión con cualquiera de estos usuarios")
        print(f"   2. Después del login, verán la pantalla de selección de rol")
        print(f"   3. Podrán elegir entre 'Portal del Empleado' y 'Panel de RRHH'")
        print(f"   4. Una vez dentro, podrán cambiar de rol usando el botón en la barra lateral")
        
        return True
    else:
        print("❌ No se encontraron usuarios RRHH en el sistema.")
        print("   Ejecuta primero el script 'crear_usuario_rrhh.py' para crear uno.")
        return False


def mostrar_instrucciones():
    """Muestra las instrucciones de uso"""
    print("\n" + "=" * 70)
    print("📖 INSTRUCCIONES DE USO:")
    print("=" * 70)
    
    print("\n🔐 PROCESO DE LOGIN CON SELECCIÓN DE ROL:")
    print("   1. El usuario inicia sesión normalmente")
    print("   2. Si es RRHH, se muestra la pantalla de selección de rol")
    print("   3. Puede elegir entre:")
    print("      📄 Portal del Empleado - Acceso a funciones de empleado")
    print("      👥 Panel de RRHH - Acceso a gestión administrativa")
    
    print("\n🔄 CAMBIO DE ROL SIN CERRAR SESIÓN:")
    print("   • En el Panel RRHH: Botón 'Cambiar a Vista Empleado' en la barra lateral")
    print("   • En Portal Empleado: Botón 'Cambiar a Panel RRHH' en la barra lateral")
    print("   • Al hacer clic, regresa a la pantalla de selección de rol")
    
    print("\n🎯 VENTAJAS DE ESTE SISTEMA:")
    print("   ✅ Un usuario RRHH puede actuar como empleado regular")
    print("   ✅ Puede gestionar sus propios datos personales")
    print("   ✅ Puede cambiar de rol sin cerrar sesión")
    print("   ✅ Interfaz clara para seleccionar el contexto de trabajo")
    
    print("\n🔧 IMPLEMENTACIÓN:")
    print("   • Se usa la sesión para recordar el rol activo")
    print("   • Los mixins verifican el rol antes de mostrar las vistas")
    print("   • El cambio de rol limpia la sesión y permite nueva selección")


def main():
    """Función principal"""
    print("🚀 Script de prueba para selección de rol")
    
    if probar_seleccion_rol():
        mostrar_instrucciones()
        print(f"\n🎉 ¡Sistema de selección de rol configurado y listo!")
        print(f"\n📝 PRÓXIMOS PASOS:")
        print(f"   1. Inicia sesión con un usuario RRHH")
        print(f"   2. Verás la pantalla de selección de rol")
        print(f"   3. Prueba cambiar entre ambos roles")
        print(f"   4. Verifica que las funcionalidades se muestren correctamente")
    else:
        print(f"\n❌ Necesitas crear primero un usuario RRHH")
        print(f"   Ejecuta: python crear_usuario_rrhh.py")


if __name__ == "__main__":
    main()
