#!/usr/bin/env python
"""
Script para regenerar el PDF de Centromédica de un recibo específico
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_rrhh.settings')
django.setup()

from apps.recibos.models import ReciboSueldo
from apps.recibos.views import aplicar_formato_centromedica_a_pdf_firmado
from django.core.files.base import ContentFile

def regenerar_centromedica_recibo(recibo_id):
    """Regenera el PDF de Centromédica para un recibo específico"""
    
    try:
        recibo = ReciboSueldo.objects.get(id=recibo_id)
        print(f"📄 Recibo encontrado: {recibo.get_periodo_display()} {recibo.anio} - {recibo.empleado.user.get_full_name()}")
        print(f"📊 Estado: {recibo.estado}")
        
        if recibo.estado != 'firmado':
            print(f"❌ El recibo debe estar firmado para regenerar el formato Centromédica")
            return False
        
        if not recibo.archivo_firmado:
            print(f"❌ No se encontró el archivo firmado")
            return False
        
        # Leer el contenido del PDF firmado
        recibo.archivo_firmado.seek(0)
        pdf_firmado_content = recibo.archivo_firmado.read()
        print(f"📋 PDF firmado leído: {len(pdf_firmado_content)} bytes")
        
        # Aplicar formato de Centromédica al PDF firmado
        print(f"🎨 Aplicando formato de Centromédica...")
        pdf_centromedica = aplicar_formato_centromedica_a_pdf_firmado(recibo, recibo.empleado, pdf_firmado_content)
        
        if pdf_centromedica and len(pdf_centromedica) > 1000:
            # Guardar el nuevo archivo
            centromedica_filename = f"recibo_centromedica_{recibo.periodo}_{recibo.anio}_{recibo.empleado.legajo}.pdf"
            recibo.archivo_pdf_centromedica.save(centromedica_filename, ContentFile(pdf_centromedica), save=True)
            
            print(f"✅ PDF de Centromédica regenerado exitosamente!")
            print(f"📁 Archivo: {centromedica_filename}")
            print(f"📊 Tamaño: {len(pdf_centromedica)} bytes")
            return True
        else:
            print(f"❌ Error al generar el PDF de Centromédica")
            return False
        
    except ReciboSueldo.DoesNotExist:
        print(f"❌ No se encontró el recibo con ID {recibo_id}")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    print("🔄 Regenerar PDF de Centromédica")
    print("=" * 50)
    
    recibo_id = input("Ingresa el ID del recibo: ").strip()
    
    if not recibo_id.isdigit():
        print("❌ El ID debe ser un número")
        return
    
    recibo_id = int(recibo_id)
    
    if regenerar_centromedica_recibo(recibo_id):
        print(f"\n🎉 ¡PDF de Centromédica regenerado exitosamente!")
        print(f"🌐 Puedes verlo en: http://127.0.0.1:8000/recibos/{recibo_id}/centromedica/")
    else:
        print(f"\n❌ No se pudo regenerar el PDF de Centromédica")

if __name__ == "__main__":
    main()
