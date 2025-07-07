#!/usr/bin/env python
"""
Script para crear usuarios de ejemplo basados en los datos del PDF del recibo
"""
import os
import django
import sys

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_rrhh.settings')
django.setup()

from django.contrib.auth.models import User
from apps.empleados.models import Empleado
from django.utils import timezone
from datetime import date

def crear_usuarios_ejemplo():
    """Crear usuarios de ejemplo basados en el PDF"""
    
    # Usuario 1: INGRASSIA, KARINA PAOLA (del PDF)
    try:
        user1 = User.objects.create_user(
            username='kingrassia',
            email='karina.ingrassia@empresa.com',
            password='demo123',
            first_name='Karina Paola',
            last_name='Ingrassia'
        )
        
        empleado1 = Empleado.objects.create(
            user=user1,
            legajo='EMP0007',
            numero_legajo=7,
            dni='22635714',
            cuil='27-22635714-4',
            fecha_nacimiento=date(1980, 5, 15),
            telefono='1234567890',
            puesto='Administrativa',
            departamento='Administración',
            supervisor='Juan Pérez',
            salario=450000.00,
            fecha_contrato=date(2020, 1, 15),
            contacto_emergencia='Carlos Ingrassia',
            telefono_emergencia='0987654321',
            relacion_emergencia='esposo/a'
        )
        print(f"✓ Usuario creado: {user1.get_full_name()} - Legajo: {empleado1.legajo}")
        
    except Exception as e:
        print(f"✗ Error creando usuario Karina Ingrassia: {e}")
    
    # Usuario 2: Ejemplo adicional
    try:
        user2 = User.objects.create_user(
            username='jperez',
            email='juan.perez@empresa.com',
            password='demo123',
            first_name='Juan',
            last_name='Pérez'
        )
        
        empleado2 = Empleado.objects.create(
            user=user2,
            legajo='EMP0001',
            numero_legajo=1,
            dni='20123456',
            cuil='20-20123456-7',
            fecha_nacimiento=date(1975, 3, 20),
            telefono='1122334455',
            puesto='Gerente',
            departamento='Administración',
            supervisor='Director General',
            salario=800000.00,
            fecha_contrato=date(2015, 6, 1),
            contacto_emergencia='María Pérez',
            telefono_emergencia='1199887766',
            relacion_emergencia='esposo/a'
        )
        print(f"✓ Usuario creado: {user2.get_full_name()} - Legajo: {empleado2.legajo}")
        
    except Exception as e:
        print(f"✗ Error creando usuario Juan Pérez: {e}")
    
    # Usuario 3: Usuario de RRHH
    try:
        user3 = User.objects.create_user(
            username='rrhh',
            email='rrhh@empresa.com',
            password='demo123',
            first_name='María',
            last_name='González'
        )
        
        empleado3 = Empleado.objects.create(
            user=user3,
            es_rrhh=True,  # Este es el usuario de RRHH
            legajo='EMP0999',
            numero_legajo=999,
            dni='30456789',
            cuil='27-30456789-1',
            fecha_nacimiento=date(1985, 8, 10),
            telefono='1155443322',
            puesto='Especialista RRHH',
            departamento='Recursos Humanos',
            supervisor='Director RRHH',
            salario=600000.00,
            fecha_contrato=date(2018, 3, 15),
            contacto_emergencia='Carlos González',
            telefono_emergencia='1166554433',
            relacion_emergencia='hermano/a'
        )
        print(f"✓ Usuario RRHH creado: {user3.get_full_name()} - Legajo: {empleado3.legajo}")
        
    except Exception as e:
        print(f"✗ Error creando usuario RRHH: {e}")
    
    # Usuario 4: Otro empleado para pruebas
    try:
        user4 = User.objects.create_user(
            username='alopez',
            email='ana.lopez@empresa.com',
            password='demo123',
            first_name='Ana',
            last_name='López'
        )
        
        empleado4 = Empleado.objects.create(
            user=user4,
            legajo='EMP0002',
            numero_legajo=2,
            dni='25987654',
            cuil='27-25987654-2',
            fecha_nacimiento=date(1990, 12, 5),
            telefono='1177665544',
            puesto='Contadora',
            departamento='Contabilidad',
            supervisor='Juan Pérez',
            salario=550000.00,
            fecha_contrato=date(2019, 9, 1),
            contacto_emergencia='Luis López',
            telefono_emergencia='1188776655',
            relacion_emergencia='padre/madre'
        )
        print(f"✓ Usuario creado: {user4.get_full_name()} - Legajo: {empleado4.legajo}")
        
    except Exception as e:
        print(f"✗ Error creando usuario Ana López: {e}")
    
    print("\n" + "="*50)
    print("RESUMEN DE USUARIOS CREADOS:")
    print("="*50)
    
    for empleado in Empleado.objects.all():
        tipo = " (RRHH)" if empleado.es_rrhh else ""
        print(f"• {empleado.user.get_full_name()}{tipo}")
        print(f"  - Usuario: {empleado.user.username}")
        print(f"  - Legajo: {empleado.legajo} (Número: {empleado.numero_legajo})")
        print(f"  - CUIL: {empleado.cuil}")
        print(f"  - Puesto: {empleado.puesto}")
        print(f"  - Contraseña: demo123")
        print()

if __name__ == '__main__':
    crear_usuarios_ejemplo()
