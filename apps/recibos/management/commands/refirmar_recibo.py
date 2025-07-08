from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.base import ContentFile
from apps.recibos.models import ReciboSueldo
from apps.empleados.models import Empleado
from apps.recibos.views import generar_pdf_firmado_sobre_original


class Command(BaseCommand):
    help = 'Refirma un recibo específico para aplicar mejoras visuales'

    def add_arguments(self, parser):
        parser.add_argument('--recibo-id', type=int, required=True, help='ID del recibo a refirmar')

    def handle(self, *args, **options):
        recibo_id = options['recibo_id']
        
        try:
            recibo = ReciboSueldo.objects.get(id=recibo_id)
            empleado = recibo.empleado
            
            self.stdout.write(self.style.SUCCESS(f'🔄 Refirmando recibo {recibo_id}'))
            self.stdout.write(f'📄 Recibo: {recibo.periodo} {recibo.anio}')
            self.stdout.write(f'👤 Empleado: {empleado.user.get_full_name()} (Legajo: {empleado.legajo})')
            
            if recibo.estado != 'firmado':
                self.stdout.write(self.style.ERROR('❌ El recibo no está firmado'))
                return
            
            # Regenerar PDF firmado con las mejoras visuales
            tipo_firma = 'conforme'
            observaciones = recibo.observaciones_empleado if recibo.observaciones_empleado else ''
            
            pdf_firmado = generar_pdf_firmado_sobre_original(recibo, empleado, tipo_firma, observaciones)
            pdf_filename = f"recibo_firmado_{recibo.periodo}_{recibo.anio}_{empleado.legajo}_updated.pdf"
            
            # Guardar el nuevo PDF
            recibo.archivo_firmado.save(pdf_filename, ContentFile(pdf_firmado), save=True)
            
            self.stdout.write(self.style.SUCCESS(f'✅ Recibo refirmado exitosamente'))
            self.stdout.write(f'📁 Archivo: {pdf_filename}')
            
        except ReciboSueldo.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ No se encontró recibo con ID {recibo_id}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
