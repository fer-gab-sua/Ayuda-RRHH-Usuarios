from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.base import ContentFile
from io import BytesIO
import base64

from apps.recibos.models import ReciboSueldo
from apps.empleados.models import Empleado
from apps.recibos.views import generar_pdf_firmado_sobre_original


class Command(BaseCommand):
    help = 'Prueba la función de firma de PDF'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando prueba de firma de PDF...'))
        
        try:
            # Buscar un empleado con firma
            empleado = Empleado.objects.filter(firma_imagen__isnull=False).first()
            if not empleado:
                self.stdout.write(self.style.ERROR('No se encontró ningún empleado con firma digital'))
                return
            
            # Buscar un recibo con PDF original
            recibo = ReciboSueldo.objects.filter(
                empleado=empleado,
                archivo_pdf__isnull=False
            ).first()
            
            if not recibo:
                self.stdout.write(self.style.ERROR(f'No se encontró ningún recibo con PDF original para el empleado {empleado.legajo}'))
                return
            
            self.stdout.write(f'Probando con empleado: {empleado.user.get_full_name()} (Legajo: {empleado.legajo})')
            self.stdout.write(f'Recibo: {recibo.get_periodo_display()} {recibo.anio}')
            
            # Simular observaciones
            observaciones = "Esto es una prueba de observaciones del empleado."
            
            # Generar PDF firmado
            pdf_firmado = generar_pdf_firmado_sobre_original(
                recibo, 
                empleado, 
                'conforme', 
                observaciones
            )
            
            if pdf_firmado:
                # Guardar el PDF de prueba
                pdf_filename = f"test_firmado_{empleado.legajo}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                # Simular guardado (sin guardarlo realmente)
                self.stdout.write(self.style.SUCCESS(f'✓ PDF firmado generado correctamente'))
                self.stdout.write(f'  - Tamaño: {len(pdf_firmado)} bytes')
                self.stdout.write(f'  - Nombre de archivo: {pdf_filename}')
                
                # Verificar que el PDF se puede leer
                try:
                    from PyPDF2 import PdfReader
                    reader = PdfReader(BytesIO(pdf_firmado))
                    num_pages = len(reader.pages)
                    self.stdout.write(f'  - Número de páginas: {num_pages}')
                    
                    # Verificar que la primera página tiene contenido
                    if num_pages > 0:
                        first_page = reader.pages[0]
                        self.stdout.write(f'  - Primera página procesada correctamente')
                        
                except Exception as pdf_error:
                    self.stdout.write(self.style.ERROR(f'Error al verificar el PDF generado: {str(pdf_error)}'))
                    return
                
                self.stdout.write(self.style.SUCCESS('✓ Prueba de firma PDF completada exitosamente'))
                
            else:
                self.stdout.write(self.style.ERROR('Error: La función retornó None'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error durante la prueba: {str(e)}'))
            import traceback
            traceback.print_exc()
