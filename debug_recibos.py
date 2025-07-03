import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_rrhh.settings')
django.setup()

from apps.recibos.models import ReciboSueldo
from apps.empleados.models import Empleado

emp = Empleado.objects.first()
print(f'Empleado: {emp.user.username}')
print('\n=== Recibos en la base de datos ===')

recibos = ReciboSueldo.objects.filter(empleado=emp)
print(f'Total recibos: {recibos.count()}')

for r in recibos.order_by('anio', 'periodo'):
    print(f'- {r.periodo} {r.anio}: estado={r.estado}')

print('\n=== Ordenamiento cronológico correcto ===')

# Ordenar correctamente usando get_orden_periodo
recibos_ordenados = []
for r in recibos:
    orden = r.anio * 100 + r.get_orden_periodo()
    recibos_ordenados.append((orden, r))

recibos_ordenados.sort(key=lambda x: x[0])

for i, (orden, r) in enumerate(recibos_ordenados):
    print(f'{i+1}. {r.periodo} {r.anio} (orden={orden}): estado={r.estado}')

print('\n=== Verificando puede_ver y puede_firmar ===')

for i, (orden, r) in enumerate(recibos_ordenados):
    puede_ver = r.puede_ver
    puede_firmar = r.puede_firmar
    esta_vencido = r.esta_vencido
    print(f'{i+1}. {r.periodo} {r.anio}: puede_ver={puede_ver}, puede_firmar={puede_firmar}, estado={r.estado}, esta_vencido={esta_vencido}')
    print(f'   Fecha vencimiento: {r.fecha_vencimiento}')

print('\n=== Verificando lógica de puede_firmar manualmente ===')
primer_recibo = recibos_ordenados[0][1]
print(f'Primer recibo: {primer_recibo.periodo} {primer_recibo.anio}')
print(f'- puede_ver: {primer_recibo.puede_ver}')
print(f'- esta_vencido: {primer_recibo.esta_vencido}')
print(f'- estado: {primer_recibo.estado}')
print(f'- estado == firmado: {primer_recibo.estado == "firmado"}')
print(f'- observaciones pendientes: {primer_recibo.empleado.recibos_sueldo.filter(estado="observado").exists()}')
print(f'- estado in [pendiente, respondido]: {primer_recibo.estado in ["pendiente", "respondido"]}')

print('\n=== Verificando archivos PDF ===')
for i, (orden, r) in enumerate(recibos_ordenados):
    tiene_archivo = bool(r.archivo_pdf and r.archivo_pdf.name)
    if tiene_archivo:
        try:
            # Verificar que el archivo exista físicamente
            archivo_existe = r.archivo_pdf.storage.exists(r.archivo_pdf.name)
            print(f'{i+1}. {r.periodo} {r.anio}: archivo_pdf={r.archivo_pdf.name}, existe={archivo_existe}')
        except Exception as e:
            print(f'{i+1}. {r.periodo} {r.anio}: archivo_pdf={r.archivo_pdf.name}, error={e}')
    else:
        print(f'{i+1}. {r.periodo} {r.anio}: SIN ARCHIVO PDF')
