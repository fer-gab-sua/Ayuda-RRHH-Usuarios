#!/usr/bin/env python
"""
Script para crear un usuario de RRHH
El usuario tendrá acceso al panel de gestión de RRHH
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_rrhh.settings')
django.setup()

from django.contrib.auth.models import User
from apps.empleados.models import Empleado, DomicilioEmpleado
from django.db import transaction


def crear_usuario_rrhh():
    """Crea un usuario de RRHH"""
    
    print("🏢 CREACIÓN DE USUARIO RRHH")
    print("=" * 50)
    
    # Solicitar datos del usuario
    print("\n📋 Ingresa los datos del usuario de RRHH:")
    
    while True:
        dni = input("DNI (será el nombre de usuario): ").strip()
        if dni and dni.isdigit() and len(dni) >= 6:
            break
        print("❌ El DNI debe tener al menos 6 dígitos numéricos")
    
    nombre = input("Nombre: ").strip()
    while not nombre:
        nombre = input("❌ El nombre es obligatorio. Nombre: ").strip()
    
    apellido = input("Apellido: ").strip()
    while not apellido:
        apellido = input("❌ El apellido es obligatorio. Apellido: ").strip()
    
    email = input("Email (opcional): ").strip()
    
    # Generar contraseña por defecto
    password_default = dni[-6:]  # Últimos 6 dígitos del DNI
    print(f"\n🔐 Contraseña por defecto: {password_default}")
    password = input("Contraseña (presiona Enter para usar la por defecto): ").strip()
    if not password:
        password = password_default
    
    # Datos adicionales opcionales
    print("\n📝 Datos adicionales (opcionales, presiona Enter para omitir):")
    legajo = input("Legajo: ").strip() or dni
    puesto = input("Puesto: ").strip() or "Personal RRHH"
    departamento = input("Departamento: ").strip() or "Recursos Humanos"
    telefono = input("Teléfono: ").strip()
    
    # Confirmar datos
    print("\n" + "=" * 50)
    print("📊 RESUMEN DEL USUARIO A CREAR:")
    print(f"   👤 Nombre: {nombre} {apellido}")
    print(f"   🆔 DNI/Usuario: {dni}")
    print(f"   🔐 Contraseña: {password}")
    print(f"   📧 Email: {email or 'Sin email'}")
    print(f"   🏷️  Legajo: {legajo}")
    print(f"   💼 Puesto: {puesto}")
    print(f"   🏢 Departamento: {departamento}")
    print(f"   📞 Teléfono: {telefono or 'Sin teléfono'}")
    print(f"   🏢 Tipo: USUARIO RRHH (acceso al panel de gestión)")
    print("=" * 50)
    
    confirmar = input("\n¿Crear este usuario? (s/N): ").strip().lower()
    if confirmar not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Operación cancelada")
        return False
    
    try:
        # Verificar si el usuario ya existe
        if User.objects.filter(username=dni).exists():
            print(f"❌ Ya existe un usuario con DNI {dni}")
            return False
        
        with transaction.atomic():
            # Crear usuario Django
            user = User.objects.create_user(
                username=dni,
                password=password,
                first_name=nombre,
                last_name=apellido,
                email=email,
                is_active=True,
                is_staff=True  # Darle acceso al admin de Django también
            )
            
            # Crear perfil de empleado con acceso RRHH
            empleado = Empleado.objects.create(
                user=user,
                legajo=legajo,
                dni=dni,
                telefono=telefono,
                puesto=puesto,
                departamento=departamento,
                es_rrhh=True,  # ¡IMPORTANTE! Esto le da acceso al panel RRHH
                debe_cambiar_password=True  # Cambiar contraseña en primer login
            )
            
            print(f"\n✅ Usuario RRHH creado exitosamente!")
            print(f"   👤 {nombre} {apellido}")
            print(f"   🆔 Usuario: {dni}")
            print(f"   🔐 Contraseña: {password}")
            print(f"   🏢 Acceso: Panel RRHH + Panel Admin Django")
            print(f"   ⚠️  Deberá cambiar la contraseña en el primer login")
            
            return True
            
    except Exception as e:
        print(f"❌ Error al crear usuario RRHH: {e}")
        return False


def main():
    """Función principal"""
    print("🚀 Script para crear usuario de RRHH")
    print("Este usuario tendrá acceso completo al panel de gestión de RRHH")
    
    if crear_usuario_rrhh():
        print("\n🎉 ¡Usuario RRHH creado exitosamente!")
        print("\n📝 PRÓXIMOS PASOS:")
        print("   1. El usuario puede acceder con su DNI y contraseña")
        print("   2. Será redirigido para cambiar su contraseña")
        print("   3. Tendrá acceso completo al panel de RRHH")
        print("   4. También puede acceder al admin de Django (/admin/)")
    else:
        print("\n❌ No se pudo crear el usuario RRHH")


if __name__ == "__main__":
    main()
