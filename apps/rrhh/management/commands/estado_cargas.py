from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.rrhh.models import CargaMasivaRecibos, LogProcesamientoRecibo
from apps.recibos.models import ReciboSueldo


class Command(BaseCommand):
    help = 'Verifica el estado de las cargas masivas más recientes'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('📋 Estado de las cargas masivas de recibos'))
        self.stdout.write('=' * 60)
        
        # Obtener las cargas más recientes
        cargas = CargaMasivaRecibos.objects.all().order_by('-fecha_carga')[:5]
        
        if not cargas:
            self.stdout.write(self.style.WARNING('No se encontraron cargas masivas'))
            return
        
        for carga in cargas:
            self.stdout.write(f'\\n🗂️  Carga #{carga.id}')
            self.stdout.write(f'   📅 Fecha: {carga.fecha_carga.strftime("%d/%m/%Y %H:%M")}')
            self.stdout.write(f'   📝 Período: {carga.get_periodo_display()} {carga.anio}')
            self.stdout.write(f'   📊 Estado: {carga.get_estado_display()}')
            self.stdout.write(f'   👥 Total empleados: {carga.total_empleados}')
            self.stdout.write(f'   ✅ Recibos generados: {carga.recibos_generados}')
            self.stdout.write(f'   ✔️  Validado: {"Sí" if carga.validado else "No"}')
            self.stdout.write(f'   👁️  Visible para empleados: {"Sí" if carga.visible_empleados else "No"}')
            
            # Mostrar logs de procesamiento
            logs = carga.logs_procesamiento.all()[:10]
            if logs:
                self.stdout.write(f'   📋 Logs de procesamiento (últimos 10):')
                for log in logs:
                    icon = '✅' if log.estado == 'exitoso' else '❌' if log.estado == 'error' else '⚠️'
                    self.stdout.write(f'      {icon} {log.nombre_empleado} (Legajo: {log.legajo_empleado})')
                    self.stdout.write(f'         {log.mensaje}')
            
            # Contar recibos por estado
            recibos = ReciboSueldo.objects.filter(
                periodo=carga.periodo,
                anio=carga.anio,
                subido_por=carga.usuario_carga
            )
            
            estados = {}
            for recibo in recibos:
                estado = recibo.estado
                if estado not in estados:
                    estados[estado] = 0
                estados[estado] += 1
            
            if estados:
                self.stdout.write(f'   📊 Recibos por estado:')
                for estado, count in estados.items():
                    self.stdout.write(f'      • {estado}: {count}')
            
            # Mostrar errores si los hay
            if carga.errores_procesamiento:
                self.stdout.write(f'   ⚠️  Errores:')
                errores = carga.errores_procesamiento.split('\\n')[:5]
                for error in errores:
                    if error.strip():
                        self.stdout.write(f'      • {error.strip()}')
            
            self.stdout.write('-' * 60)
        
        # Resumen general
        self.stdout.write('\\n📊 RESUMEN GENERAL:')
        total_recibos = ReciboSueldo.objects.count()
        recibos_pendientes = ReciboSueldo.objects.filter(estado='pendiente').count()
        recibos_firmados = ReciboSueldo.objects.filter(estado='firmado').count()
        recibos_observados = ReciboSueldo.objects.filter(estado='observado').count()
        recibos_no_encontrados = ReciboSueldo.objects.filter(estado='no_encontrado').count()
        
        self.stdout.write(f'   📄 Total recibos: {total_recibos}')
        self.stdout.write(f'   ⏳ Pendientes: {recibos_pendientes}')
        self.stdout.write(f'   ✅ Firmados: {recibos_firmados}')
        self.stdout.write(f'   💬 Observados: {recibos_observados}')
        self.stdout.write(f'   ❓ No encontrados: {recibos_no_encontrados}')
        
        self.stdout.write('\\n✨ Comando completado exitosamente')
