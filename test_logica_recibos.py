import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_rrhh.settings')
django.setup()

from apps.recibos.models import ReciboSueldo
from apps.empleados.models import Empleado

def test_logica_recibos():
    print("=== TESTING LÓGICA DE RECIBOS ===\n")
    
    # Buscar un empleado con recibos
    empleado = Empleado.objects.filter(recibos_sueldo__isnull=False).first()
    
    if not empleado:
        print("No se encontraron empleados con recibos")
        return
    
    print(f"Empleado: {empleado.user.get_full_name()} (Legajo: {empleado.legajo})")
    print("-" * 50)
    
    # Obtener todos los recibos del empleado
    recibos = ReciboSueldo.objects.filter(empleado=empleado).order_by('anio', 'periodo')
    
    print("TODOS LOS RECIBOS:")
    for recibo in recibos:
        tipo_display = recibo.get_tipo_recibo_display()
        periodo_display = recibo.get_periodo_display()
        puede_ver = recibo.puede_ver
        puede_firmar = recibo.puede_firmar
        
        status = "✅" if puede_ver else "❌"
        firmar_status = "🖊️" if puede_firmar else "🚫"
        
        print(f"{status} {firmar_status} {tipo_display} - {periodo_display} {recibo.anio} ({recibo.estado})")
    
    print("\n" + "="*50)
    
    # Verificar casos específicos
    recibos_firmados = recibos.filter(estado='firmado')
    recibos_pendientes = recibos.filter(estado='pendiente')
    recibos_sac = recibos.filter(tipo_recibo='sac')
    
    print(f"\nRESUMEN:")
    print(f"- Total recibos: {recibos.count()}")
    print(f"- Recibos firmados: {recibos_firmados.count()}")
    print(f"- Recibos pendientes: {recibos_pendientes.count()}")
    print(f"- Recibos SAC: {recibos_sac.count()}")
    
    print(f"\nVERIFICACIONES:")
    
    # Verificar que todos los firmados se pueden ver
    firmados_visibles = sum(1 for r in recibos_firmados if r.puede_ver)
    print(f"- Firmados visibles: {firmados_visibles}/{recibos_firmados.count()}")
    
    # Verificar SAC visibles
    sac_visibles = sum(1 for r in recibos_sac if r.puede_ver)
    print(f"- SAC visibles: {sac_visibles}/{recibos_sac.count()}")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    test_logica_recibos()
