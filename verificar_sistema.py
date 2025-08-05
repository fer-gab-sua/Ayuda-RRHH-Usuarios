#!/usr/bin/env python
"""
Script para verificar que todas las dependencias están instaladas correctamente
"""

import sys
import django
import os

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_rrhh.settings')
django.setup()

def verificar_dependencias():
    """Verifica que todas las dependencias están disponibles"""
    print("🔍 VERIFICANDO DEPENDENCIAS")
    print("=" * 50)
    
    dependencias = [
        ('Django', 'django'),
        ('Crispy Forms', 'crispy_forms'),
        ('Crispy Bootstrap5', 'crispy_bootstrap5'),
        ('Python Decouple', 'decouple'),
        ('Pillow', 'PIL'),
        ('ReportLab', 'reportlab'),
        ('PyPDF2', 'PyPDF2'),
        ('Pandas', 'pandas'),
        ('NumPy', 'numpy'),
        ('OpenPyXL', 'openpyxl'),
    ]
    
    instaladas = 0
    errores = 0
    
    for nombre, modulo in dependencias:
        try:
            __import__(modulo)
            print(f"✅ {nombre}: OK")
            instaladas += 1
        except ImportError as e:
            print(f"❌ {nombre}: ERROR - {e}")
            errores += 1
    
    print("\n" + "=" * 50)
    print(f"📊 RESUMEN:")
    print(f"✅ Instaladas correctamente: {instaladas}")
    print(f"❌ Con errores: {errores}")
    
    if errores == 0:
        print("\n🎉 ¡Todas las dependencias están instaladas correctamente!")
        return True
    else:
        print(f"\n⚠️  Hay {errores} dependencias con problemas.")
        return False

def verificar_django():
    """Verifica la configuración de Django"""
    print("\n🔍 VERIFICANDO CONFIGURACIÓN DJANGO")
    print("=" * 50)
    
    try:
        from django.core.management import execute_from_command_line
        from django.conf import settings
        
        print(f"✅ Django Version: {django.get_version()}")
        print(f"✅ Debug Mode: {settings.DEBUG}")
        print(f"✅ Database: {settings.DATABASES['default']['ENGINE']}")
        print(f"✅ Secret Key: {'Configurado' if settings.SECRET_KEY else 'NO CONFIGURADO'}")
        
        # Verificar apps instaladas
        apps_importantes = [
            'apps.empleados',
            'apps.recibos',
            'apps.rrhh',
            'crispy_forms',
            'crispy_bootstrap5'
        ]
        
        for app in apps_importantes:
            if app in settings.INSTALLED_APPS:
                print(f"✅ App {app}: Instalada")
            else:
                print(f"❌ App {app}: NO ENCONTRADA")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en Django: {e}")
        return False

def verificar_funciones_pdf():
    """Verifica las funciones de PDF"""
    print("\n🔍 VERIFICANDO FUNCIONES PDF")
    print("=" * 50)
    
    try:
        # Probar imports de PDF
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from PyPDF2 import PdfReader, PdfWriter
        print("✅ Librerías PDF: OK")
        
        # Probar creación básica de PDF
        from io import BytesIO
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.drawString(100, 750, "Test PDF")
        c.save()
        
        if buffer.getvalue():
            print("✅ Generación PDF: OK")
            return True
        else:
            print("❌ Generación PDF: Error")
            return False
            
    except Exception as e:
        print(f"❌ Error en PDF: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 VERIFICADOR DE SISTEMA RRHH")
    print("=" * 50)
    print(f"Python Version: {sys.version}")
    print("")
    
    # Verificar dependencias
    deps_ok = verificar_dependencias()
    
    # Verificar Django
    django_ok = verificar_django()
    
    # Verificar PDF
    pdf_ok = verificar_funciones_pdf()
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📋 RESUMEN FINAL")
    print("=" * 50)
    
    if deps_ok and django_ok and pdf_ok:
        print("🎉 ¡TODO ESTÁ FUNCIONANDO CORRECTAMENTE!")
        print("   El sistema está listo para usar.")
        print("\n🚀 Próximos pasos:")
        print("   1. python manage.py migrate")
        print("   2. python manage.py createsuperuser")
        print("   3. python manage.py runserver")
        return True
    else:
        print("⚠️  HAY ALGUNOS PROBLEMAS")
        print("   Revisa los errores mostrados arriba.")
        print("\n🔧 Soluciones:")
        print("   1. pip install -r requirements.txt")
        print("   2. Verificar versión de Python (necesita 3.10)")
        return False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Verificación cancelada por el usuario.")
    except Exception as e:
        print(f"\n\n💥 Error inesperado: {e}")
        import traceback
        traceback.print_exc()
