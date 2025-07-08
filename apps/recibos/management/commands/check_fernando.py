from django.core.management.base import BaseCommand
from apps.empleados.models import Empleado
from apps.recibos.models import ReciboSueldo


class Command(BaseCommand):
    help = 'Verifica el estado de Fernando Suárez'

    def handle(self, *args, **options):
        try:
            empleado = Empleado.objects.get(legajo='808')
            self.stdout.write(f'Empleado: {empleado.user.get_full_name()} (Legajo: {empleado.legajo})')
            self.stdout.write(f'Tiene firma digital: {"Sí" if empleado.firma_imagen else "No"}')
            self.stdout.write(f'PIN configurado: {"Sí" if empleado.firma_pin else "No"}')
            self.stdout.write('')
            
            recibos = ReciboSueldo.objects.filter(empleado=empleado).order_by('anio', 'periodo')
            self.stdout.write('Recibos disponibles:')
            for recibo in recibos:
                self.stdout.write(f'  - {recibo.get_periodo_display()} {recibo.anio}: {recibo.estado}')
                self.stdout.write(f'    Puede ver: {recibo.puede_ver}')
                self.stdout.write(f'    Puede firmar: {recibo.puede_firmar}')
                self.stdout.write(f'    Archivo PDF: {"Sí" if recibo.archivo_pdf else "No"}')
                self.stdout.write(f'    Recibo ID: {recibo.id}')
                self.stdout.write('')
        except Empleado.DoesNotExist:
            self.stdout.write('No se encontró empleado con legajo 808')
