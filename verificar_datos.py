from apps.empleados.models import Empleado
from django.contrib.auth.models import User
from apps.recibos.models import ReciboSueldo
from datetime import datetime, timedelta
from django.utils import timezone

# Verificar empleados
print("Empleados:", Empleado.objects.count())
for e in Empleado.objects.all():
    print(f"- {e.user.username} ({e.user.get_full_name()})")

# Verificar usuarios
print("\nUsuarios:")
for u in User.objects.all():
    print(f"- {u.username} ({u.get_full_name()})")

# Verificar recibos existentes
print("\nRecibos existentes:")
for r in ReciboSueldo.objects.all():
    print(f"- {r}")

# Crear un empleado de ejemplo si no existe
if not Empleado.objects.exists():
    print("\nCreando empleado de ejemplo...")
    user = User.objects.create_user(
        username='empleado1',
        password='test123',
        first_name='Juan',
        last_name='Pérez',
        email='juan@empresa.com'
    )
    empleado = Empleado.objects.create(
        user=user,
        legajo='001',
        dni='12345678',
        fecha_ingreso=timezone.now().date(),
        cargo='Empleado'
    )
    print(f"Empleado creado: {empleado}")
