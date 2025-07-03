from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from rrhh.models import Empleado, TipoSolicitud, ReciboSueldo, Notificacion
import os


class Command(BaseCommand):
    help = 'Crear datos de ejemplo para el sistema'

    def handle(self, *args, **options):
        # Crear usuario Fernando
        user, created = User.objects.get_or_create(
            username='fernando',
            defaults={
                'first_name': 'Fernando',
                'last_name': 'Pérez',
                'email': 'fernando@empresa.com',
                'is_active': True,
            }
        )
        if created:
            user.set_password('fernando123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Usuario {user.username} creado'))

        # Crear empleado
        empleado, created = Empleado.objects.get_or_create(
            user=user,
            defaults={
                'dni': '12345678',
                'fecha_nacimiento': date(1985, 6, 15),
                'telefono': '+54 11 1234-5678',
                'direccion': 'Av. Corrientes 1234',
                'ciudad': 'Buenos Aires',
                'codigo_postal': '1043',
                'telefono_emergencia': '+54 11 8765-4321',
                'contacto_emergencia': 'María Pérez (Esposa)',
                'fecha_ingreso': date(2020, 3, 1),
                'puesto': 'Desarrollador Senior',
                'departamento': 'Tecnología',
                'salario': 150000.00,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Empleado {empleado} creado'))

        # Crear tipos de solicitud
        tipos_solicitud = [
            {'nombre': 'Día de Estudio', 'descripcion': 'Solicitud para día de estudio'},
            {'nombre': 'Vacaciones', 'descripcion': 'Solicitud de vacaciones'},
            {'nombre': 'Genérica', 'descripcion': 'Solicitud genérica'},
            {'nombre': 'Licencia por enfermedad', 'descripcion': 'Licencia médica'},
            {'nombre': 'Permiso personal', 'descripcion': 'Permiso por asuntos personales'},
        ]

        for tipo_data in tipos_solicitud:
            tipo, created = TipoSolicitud.objects.get_or_create(
                nombre=tipo_data['nombre'],
                defaults=tipo_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Tipo de solicitud {tipo.nombre} creado'))

        # Crear recibos de sueldo de ejemplo
        recibos_data = [
            {'periodo': 'Mayo 2024', 'fecha': date(2024, 5, 31), 'estado': 'pendiente'},
            {'periodo': 'Abril 2024', 'fecha': date(2024, 4, 30), 'estado': 'firmado'},
            {'periodo': 'Marzo 2024', 'fecha': date(2024, 3, 31), 'estado': 'firmado'},
            {'periodo': 'Febrero 2024', 'fecha': date(2024, 2, 29), 'estado': 'disconformidad'},
        ]

        for recibo_data in recibos_data:
            # Crear un archivo dummy para el recibo
            recibo, created = ReciboSueldo.objects.get_or_create(
                empleado=empleado,
                periodo=recibo_data['periodo'],
                defaults={
                    'fecha': recibo_data['fecha'],
                    'archivo': f"recibos/recibo_{recibo_data['periodo'].replace(' ', '_').lower()}.pdf",
                    'estado': recibo_data['estado'],
                    'observaciones': 'Recibo de ejemplo' if recibo_data['estado'] != 'pendiente' else '',
                    'fecha_firma': timezone.now() - timedelta(days=30) if recibo_data['estado'] != 'pendiente' else None,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Recibo {recibo.periodo} creado'))

        # Crear notificaciones de ejemplo
        notificaciones_data = [
            {
                'titulo': 'Nuevo recibo disponible',
                'mensaje': 'Tu recibo de Mayo 2024 está disponible para firmar.',
                'tipo': 'info',
            },
            {
                'titulo': 'Recordatorio: Actualizar datos',
                'mensaje': 'Recuerda mantener actualizados tus datos de contacto.',
                'tipo': 'recordatorio',
            },
            {
                'titulo': 'Cambios en el sistema',
                'mensaje': 'El sistema estará en mantenimiento el próximo fin de semana.',
                'tipo': 'alerta',
            },
        ]

        for notif_data in notificaciones_data:
            notif, created = Notificacion.objects.get_or_create(
                empleado=empleado,
                titulo=notif_data['titulo'],
                defaults={
                    'mensaje': notif_data['mensaje'],
                    'tipo': notif_data['tipo'],
                    'leida': False,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Notificación "{notif.titulo}" creada'))

        self.stdout.write(
            self.style.SUCCESS(
                '\n¡Datos de ejemplo creados exitosamente!\n'
                'Usuario: fernando\n'
                'Contraseña: fernando123\n'
                'Admin: admin (sin contraseña configurada)\n'
            )
        )
