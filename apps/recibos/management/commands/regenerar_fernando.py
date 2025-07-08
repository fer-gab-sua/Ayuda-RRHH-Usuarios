from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.base import ContentFile
from apps.empleados.models import Empleado
from apps.recibos.models import ReciboSueldo, FirmaRecibo
from apps.recibos.views import generar_pdf_firmado_sobre_original


class Command(BaseCommand):
    help = 'Regenera el PDF firmado de Fernando Suárez con imagen'

    def handle(self, *args, **options):
        try:
            empleado = Empleado.objects.get(legajo='808')
            recibo = ReciboSueldo.objects.get(id=95)  # Recibo de marzo
            
            self.stdout.write(f'🔄 Regenerando PDF firmado de {empleado.user.get_full_name()}')
            self.stdout.write(f'📄 Período: {recibo.get_periodo_display()} {recibo.anio}')
            
            # Generar PDF firmado con la función corregida
            tipo_firma = 'conforme'
            observaciones_para_pdf = ''
            
            self.stdout.write('🖋️ Generando PDF firmado con imagen...')
            pdf_firmado = generar_pdf_firmado_sobre_original(recibo, empleado, tipo_firma, observaciones_para_pdf)
            
            # Guardar archivo firmado
            pdf_filename = f"recibo_firmado_{recibo.periodo}_{recibo.anio}_{empleado.legajo}_v2.pdf"
            recibo.archivo_firmado.save(pdf_filename, ContentFile(pdf_firmado), save=True)
            
            self.stdout.write(self.style.SUCCESS('✅ PDF regenerado exitosamente'))
            self.stdout.write(f'📁 Archivo firmado: {recibo.archivo_firmado.name}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
