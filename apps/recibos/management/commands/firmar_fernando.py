from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.base import ContentFile
from apps.empleados.models import Empleado
from apps.recibos.models import ReciboSueldo, FirmaRecibo
from apps.recibos.views import generar_pdf_firmado_sobre_original, get_client_ip


class Command(BaseCommand):
    help = 'Simula la firma del recibo de Fernando Suárez'

    def handle(self, *args, **options):
        try:
            empleado = Empleado.objects.get(legajo='808')
            recibo = ReciboSueldo.objects.get(id=95)  # Recibo de marzo
            
            self.stdout.write(f'🖋️ Firmando recibo de {empleado.user.get_full_name()}')
            self.stdout.write(f'📄 Período: {recibo.get_periodo_display()} {recibo.anio}')
            self.stdout.write(f'📊 Estado actual: {recibo.estado}')
            
            if not recibo.puede_firmar:
                self.stdout.write(self.style.ERROR('❌ El recibo no se puede firmar en este momento'))
                return
            
            # Simular firma
            tipo_firma = 'conforme'
            observaciones_para_pdf = ''
            
            # Actualizar estado del recibo
            recibo.estado = 'firmado'
            recibo.fecha_firma = timezone.now()
            recibo.save()
            
            # Generar PDF firmado
            self.stdout.write('🔄 Generando PDF firmado...')
            pdf_firmado = generar_pdf_firmado_sobre_original(recibo, empleado, tipo_firma, observaciones_para_pdf)
            
            # Guardar archivo firmado
            pdf_filename = f"recibo_firmado_{recibo.periodo}_{recibo.anio}_{empleado.legajo}.pdf"
            recibo.archivo_firmado.save(pdf_filename, ContentFile(pdf_firmado), save=True)
            
            # Registrar firma para auditoría
            FirmaRecibo.objects.create(
                recibo=recibo,
                empleado=empleado,
                ip_address='127.0.0.1',  # IP simulada
                user_agent='Test Command',
                tipo_firma=tipo_firma,
                observaciones=observaciones_para_pdf
            )
            
            self.stdout.write(self.style.SUCCESS('✅ Recibo firmado exitosamente'))
            self.stdout.write(f'📁 Archivo firmado: {recibo.archivo_firmado.name}')
            self.stdout.write(f'📅 Fecha de firma: {recibo.fecha_firma}')
            
        except Empleado.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ No se encontró empleado con legajo 808'))
        except ReciboSueldo.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ No se encontró el recibo de marzo'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
