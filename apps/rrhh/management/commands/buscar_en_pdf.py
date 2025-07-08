from django.core.management.base import BaseCommand
from apps.rrhh.models import CargaMasivaRecibos
from PyPDF2 import PdfReader
import re


class Command(BaseCommand):
    help = 'Busca texto específico en un PDF de carga masiva'

    def add_arguments(self, parser):
        parser.add_argument('--texto', type=str, help='Texto a buscar')
        parser.add_argument('--carga-id', type=int, help='ID de la carga masiva')

    def handle(self, *args, **options):
        texto = options.get('texto')
        carga_id = options.get('carga-id')
        
        if not texto:
            self.stdout.write(self.style.ERROR('Debes especificar el texto con --texto'))
            return
            
        if not carga_id:
            # Buscar la carga más reciente
            carga = CargaMasivaRecibos.objects.all().order_by('-fecha_carga').first()
        else:
            try:
                carga = CargaMasivaRecibos.objects.get(id=carga_id)
            except CargaMasivaRecibos.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'No se encontró la carga #{carga_id}'))
                return
        
        if not carga or not carga.archivo_pdf:
            self.stdout.write(self.style.ERROR('No hay archivo PDF disponible'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'🔍 Buscando "{texto}" en el PDF'))
        self.stdout.write('=' * 60)
        
        try:
            carga.archivo_pdf.seek(0)
            reader = PdfReader(carga.archivo_pdf)
            texto_upper = texto.upper()
            
            coincidencias = []
            
            for i, page in enumerate(reader.pages):
                try:
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    text_upper_page = text.upper()
                    lines = text_upper_page.split('\\n')
                    
                    for j, line in enumerate(lines):
                        if texto_upper in line:
                            coincidencias.append({
                                'pagina': i + 1,
                                'linea': j + 1,
                                'contenido': line.strip()
                            })
                            
                except Exception as e:
                    continue
            
            self.stdout.write(f'📊 Se encontraron {len(coincidencias)} coincidencias')
            
            if coincidencias:
                self.stdout.write(f'\\n✅ Coincidencias encontradas:')
                for idx, match in enumerate(coincidencias[:20]):  # Mostrar máximo 20
                    self.stdout.write(f'   {idx+1}. Página {match["pagina"]}, línea {match["linea"]}:')
                    self.stdout.write(f'      "{match["contenido"]}"')
                    
                if len(coincidencias) > 20:
                    self.stdout.write(f'   ... y {len(coincidencias) - 20} coincidencias más')
            else:
                self.stdout.write(f'\\n❌ No se encontraron coincidencias')
                
                # Sugerir búsquedas alternativas
                if len(texto) > 3:
                    # Buscar partes del texto
                    palabras = texto.split()
                    if len(palabras) > 1:
                        self.stdout.write(f'\\n💡 Prueba buscar palabras individuales:')
                        for palabra in palabras:
                            if len(palabra) > 2:
                                self.stdout.write(f'   python manage.py buscar_en_pdf --texto "{palabra}"')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error analizando PDF: {str(e)}'))
        
        self.stdout.write('\\n✨ Búsqueda completada')
