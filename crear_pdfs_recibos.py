import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_rrhh.settings')
django.setup()

from apps.recibos.models import ReciboSueldo
from apps.empleados.models import Empleado
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from io import BytesIO

def crear_pdf_recibo(empleado, periodo, anio, sueldo_bruto, descuentos, sueldo_neto):
    """Crear un PDF de recibo de sueldo"""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Título
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(width/2, height-50, "RECIBO DE SUELDO")
    
    # Información del empleado
    p.setFont("Helvetica", 12)
    y = height - 100
    
    p.drawString(50, y, f"Empleado: {empleado.user.get_full_name()}")
    y -= 20
    p.drawString(50, y, f"Legajo: {empleado.legajo}")
    y -= 20
    p.drawString(50, y, f"Período: {periodo.title()} {anio}")
    y -= 40
    
    # Datos del recibo
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "DETALLE DEL RECIBO")
    y -= 30
    
    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Sueldo Bruto: ${sueldo_bruto:,.2f}")
    y -= 20
    p.drawString(50, y, f"Descuentos: ${descuentos:,.2f}")
    y -= 20
    p.drawString(50, y, f"Sueldo Neto: ${sueldo_neto:,.2f}")
    y -= 40
    
    # Pie de página
    p.setFont("Helvetica", 10)
    p.drawString(50, 50, "Este es un recibo de sueldo generado automáticamente.")
    p.drawString(50, 35, "Debe ser firmado digitalmente para ser válido.")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer.getvalue()

# Obtener empleado
emp = Empleado.objects.first()
print(f'Empleado: {emp.user.username}')

# Obtener recibos existentes
recibos = ReciboSueldo.objects.filter(empleado=emp).order_by('anio', 'periodo')
print(f'Recibos encontrados: {recibos.count()}')

for recibo in recibos:
    print(f'\nProcesando recibo: {recibo.periodo} {recibo.anio}')
    
    # Crear PDF
    pdf_content = crear_pdf_recibo(
        recibo.empleado,
        recibo.periodo,
        recibo.anio,
        recibo.sueldo_bruto,
        recibo.descuentos,
        recibo.sueldo_neto
    )
    
    # Guardar el PDF
    filename = f"recibo_{recibo.periodo}_{recibo.anio}_{recibo.empleado.legajo}.pdf"
    recibo.archivo_pdf.save(filename, ContentFile(pdf_content))
    
    print(f'✓ PDF creado: {filename}')
    print(f'  - Archivo PDF: {recibo.archivo_pdf.url}')

print(f'\n✅ Todos los PDFs han sido creados correctamente!')
