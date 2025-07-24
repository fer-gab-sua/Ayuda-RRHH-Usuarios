#!/usr/bin/env python
"""
Script para crear usuarios desde archivo Excel
Crea usuarios de tipo empleado donde:
- Usuario: número de documento
- Contraseña: últimos 6 dígitos del documento
"""

import os
import sys
import django
import pandas as pd
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_rrhh.settings')
django.setup()

from django.contrib.auth.models import User
from apps.empleados.models import Empleado, DomicilioEmpleado, ObraSocialEmpleado
from django.db import transaction


def leer_excel():
    """Lee el archivo Excel y retorna los datos"""
    try:
        # Intentar leer el archivo Excel
        df = pd.read_excel('Lista empleados.xls')
        print(f"✅ Archivo Excel leído exitosamente. Filas encontradas: {len(df)}")
        print(f"📋 Columnas disponibles: {list(df.columns)}")
        return df
    except Exception as e:
        print(f"❌ Error al leer el archivo Excel: {e}")
        return None


def limpiar_texto(texto):
    """Limpia y normaliza texto"""
    if pd.isna(texto) or texto is None:
        return ""
    return str(texto).strip()


def limpiar_numero(numero):
    """Limpia y normaliza números"""
    if pd.isna(numero) or numero is None:
        return ""
    # Remover puntos y espacios de números de documento
    return str(numero).replace(".", "").replace(" ", "").strip()


def procesar_fecha(fecha):
    """Procesa fechas desde Excel"""
    if pd.isna(fecha) or fecha is None:
        return None
    
    try:
        if isinstance(fecha, str):
            # Intentar parsear diferentes formatos de fecha
            for formato in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                try:
                    return datetime.strptime(fecha, formato).date()
                except ValueError:
                    continue
        elif hasattr(fecha, 'date'):
            return fecha.date()
        return None
    except:
        return None


def crear_usuario_empleado(fila, numero_fila):
    """Crea un usuario y su perfil de empleado"""
    try:
        # Obtener datos básicos - usando los nombres de columnas correctos del Excel
        documento = limpiar_numero(fila.get('DNI', '') or fila.get('Documento', ''))
        nombre = limpiar_texto(fila.get('Nombre', ''))
        apellido = limpiar_texto(fila.get('Apellido', ''))
        
        if not documento or not nombre or not apellido:
            print(f"⚠️  Fila {numero_fila}: Faltan datos básicos (documento: '{documento}', nombre: '{nombre}', apellido: '{apellido}')")
            return False
            
        # Verificar que el documento tenga al menos 6 dígitos
        if len(documento) < 6:
            print(f"⚠️  Fila {numero_fila}: Documento {documento} muy corto (menos de 6 dígitos)")
            return False
            
        # Generar contraseña (últimos 6 dígitos del documento)
        password = documento[-6:]
        
        # Verificar si el usuario ya existe
        if User.objects.filter(username=documento).exists():
            print(f"⚠️  Fila {numero_fila}: Usuario {documento} ya existe")
            return False
            
        with transaction.atomic():
            # Crear usuario Django
            user = User.objects.create_user(
                username=documento,
                password=password,
                first_name=nombre.strip(),
                last_name=apellido.strip(),
                email=limpiar_texto(fila.get('Correo electronico', '')),
                is_active=True
            )
            
            # Crear perfil de empleado
            empleado = Empleado.objects.create(
                user=user,
                legajo=str(fila.get('Legajo', documento)),
                dni=documento,  # Campo correcto es 'dni'
                cuil=limpiar_numero(fila.get('CUIL', '')),
                telefono=limpiar_texto(fila.get('Telefono', '') or fila.get('Contacto', '')),
                fecha_nacimiento=procesar_fecha(fila.get('Fecha de nacimiento')),
                fecha_contrato=procesar_fecha(fila.get('Fecha de ingreso')),  # fecha_contrato en lugar de fecha_ingreso
                puesto=limpiar_texto(fila.get('Puesto ', '') or fila.get('Cargo', 'Empleado')),  # Nota: 'Puesto ' tiene espacio
                departamento=limpiar_texto(fila.get('Sector', '')),
                salario=float(fila.get('Basico Categoria', 0)) if pd.notna(fila.get('Basico Categoria')) else 0,  # Campo correcto es 'salario'
                debe_cambiar_password=True  # Marcar para que cambien la contraseña en el primer login
            )
            
            # Crear obra social si hay datos
            obra_social_nombre = limpiar_texto(fila.get('Obra social', ''))
            if obra_social_nombre:
                ObraSocialEmpleado.objects.create(
                    empleado=empleado,
                    nombre=obra_social_nombre,
                    fecha_alta=procesar_fecha(fila.get('Fecha de ingreso'))  # Usar fecha de ingreso como fecha de alta
                )
            
            # Crear domicilio con los datos disponibles
            direccion_base = limpiar_texto(fila.get('Domicilio', ''))
            if direccion_base:
                # Separar calle y número si es posible
                partes_direccion = direccion_base.split()
                if len(partes_direccion) > 1 and partes_direccion[-1].isdigit():
                    calle = ' '.join(partes_direccion[:-1])
                    numero = partes_direccion[-1]
                else:
                    calle = direccion_base
                    numero = ''
                
                DomicilioEmpleado.objects.create(
                    empleado=empleado,
                    calle=calle,
                    numero=numero,
                    piso=limpiar_texto(fila.get('Piso', '')),
                    depto=limpiar_texto(fila.get('Depto', '')),
                    localidad=limpiar_texto(fila.get('Localidad', '') or fila.get('per_locms', '')),
                    provincia=limpiar_texto(fila.get('Provincia', '')),
                    codigo_postal=str(fila.get('CP', '')) if pd.notna(fila.get('CP')) else '',
                )
            
            print(f"✅ Fila {numero_fila}: Usuario {documento} ({nombre.strip()} {apellido.strip()}) creado exitosamente")
            return True
            
    except Exception as e:
        print(f"❌ Fila {numero_fila}: Error al crear usuario {documento}: {e}")
        return False


def main():
    """Función principal"""
    print("🚀 Iniciando creación de usuarios desde Excel...")
    print("=" * 60)
    
    # Leer archivo Excel
    df = leer_excel()
    if df is None:
        return
    
    # Mostrar muestra de datos
    print("\n📊 Primeras 3 filas del archivo:")
    print(df.head(3).to_string())
    print("\n" + "=" * 60)
    
    # Confirmar antes de proceder
    respuesta = input(f"\n¿Proceder con la creación de {len(df)} usuarios? (s/N): ")
    if respuesta.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Operación cancelada por el usuario")
        return
    
    # Procesar cada fila
    creados = 0
    errores = 0
    
    print(f"\n🔄 Procesando {len(df)} empleados...")
    print("=" * 60)
    
    for index, fila in df.iterrows():
        numero_fila = index + 2  # +2 porque Excel empieza en 1 y hay header
        
        if crear_usuario_empleado(fila, numero_fila):
            creados += 1
        else:
            errores += 1
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN FINAL:")
    print(f"✅ Usuarios creados exitosamente: {creados}")
    print(f"❌ Errores encontrados: {errores}")
    print(f"📋 Total procesado: {creados + errores}")
    
    if creados > 0:
        print(f"\n🔑 IMPORTANTE:")
        print(f"   - Usuario: número de documento")
        print(f"   - Contraseña: últimos 6 dígitos del documento")
        print(f"   - Todos los usuarios están activos")
    
    print("\n🎉 Proceso completado!")


if __name__ == "__main__":
    main()
