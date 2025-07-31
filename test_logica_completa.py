import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_rrhh.settings')
django.setup()

from apps.recibos.models import ReciboSueldo
from apps.empleados.models import Empleado

def test_empleado_con_firmados():
    print("=== BUSCANDO EMPLEADO CON RECIBOS FIRMADOS ===\n")
    
    # Buscar empleados con recibos firmados
    empleados_con_firmados = Empleado.objects.filter(
        recibos_sueldo__estado='firmado'
    ).distinct()
    
    if not empleados_con_firmados.exists():
        print("No se encontraron empleados con recibos firmados")
        
        # Buscar el primer empleado y firmar algunos de sus recibos para la prueba
        empleado = Empleado.objects.filter(recibos_sueldo__isnull=False).first()
        if empleado:
            print(f"Firmando algunos recibos de {empleado.user.get_full_name()} para la prueba...")
            
            # Firmar los recibos de enero, febrero, marzo y abril
            recibos_a_firmar = ReciboSueldo.objects.filter(
                empleado=empleado,
                periodo__in=['enero', 'febrero', 'marzo', 'abril']
            )
            
            for recibo in recibos_a_firmar:
                recibo.estado = 'firmado'
                recibo.fecha_firma = django.utils.timezone.now()
                recibo.save()
                print(f"  ✅ Firmado: {recibo.get_periodo_display()} {recibo.anio}")
            
            print("\nAhora probando la lógica...")
            test_logica_completa(empleado)
        else:
            print("No se encontraron empleados con recibos")
    else:
        empleado = empleados_con_firmados.first()
        test_logica_completa(empleado)

def test_logica_completa(empleado):
    print(f"\nEmpleado: {empleado.user.get_full_name()} (Legajo: {empleado.legajo})")
    print("-" * 60)
    
    # Obtener todos los recibos del empleado ordenados cronológicamente
    recibos = ReciboSueldo.objects.filter(empleado=empleado).extra(
        select={'orden': 'anio * 100 + CASE '
                       'WHEN periodo = "enero" THEN 1 '
                       'WHEN periodo = "febrero" THEN 2 '
                       'WHEN periodo = "marzo" THEN 3 '
                       'WHEN periodo = "abril" THEN 4 '
                       'WHEN periodo = "mayo" THEN 5 '
                       'WHEN periodo = "junio" THEN 6 '
                       'WHEN periodo = "julio" THEN 7 '
                       'WHEN periodo = "agosto" THEN 8 '
                       'WHEN periodo = "septiembre" THEN 9 '
                       'WHEN periodo = "octubre" THEN 10 '
                       'WHEN periodo = "noviembre" THEN 11 '
                       'WHEN periodo = "diciembre" THEN 12 '
                       'WHEN periodo = "sac_1" THEN 13 '
                       'WHEN periodo = "sac_2" THEN 14 '
                       'ELSE 0 END'}
    ).order_by('orden')
    
    print("TODOS LOS RECIBOS (orden cronológico):")
    for recibo in recibos:
        tipo_display = recibo.get_tipo_recibo_display()
        periodo_display = recibo.get_periodo_display()
        puede_ver = recibo.puede_ver
        puede_firmar = recibo.puede_firmar
        
        status = "✅" if puede_ver else "❌"
        firmar_status = "🖊️" if puede_firmar else "🚫"
        estado_icon = "✅" if recibo.estado == 'firmado' else "⏳"
        
        print(f"{status} {firmar_status} {estado_icon} {tipo_display} - {periodo_display} {recibo.anio} ({recibo.estado})")
    
    print("\n" + "="*60)
    
    # Análisis
    recibos_firmados = recibos.filter(estado='firmado')
    recibos_pendientes = recibos.filter(estado='pendiente')
    recibos_sac = recibos.filter(periodo__in=['sac_1', 'sac_2'])
    
    print(f"\nANÁLISIS:")
    print(f"- Total recibos: {recibos.count()}")
    print(f"- Recibos firmados: {recibos_firmados.count()}")
    print(f"- Recibos pendientes: {recibos_pendientes.count()}")
    print(f"- Recibos SAC: {recibos_sac.count()}")
    
    # Verificaciones específicas
    print(f"\nVERIFICACIONES:")
    
    # 1. Todos los firmados deben ser visibles
    firmados_visibles = [r for r in recibos_firmados if r.puede_ver]
    print(f"✅ Firmados visibles: {len(firmados_visibles)}/{recibos_firmados.count()}")
    
    # 2. Todos los SAC deben ser visibles
    sac_visibles = [r for r in recibos_sac if r.puede_ver]
    print(f"✅ SAC visibles: {len(sac_visibles)}/{recibos_sac.count()}")
    
    # 3. Verificar lógica secuencial para mensuales
    recibos_mensuales = recibos.filter(tipo_recibo='mensual').order_by('orden')
    print(f"\nLÓGICA SECUENCIAL MENSUAL:")
    for i, recibo in enumerate(recibos_mensuales):
        if i == 0:
            print(f"  📅 {recibo.get_periodo_display()}: PRIMERO → debe ser visible ({'✅' if recibo.puede_ver else '❌'})")
        else:
            anterior = recibos_mensuales[i-1]
            esperado = anterior.estado == 'firmado'
            actual = recibo.puede_ver
            match = "✅" if esperado == actual else "❌"
            print(f"  📅 {recibo.get_periodo_display()}: anterior {anterior.get_periodo_display()} está {'firmado' if anterior.estado == 'firmado' else 'pendiente'} → debe ser {'visible' if esperado else 'bloqueado'} {match}")

if __name__ == "__main__":
    test_empleado_con_firmados()
