from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from apps.empleados.models import Empleado
import secrets
import string


class Command(BaseCommand):
    help = 'Crea un empleado con contraseña temporal y marca para cambio obligatorio'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, required=True, help='Nombre de usuario')
        parser.add_argument('--email', type=str, required=True, help='Email del usuario')
        parser.add_argument('--first_name', type=str, required=True, help='Nombre')
        parser.add_argument('--last_name', type=str, required=True, help='Apellido')
        parser.add_argument('--legajo', type=str, required=True, help='Legajo del empleado')
        parser.add_argument('--dni', type=str, required=True, help='DNI del empleado')
        parser.add_argument('--puesto', type=str, help='Puesto del empleado')
        parser.add_argument('--es_rrhh', action='store_true', help='Marcar como usuario de RRHH')
        parser.add_argument('--password', type=str, help='Contraseña específica (opcional, se genera automáticamente si no se proporciona)')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        first_name = options['first_name']
        last_name = options['last_name']
        legajo = options['legajo']
        dni = options['dni']
        puesto = options.get('puesto', 'Sin especificar')
        es_rrhh = options['es_rrhh']
        custom_password = options.get('password')

        # Verificar si el usuario ya existe
        if User.objects.filter(username=username).exists():
            raise CommandError(f'El usuario "{username}" ya existe.')

        # Verificar si el legajo ya existe
        if Empleado.objects.filter(legajo=legajo).exists():
            raise CommandError(f'El legajo "{legajo}" ya existe.')

        # Generar contraseña temporal si no se proporciona una
        if custom_password:
            password_temporal = custom_password
        else:
            # Generar una contraseña segura pero fácil de comunicar
            # Formato: 3 letras mayúsculas + 3 números + 2 letras minúsculas
            mayusculas = ''.join(secrets.choice(string.ascii_uppercase) for _ in range(3))
            numeros = ''.join(secrets.choice(string.digits) for _ in range(3))
            minusculas = ''.join(secrets.choice(string.ascii_lowercase) for _ in range(2))
            password_temporal = mayusculas + numeros + minusculas

        try:
            # Crear el usuario
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password_temporal,
                first_name=first_name,
                last_name=last_name
            )

            # Crear el empleado
            empleado = Empleado.objects.create(
                user=user,
                legajo=legajo,
                dni=dni,
                puesto=puesto,
                es_rrhh=es_rrhh,
                debe_cambiar_password=True  # Marcar para cambio obligatorio
            )

            # Mostrar información de éxito
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n¡Empleado creado exitosamente!\n'
                    f'Usuario: {username}\n'
                    f'Email: {email}\n'
                    f'Nombre completo: {first_name} {last_name}\n'
                    f'Legajo: {legajo}\n'
                    f'DNI: {dni}\n'
                    f'Puesto: {puesto}\n'
                    f'Tipo: {"RRHH" if es_rrhh else "Empleado"}\n'
                    f'Contraseña temporal: {password_temporal}\n'
                    f'\n⚠️  El usuario DEBE cambiar la contraseña en su primer login.\n'
                )
            )

            # Información adicional sobre seguridad
            self.stdout.write(
                self.style.WARNING(
                    f'\n📋 INSTRUCCIONES PARA EL EMPLEADO:\n'
                    f'1. Usar usuario: {username}\n'
                    f'2. Usar contraseña temporal: {password_temporal}\n'
                    f'3. El sistema le pedirá cambiar la contraseña inmediatamente\n'
                    f'4. Después del cambio podrá acceder normalmente al sistema\n'
                )
            )

        except Exception as e:
            raise CommandError(f'Error al crear el empleado: {str(e)}')
