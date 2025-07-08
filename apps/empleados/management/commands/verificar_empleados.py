from django.core.management.base import BaseCommand
from apps.empleados.models import Empleado
from apps.rrhh.models import CargaMasivaRecibos


class Command(BaseCommand):
    help = 'Verifica los datos de empleados específicos'

    def add_arguments(self, parser):
        parser.add_argument('--legajo', type=str, help='Legajo del empleado a verificar')

    def handle(self, *args, **options):
        legajo = options.get('legajo')
        
        if legajo:
            # Verificar empleado específico
            try:
                empleado = Empleado.objects.get(legajo=legajo)
                self.mostrar_empleado(empleado)
            except Empleado.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'No se encontró empleado con legajo {legajo}'))
        else:
            # Mostrar todos los empleados
            self.stdout.write(self.style.SUCCESS('👥 Empleados en la base de datos'))
            self.stdout.write('=' * 60)
            
            empleados = Empleado.objects.all().order_by('legajo')
            for empleado in empleados:
                self.mostrar_empleado(empleado)
                self.stdout.write('-' * 40)

    def mostrar_empleado(self, empleado):
        self.stdout.write(f'🧑 Empleado: {empleado.user.get_full_name()}')
        self.stdout.write(f'   📝 Legajo: {empleado.legajo}')
        self.stdout.write(f'   👤 Nombre: {empleado.user.first_name}')
        self.stdout.write(f'   👤 Apellido: {empleado.user.last_name}')
        self.stdout.write(f'   📧 Email: {empleado.user.email}')
        self.stdout.write(f'   🏢 Departamento: {empleado.departamento}')
        self.stdout.write(f'   💼 Puesto: {empleado.puesto}')
        
        # Formato para búsqueda en PDF
        apellido_nombre_busqueda = f"{empleado.user.last_name.upper().strip()}, {empleado.user.first_name.upper().strip()}"
        self.stdout.write(f'   🔍 Formato búsqueda PDF: "{apellido_nombre_busqueda}"')
        
        # Verificar si tiene firma
        tiene_firma = empleado.firma_imagen is not None and empleado.firma_imagen != ''
        self.stdout.write(f'   ✍️  Tiene firma digital: {"Sí" if tiene_firma else "No"}')
