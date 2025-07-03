import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_rrhh.settings')
django.setup()

from apps.empleados.models import Empleado
from apps.recibos.models import ReciboSueldo
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.files.base import ContentFile
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def crear_pdf_simple(empleado, periodo, anio):
    """Crear un PDF simple para el recibo"""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Título
    p.drawString(100, 750, f"RECIBO DE SUELDO - {periodo.upper()} {anio}")
    p.drawString(100, 720, f"Empleado: {empleado.user.get_full_name() or empleado.user.username}")
    p.drawString(100, 700, f"Legajo: {empleado.legajo}")
    p.drawString(100, 680, f"Período: {periodo} {anio}")
    p.drawString(100, 650, "Sueldo Bruto: $250,000.00")
    p.drawString(100, 630, "Descuentos: $50,000.00")
    p.drawString(100, 610, "Sueldo Neto: $200,000.00")
    
    p.save()
    buffer.seek(0)
    return buffer.getvalue()

# Obtener empleados
empleados = Empleado.objects.all()
print(f"Empleados encontrados: {empleados.count()}")

# Crear recibos para los últimos 3 meses
periodos = [
    ('abril', 2025),
    ('mayo', 2025),
    ('junio', 2025)
]

recibos_creados = 0

for empleado in empleados:
    print(f"Creando recibos para: {empleado.user.get_full_name() or empleado.user.username}")
    
    for periodo, anio in periodos:
        # Verificar si ya existe
        if ReciboSueldo.objects.filter(empleado=empleado, periodo=periodo, anio=anio).exists():
            print(f"  - {periodo} {anio}: Ya existe")
            continue
        
        # Crear PDF
        pdf_content = crear_pdf_simple(empleado, periodo, anio)
        
        # Fecha de emisión y vencimiento
        fecha_emision = timezone.now() - timedelta(days=30)
        fecha_vencimiento = timezone.now() + timedelta(days=15)
        
        # Crear recibo
        recibo = ReciboSueldo.objects.create(
            empleado=empleado,
            periodo=periodo,
            anio=anio,
            fecha_emision=fecha_emision,
            fecha_vencimiento=fecha_vencimiento,
            sueldo_bruto=250000,
            descuentos=50000,
            sueldo_neto=200000,
            estado='pendiente'
        )
        
        # Guardar PDF
        pdf_filename = f"recibo_{periodo}_{anio}_{empleado.legajo}.pdf"
        recibo.archivo_pdf.save(pdf_filename, ContentFile(pdf_content), save=True)
        
        print(f"  - {periodo} {anio}: Creado")
        recibos_creados += 1

print(f"\nTotal de recibos creados: {recibos_creados}")
