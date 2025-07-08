from apps.empleados.models import Empleado
from apps.recibos.models import ReciboSueldo

try:
    empleado = Empleado.objects.get(legajo='808')
    print(f'Empleado: {empleado.user.get_full_name()} (Legajo: {empleado.legajo})')
    print(f'Tiene firma digital: {"Sí" if empleado.firma_imagen else "No"}')
    print(f'PIN configurado: {"Sí" if empleado.firma_pin else "No"}')
    print()
    recibos = ReciboSueldo.objects.filter(empleado=empleado).order_by('anio', 'periodo')
    print('Recibos disponibles:')
    for recibo in recibos:
        print(f'  - {recibo.get_periodo_display()} {recibo.anio}: {recibo.estado}')
        print(f'    Puede ver: {recibo.puede_ver}')
        print(f'    Puede firmar: {recibo.puede_firmar}')
        print(f'    Archivo PDF: {"Sí" if recibo.archivo_pdf else "No"}')
        print(f'    Recibo ID: {recibo.id}')
        print()
except Empleado.DoesNotExist:
    print('No se encontró empleado con legajo 808')
