from django.core.management.base import BaseCommand
from PyPDF2 import PdfReader
from apps.rrhh.models import CargaMasivaRecibos
import re


class Command(BaseCommand):
    help = 'Analiza detalladamente un PDF buscando un empleado específico'

    def add_arguments(self, parser):
        parser.add_argument('--carga-id', type=int, required=True, help='ID de la carga masiva')
        parser.add_argument('--buscar', type=str, required=True, help='Texto a buscar en el PDF')

    def handle(self, *args, **options):
        carga_id = options['carga_id']
        texto_buscar = options['buscar'].upper()
        
        try:
            carga_masiva = CargaMasivaRecibos.objects.get(id=carga_id)
        except CargaMasivaRecibos.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'No se encontró la carga masiva con ID {carga_id}'))
            return

        self.stdout.write(self.style.SUCCESS(f'🔍 Analizando PDF de la carga #{carga_id}'))
        self.stdout.write(f'🔎 Buscando: "{texto_buscar}"')
        
        try:
            archivo_pdf = carga_masiva.archivo_pdf
            archivo_pdf.seek(0)
            reader = PdfReader(archivo_pdf)
            
            total_paginas = len(reader.pages)
            self.stdout.write(f'📄 Total de páginas: {total_paginas}')
            
            coincidencias = []
            
            for i, page in enumerate(reader.pages):
                try:
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    text_upper = text.upper()
                    lines = text_upper.split('\\n')
                    
                    # Buscar líneas que contengan el texto
                    for j, line in enumerate(lines):
                        if texto_buscar in line:
                            coincidencias.append({
                                'pagina': i + 1,
                                'linea': j + 1,
                                'contenido': line.strip()
                            })
                            
                            # Mostrar también las líneas anteriores y posteriores para contexto
                            contexto_inicio = max(0, j - 2)
                            contexto_fin = min(len(lines), j + 3)
                            
                            self.stdout.write(f'\\n✅ Encontrado en página {i + 1}, línea {j + 1}:')
                            self.stdout.write('-' * 50)
                            for k in range(contexto_inicio, contexto_fin):
                                if k < len(lines):
                                    marcador = '>>> ' if k == j else '    '
                                    self.stdout.write(f'{marcador}{lines[k].strip()}')
                            self.stdout.write('-' * 50)
                    
                except Exception as e:
                    self.stdout.write(f'❌ Error procesando página {i + 1}: {str(e)}')
                    continue
            
            if not coincidencias:
                self.stdout.write(self.style.WARNING(f'❌ No se encontró "{texto_buscar}" en ninguna página'))
                
                # Intentar búsquedas más amplias
                self.stdout.write('\\n🔍 Intentando búsquedas alternativas...')
                
                palabras = texto_buscar.split()
                for palabra in palabras:
                    if len(palabra) > 3:  # Solo palabras significativas
                        self.stdout.write(f'\\n🔎 Buscando solo "{palabra}":')
                        encontrado = False
                        for i, page in enumerate(reader.pages):
                            try:
                                text = page.extract_text()
                                if text and palabra in text.upper():
                                    if not encontrado:
                                        self.stdout.write(f'   ✅ Encontrado en páginas: ', end='')
                                        encontrado = True
                                    self.stdout.write(f'{i + 1} ', end='')
                            except:
                                continue
                        if encontrado:
                            self.stdout.write('')  # Nueva línea
                        else:
                            self.stdout.write(f'   ❌ No encontrado')
                            
            else:
                self.stdout.write(f'\\n📊 Total de coincidencias encontradas: {len(coincidencias)}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al analizar el PDF: {str(e)}'))
