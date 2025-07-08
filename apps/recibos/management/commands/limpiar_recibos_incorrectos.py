from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.empleados.models import Empleado
from apps.recibos.models import ReciboSueldo
from apps.rrhh.models import CargaMasivaRecibos, LogProcesamientoRecibo


class Command(BaseCommand):
    help = 'Limpia recibos que puedan haber sido asignados incorrectamente a empleados sin datos válidos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo mostrar qué se eliminaría sin realizar cambios',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.WARNING('Analizando empleados con datos incompletos...'))
        
        # Buscar empleados problemáticos
        empleados_sin_legajo = Empleado.objects.filter(legajo__isnull=True) | Empleado.objects.filter(legajo='')
        empleados_sin_nombre = Empleado.objects.filter(user__first_name__isnull=True) | Empleado.objects.filter(user__first_name='')
        empleados_sin_apellido = Empleado.objects.filter(user__last_name__isnull=True) | Empleado.objects.filter(user__last_name='')
        
        total_problematicos = 0
        recibos_a_eliminar = 0
        
        # Procesar empleados sin legajo
        for empleado in empleados_sin_legajo:
            total_problematicos += 1
            recibos = ReciboSueldo.objects.filter(empleado=empleado)
            recibos_count = recibos.count()
            if recibos_count > 0:
                recibos_a_eliminar += recibos_count
                self.stdout.write(
                    self.style.ERROR(
                        f'Empleado sin legajo: {empleado.user.get_full_name()} - {recibos_count} recibos'
                    )
                )
                if not dry_run:
                    recibos.delete()
        
        # Procesar empleados sin nombre
        for empleado in empleados_sin_nombre:
            total_problematicos += 1
            recibos = ReciboSueldo.objects.filter(empleado=empleado)
            recibos_count = recibos.count()
            if recibos_count > 0:
                recibos_a_eliminar += recibos_count
                self.stdout.write(
                    self.style.ERROR(
                        f'Empleado sin nombre: {empleado.legajo} - {empleado.user.last_name} - {recibos_count} recibos'
                    )
                )
                if not dry_run:
                    recibos.delete()
        
        # Procesar empleados sin apellido
        for empleado in empleados_sin_apellido:
            total_problematicos += 1
            recibos = ReciboSueldo.objects.filter(empleado=empleado)
            recibos_count = recibos.count()
            if recibos_count > 0:
                recibos_a_eliminar += recibos_count
                self.stdout.write(
                    self.style.ERROR(
                        f'Empleado sin apellido: {empleado.legajo} - {empleado.user.first_name} - {recibos_count} recibos'
                    )
                )
                if not dry_run:
                    recibos.delete()
        
        # Buscar recibos en estado 'no_encontrado' que no deberían ser visibles
        recibos_no_encontrados = ReciboSueldo.objects.filter(estado='no_encontrado')
        if recibos_no_encontrados.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'Encontrados {recibos_no_encontrados.count()} recibos en estado "no_encontrado" que deberían ser revisados'
                )
            )
        
        # Resumen
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN: Se eliminarían {recibos_a_eliminar} recibos de {total_problematicos} empleados problemáticos'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Eliminados {recibos_a_eliminar} recibos de {total_problematicos} empleados problemáticos'
                )
            )
        
        # Mostrar estadísticas generales
        total_empleados = Empleado.objects.count()
        total_recibos = ReciboSueldo.objects.count()
        empleados_validos = Empleado.objects.exclude(
            legajo__isnull=True
        ).exclude(
            legajo=''
        ).exclude(
            user__first_name__isnull=True
        ).exclude(
            user__first_name=''
        ).exclude(
            user__last_name__isnull=True
        ).exclude(
            user__last_name=''
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nEstadísticas:\n'
                f'- Total empleados: {total_empleados}\n'
                f'- Empleados válidos: {empleados_validos.count()}\n'
                f'- Empleados problemáticos: {total_problematicos}\n'
                f'- Total recibos actuales: {total_recibos}'
            )
        )
