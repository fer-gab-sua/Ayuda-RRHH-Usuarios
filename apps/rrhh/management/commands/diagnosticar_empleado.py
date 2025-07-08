from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.rrhh.models import CargaMasivaRecibos, LogProcesamientoRecibo
from apps.recibos.models import ReciboSueldo
from apps.empleados.models import Empleado
from PyPDF2 import PdfReader
import re


class Command(BaseCommand):
    help = 'Diagnostica por qué un empleado específico no se encuentra en el PDF'

    def add_arguments(self, parser):
        parser.add_argument('--legajo', type=str, help='Legajo del empleado a diagnosticar')
        parser.add_argument('--carga-id', type=int, help='ID de la carga masiva')

    def handle(self, *args, **options):
        legajo = options.get('legajo')
        carga_id = options.get('carga-id')
        
        if not legajo:
            self.stdout.write(self.style.ERROR('Debes especificar el legajo con --legajo'))
            return
            
        if not carga_id:
            # Buscar la carga más reciente
            carga = CargaMasivaRecibos.objects.all().order_by('-fecha_carga').first()
            if not carga:
                self.stdout.write(self.style.ERROR('No se encontraron cargas masivas'))
                return
        else:
            try:
                carga = CargaMasivaRecibos.objects.get(id=carga_id)
            except CargaMasivaRecibos.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'No se encontró la carga #{carga_id}'))
                return
        
        # Buscar empleado
        try:
            empleado = Empleado.objects.get(legajo=legajo)
        except Empleado.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'No se encontró empleado con legajo {legajo}'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'🔍 Diagnóstico para empleado: {empleado.user.get_full_name()}'))
        self.stdout.write('=' * 60)
        
        self.stdout.write(f'📋 Datos del empleado:')
        self.stdout.write(f'   Legajo: {empleado.legajo}')
        self.stdout.write(f'   Nombre: {empleado.user.first_name}')
        self.stdout.write(f'   Apellido: {empleado.user.last_name}')
        self.stdout.write(f'   Nombre completo: {empleado.user.get_full_name()}')
        
        self.stdout.write(f'\\n📄 Datos de la carga:')
        self.stdout.write(f'   ID: {carga.id}')
        self.stdout.write(f'   Período: {carga.get_periodo_display()} {carga.anio}')
        self.stdout.write(f'   Archivo: {carga.archivo_pdf.name if carga.archivo_pdf else "No disponible"}')
        
        # Analizar el PDF
        if not carga.archivo_pdf:
            self.stdout.write(self.style.ERROR('No hay archivo PDF en la carga'))
            return
            
        try:
            carga.archivo_pdf.seek(0)
            reader = PdfReader(carga.archivo_pdf)
            total_pages = len(reader.pages)
            
            self.stdout.write(f'\\n📖 Analizando PDF:')
            self.stdout.write(f'   Total de páginas: {total_pages}')
            
            # Preparar datos de búsqueda
            empleado_legajo = empleado.legajo
            empleado_apellido = empleado.user.last_name.upper().strip() if empleado.user.last_name else ""
            empleado_nombre = empleado.user.first_name.upper().strip() if empleado.user.first_name else ""
            apellido_nombre_exacto = f"{empleado_apellido}, {empleado_nombre}"
            
            self.stdout.write(f'\\n🔍 Buscando patrones:')
            self.stdout.write(f'   Patrón exacto: "{apellido_nombre_exacto}"')
            self.stdout.write(f'   Legajo: "{empleado_legajo}"')
            
            # Buscar en todas las páginas
            coincidencias_nombre = []
            coincidencias_legajo = []
            paginas_con_contenido = []
            
            for i, page in enumerate(reader.pages):
                try:
                    text = page.extract_text()
                    if not text:
                        continue
                        
                    paginas_con_contenido.append(i)
                    text_upper = text.upper()
                    lines = text_upper.split('\\n')
                    
                    # Buscar nombre exacto
                    for j, line in enumerate(lines):
                        if apellido_nombre_exacto in line:
                            coincidencias_nombre.append({
                                'pagina': i + 1,
                                'linea': j,
                                'contenido': line.strip()
                            })
                    
                    # Buscar legajo
                    for j, line in enumerate(lines):
                        # Buscar legajo después de CUIL
                        cuil_legajo_pattern = rf"(\\d{{2}}-\\d{{7,8}}-\\d)\\s+{re.escape(empleado_legajo)}(\\s|$)"
                        if re.search(cuil_legajo_pattern, line):
                            coincidencias_legajo.append({
                                'pagina': i + 1,
                                'linea': j,
                                'contenido': line.strip(),
                                'tipo': 'CUIL+Legajo'
                            })
                        
                        # Buscar legajo aislado
                        legajo_aislado_pattern = rf"(^|\\s){re.escape(empleado_legajo)}(\\s|$)"
                        if re.search(legajo_aislado_pattern, line):
                            if not re.search(rf"\\d-{re.escape(empleado_legajo)}-\\d", line):
                                coincidencias_legajo.append({
                                    'pagina': i + 1,
                                    'linea': j,
                                    'contenido': line.strip(),
                                    'tipo': 'Aislado'
                                })
                
                except Exception as e:
                    self.stdout.write(f'   ⚠️ Error en página {i+1}: {str(e)}')
            
            self.stdout.write(f'\\n📊 Resultados del análisis:')
            self.stdout.write(f'   Páginas con contenido: {len(paginas_con_contenido)}')
            self.stdout.write(f'   Coincidencias de nombre: {len(coincidencias_nombre)}')
            self.stdout.write(f'   Coincidencias de legajo: {len(coincidencias_legajo)}')
            
            if coincidencias_nombre:
                self.stdout.write(f'\\n✅ Coincidencias de nombre encontradas:')
                for match in coincidencias_nombre[:5]:
                    self.stdout.write(f'   📄 Página {match["pagina"]}, línea {match["linea"]}:')
                    self.stdout.write(f'      "{match["contenido"]}"')
            else:
                self.stdout.write(f'\\n❌ No se encontraron coincidencias exactas del nombre')
                # Buscar nombres similares
                self.stdout.write(f'\\n🔍 Buscando nombres similares...')
                nombres_similares = []
                
                for i, page in enumerate(reader.pages[:10]):  # Solo primeras 10 páginas
                    try:
                        text = page.extract_text()
                        if not text:
                            continue
                        lines = text.upper().split('\\n')
                        
                        for line in lines:
                            # Buscar apellido solo
                            if empleado_apellido in line and len(empleado_apellido) > 3:
                                nombres_similares.append({
                                    'pagina': i + 1,
                                    'contenido': line.strip()
                                })
                    except:
                        continue
                
                if nombres_similares:
                    self.stdout.write(f'   🔍 Líneas que contienen el apellido "{empleado_apellido}":')
                    for match in nombres_similares[:5]:
                        self.stdout.write(f'      Página {match["pagina"]}: "{match["contenido"]}"')
            
            if coincidencias_legajo:
                self.stdout.write(f'\\n✅ Coincidencias de legajo encontradas:')
                for match in coincidencias_legajo[:5]:
                    self.stdout.write(f'   📄 Página {match["pagina"]}, línea {match["linea"]} ({match["tipo"]}):')
                    self.stdout.write(f'      "{match["contenido"]}"')
            else:
                self.stdout.write(f'\\n❌ No se encontraron coincidencias del legajo')
            
            # Verificar lógica de coincidencia
            self.stdout.write(f'\\n🔬 Análisis de la lógica de búsqueda:')
            
            if len(empleado_apellido) < 3 or len(empleado_nombre) < 3:
                self.stdout.write(f'   ⚠️ PROBLEMA: Nombre o apellido demasiado corto')
                self.stdout.write(f'      Apellido: "{empleado_apellido}" (longitud: {len(empleado_apellido)})')
                self.stdout.write(f'      Nombre: "{empleado_nombre}" (longitud: {len(empleado_nombre)})')
            
            if coincidencias_nombre and coincidencias_legajo:
                self.stdout.write(f'   ✅ Se encontraron tanto nombre como legajo')
                self.stdout.write(f'   ℹ️ El empleado DEBERÍA haber sido encontrado')
            elif coincidencias_nombre and not coincidencias_legajo:
                self.stdout.write(f'   ⚠️ Se encontró el nombre pero NO el legajo')
                self.stdout.write(f'   💡 Verifica que el legajo "{empleado_legajo}" esté correcto')
            elif not coincidencias_nombre and coincidencias_legajo:
                self.stdout.write(f'   ⚠️ Se encontró el legajo pero NO el nombre')
                self.stdout.write(f'   💡 Verifica el formato del nombre: "{apellido_nombre_exacto}"')
            else:
                self.stdout.write(f'   ❌ No se encontraron ni nombre ni legajo')
                self.stdout.write(f'   💡 Verifica los datos del empleado y el contenido del PDF')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error analizando PDF: {str(e)}'))
            import traceback
            traceback.print_exc()
        
        self.stdout.write('\\n✨ Diagnóstico completado')
