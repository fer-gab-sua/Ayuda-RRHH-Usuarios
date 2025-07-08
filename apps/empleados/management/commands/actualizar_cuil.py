from django.core.management.base import BaseCommand
from apps.empleados.models import Empleado


class Command(BaseCommand):
    help = 'Actualiza el CUIL de un empleado específico'

    def add_arguments(self, parser):
        parser.add_argument('--legajo', type=str, help='Legajo del empleado')
        parser.add_argument('--cuil', type=str, help='CUIL del empleado')

    def handle(self, *args, **options):
        legajo = options.get('legajo')
        cuil = options.get('cuil')
        
        if not legajo or not cuil:
            self.stdout.write(self.style.ERROR('Debes especificar --legajo y --cuil'))
            return
        
        try:
            empleado = Empleado.objects.get(legajo=legajo)
            empleado_anterior = f"{empleado.user.get_full_name()} - CUIL anterior: '{empleado.cuil}'"
            
            empleado.cuil = cuil
            empleado.save()
            
            self.stdout.write(self.style.SUCCESS(f'✅ CUIL actualizado exitosamente'))
            self.stdout.write(f'   Empleado: {empleado.user.get_full_name()}')
            self.stdout.write(f'   Legajo: {empleado.legajo}')
            self.stdout.write(f'   CUIL anterior: {empleado_anterior}')
            self.stdout.write(f'   CUIL nuevo: {empleado.cuil}')
            
        except Empleado.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'No se encontró empleado con legajo {legajo}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
