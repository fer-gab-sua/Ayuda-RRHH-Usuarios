#!/usr/bin/env python
"""
Script para crear empleados de prueba para testear la carga masiva de recibos
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_rrhh.settings')
django.setup()

from django.contrib.auth.models import User
from apps.empleados.models import Empleado
from datetime import date

def crear_empleados_prueba():
    """Crear empleados de prueba"""
    empleados_data = [
        {
            'username': 'jperez',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan.perez@empresa.com',
            'legajo': '001',
            'dni': '12345678',
            'telefono': '1234567890',
            'fecha_nacimiento': date(1985, 1, 15),
            'fecha_ingreso': date(2020, 1, 1),
        },
        {
            'username': 'mgonzalez',
            'first_name': 'María',
            'last_name': 'González',
            'email': 'maria.gonzalez@empresa.com',
            'legajo': '002',
            'dni': '23456789',
            'telefono': '2345678901',
            'fecha_nacimiento': date(1990, 5, 20),
            'fecha_ingreso': date(2021, 3, 1),
        },
        {
            'username': 'crodriguez',
            'first_name': 'Carlos',
            'last_name': 'Rodríguez',
            'email': 'carlos.rodriguez@empresa.com',
            'legajo': '003',
            'dni': '34567890',
            'telefono': '3456789012',
            'fecha_nacimiento': date(1988, 8, 10),
            'fecha_ingreso': date(2019, 6, 15),
        },
        {
            'username': 'alopez',
            'first_name': 'Ana',
            'last_name': 'López',
            'email': 'ana.lopez@empresa.com',
            'legajo': '004',
            'dni': '45678901',
            'telefono': '4567890123',
            'fecha_nacimiento': date(1992, 12, 3),
            'fecha_ingreso': date(2022, 1, 10),
        },
        {
            'username': 'rmartinez',
            'first_name': 'Roberto',
            'last_name': 'Martínez',
            'email': 'roberto.martinez@empresa.com',
            'legajo': '005',
            'dni': '56789012',
            'telefono': '5678901234',
            'fecha_nacimiento': date(1987, 3, 25),
            'fecha_ingreso': date(2020, 9, 1),
        }
    ]
    
    print("Creando empleados de prueba...")
    
    for emp_data in empleados_data:
        # Verificar si el usuario ya existe
        if User.objects.filter(username=emp_data['username']).exists():
            print(f"Usuario {emp_data['username']} ya existe, saltando...")
            continue
            
        # Crear usuario
        user = User.objects.create_user(
            username=emp_data['username'],
            first_name=emp_data['first_name'],
            last_name=emp_data['last_name'],
            email=emp_data['email'],
            password='123456'  # Contraseña simple para pruebas
        )
        
        # Crear empleado
        empleado = Empleado.objects.create(
            user=user,
            legajo=emp_data['legajo'],
            dni=emp_data['dni'],
            telefono=emp_data['telefono'],
            fecha_nacimiento=emp_data['fecha_nacimiento'],
            fecha_ingreso=emp_data['fecha_ingreso'],
            estado='activo'
        )
        
        print(f"Empleado creado: {empleado.user.get_full_name()} (Legajo: {empleado.legajo})")
    
    print("\n¡Empleados de prueba creados exitosamente!")
    print("Credenciales:")
    for emp_data in empleados_data:
        print(f"Usuario: {emp_data['username']} | Contraseña: 123456")

if __name__ == '__main__':
    crear_empleados_prueba()
