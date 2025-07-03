import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_rrhh.settings')
django.setup()

from apps.recibos.models import ReciboSueldo
from apps.empleados.models import Empleado
from django.utils import timezone
from datetime import timedelta

# Obtener empleado
emp = Empleado.objects.first()
print(f'Empleado: {emp.user.username}')

# Borrar recibos existentes para empezar limpio
ReciboSueldo.objects.filter(empleado=emp).delete()
print('Recibos existentes borrados')

# Crear recibos válidos (no vencidos) para testing
# Fecha actual
now = timezone.now()

# Crear recibos con fechas futuras para que no estén vencidos
recibos_data = [
    {'periodo': 'enero', 'anio': 2025, 'dias_vencimiento': 30},
    {'periodo': 'febrero', 'anio': 2025, 'dias_vencimiento': 30},
    {'periodo': 'marzo', 'anio': 2025, 'dias_vencimiento': 30},
]

for data in recibos_data:
    # Crear archivo temporal para el PDF
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n')
        tmp_path = tmp.name
    
    recibo = ReciboSueldo.objects.create(
        empleado=emp,
        periodo=data['periodo'],
        anio=data['anio'],
        fecha_vencimiento=now + timedelta(days=data['dias_vencimiento']),
        sueldo_bruto=100000.00,
        descuentos=25000.00,
        sueldo_neto=75000.00,
        estado='pendiente'
    )
    
    # Asignar el archivo PDF
    recibo.archivo_pdf.name = f'recibos_sueldo/recibo_{data["periodo"]}_{data["anio"]}.pdf'
    recibo.save()
    
    print(f'✓ Creado recibo: {recibo.periodo} {recibo.anio} (vence: {recibo.fecha_vencimiento})')

print(f'\nTotal recibos creados: {ReciboSueldo.objects.filter(empleado=emp).count()}')
