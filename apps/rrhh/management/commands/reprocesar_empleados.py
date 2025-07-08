from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.base import ContentFile
from io import BytesIO
import re
from PyPDF2 import PdfReader, PdfWriter

from apps.empleados.models import Empleado
from apps.recibos.models import ReciboSueldo
from apps.rrhh.models import CargaMasivaRecibos, LogProcesamientoRecibo


class Command(BaseCommand):
    help = 'Reprocesa empleados específicos que no fueron encontrados en una carga masiva'

    def add_arguments(self, parser):
        parser.add_argument('--carga-id', type=int, required=True, help='ID de la carga masiva a reprocesar')
        parser.add_argument('--legajo', type=str, help='Legajo específico a reprocesar (opcional)')

    def handle(self, *args, **options):
        carga_id = options['carga_id']
        legajo_especifico = options.get('legajo')
        
        try:
            carga_masiva = CargaMasivaRecibos.objects.get(id=carga_id)
        except CargaMasivaRecibos.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'No se encontró la carga masiva con ID {carga_id}'))
            return

        self.stdout.write(self.style.SUCCESS(f'🔄 Reprocesando carga masiva #{carga_id}'))
        self.stdout.write(f'📅 Período: {carga_masiva.get_periodo_display()} {carga_masiva.anio}')
        
        # Obtener empleados a reprocesar
        if legajo_especifico:
            try:
                empleado = Empleado.objects.get(legajo=legajo_especifico)
                empleados_a_procesar = [empleado]
                self.stdout.write(f'👤 Reprocesando solo empleado: {empleado.user.get_full_name()} (Legajo: {legajo_especifico})')
            except Empleado.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'No se encontró empleado con legajo {legajo_especifico}'))
                return
        else:
            # Obtener todos los empleados que no fueron encontrados
            logs_no_encontrados = carga_masiva.logs_procesamiento.filter(estado='no_encontrado')
            legajos_no_encontrados = [log.legajo_empleado for log in logs_no_encontrados]
            empleados_a_procesar = Empleado.objects.filter(legajo__in=legajos_no_encontrados)
            self.stdout.write(f'👥 Reprocesando {empleados_a_procesar.count()} empleados no encontrados')

        if not empleados_a_procesar:
            self.stdout.write(self.style.WARNING('No hay empleados para reprocesar'))
            return

        # Procesar cada empleado
        exitos = 0
        errores = 0
        
        for empleado in empleados_a_procesar:
            self.stdout.write(f'\\n🔍 Procesando: {empleado.user.get_full_name()} (Legajo: {empleado.legajo})')
            
            # Verificar si ya existe un recibo para este empleado
            recibo_existente = ReciboSueldo.objects.filter(
                empleado=empleado,
                periodo=carga_masiva.periodo,
                anio=carga_masiva.anio
            ).first()
            
            if recibo_existente:
                self.stdout.write(f'   ⚠️  Ya existe un recibo para este empleado, saltando...')
                continue
            
            # Buscar empleado en el PDF
            paginas_encontradas = self.buscar_empleado_en_pdf(empleado, carga_masiva.archivo_pdf)
            
            if paginas_encontradas is not None:
                # Crear el recibo
                try:
                    recibo = ReciboSueldo.objects.create(
                        empleado=empleado,
                        periodo=carga_masiva.periodo,
                        anio=carga_masiva.anio,
                        fecha_vencimiento=carga_masiva.fecha_vencimiento_calculada,
                        estado='pendiente',
                        subido_por=carga_masiva.usuario_carga
                    )
                    
                    # Generar PDFs individuales
                    if self.generar_pdf_individual_desde_pagina(recibo, carga_masiva.archivo_pdf, paginas_encontradas):
                        exitos += 1
                        pagina_original = paginas_encontradas['pagina_original']
                        pagina_centromedica = paginas_encontradas.get('pagina_centromedica')
                        mensaje_paginas = f'página original {pagina_original + 1}'
                        if pagina_centromedica is not None:
                            mensaje_paginas += f' y página Centromédica {pagina_centromedica + 1}'
                        
                        self.stdout.write(f'   ✅ Recibo generado exitosamente ({mensaje_paginas})')
                        
                        # Actualizar log
                        LogProcesamientoRecibo.objects.create(
                            carga_masiva=carga_masiva,
                            legajo_empleado=empleado.legajo,
                            nombre_empleado=empleado.user.get_full_name(),
                            estado='exitoso',
                            mensaje=f'Recibo generado en reprocesamiento - {mensaje_paginas}'
                        )
                    else:
                        recibo.delete()
                        errores += 1
                        self.stdout.write(f'   ❌ Error al generar PDF individual')
                        
                except Exception as e:
                    errores += 1
                    self.stdout.write(f'   ❌ Error al crear recibo: {str(e)}')
            else:
                errores += 1
                self.stdout.write(f'   ❌ No se encontró en el PDF (verificar nombre exacto)')
        
        # Actualizar estadísticas de la carga
        carga_masiva.recibos_generados += exitos
        carga_masiva.save()
        
        self.stdout.write(f'\\n📊 Resumen del reprocesamiento:')
        self.stdout.write(f'   ✅ Éxitos: {exitos}')
        self.stdout.write(f'   ❌ Errores: {errores}')
        self.stdout.write(f'   📄 Total recibos en carga: {carga_masiva.recibos_generados}')

    def buscar_empleado_en_pdf(self, empleado, archivo_masivo):
        """Busca un empleado específico en el PDF"""
        try:
            archivo_masivo.seek(0)
            reader = PdfReader(archivo_masivo)
            
            empleado_legajo = empleado.legajo
            empleado_apellido = empleado.user.last_name.upper().strip()
            empleado_nombre = empleado.user.first_name.upper().strip()
            
            apellido_nombre_exacto = f"{empleado_apellido}, {empleado_nombre}"
            
            for i, page in enumerate(reader.pages):
                try:
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    text_upper = text.upper()
                    lines = text_upper.split('\\n')
                    
                    # Buscar nombre completo con tolerancia a espacios
                    encontrado_nombre_completo = False
                    linea_nombre = -1
                    
                    for j, line in enumerate(lines):
                        # Búsqueda exacta primero
                        if apellido_nombre_exacto in line:
                            encontrado_nombre_completo = True
                            linea_nombre = j
                            break
                        
                        # Búsqueda tolerante a espacios alrededor de la coma
                        # Normalizar espacios alrededor de la coma
                        line_normalizada = re.sub(r'\s*,\s*', ', ', line)
                        apellido_nombre_normalizado = re.sub(r'\s*,\s*', ', ', apellido_nombre_exacto)
                        
                        if apellido_nombre_normalizado in line_normalizada:
                            encontrado_nombre_completo = True
                            linea_nombre = j
                            self.stdout.write(f'   📝 Encontrado con espacios normalizados: "{line.strip()}"')
                            break
                    
                    if not encontrado_nombre_completo:
                        continue
                    
                    # Buscar legajo con mayor tolerancia
                    legajo_encontrado = False
                    self.stdout.write(f'   🔍 Buscando legajo "{empleado_legajo}" cerca de la línea {linea_nombre}')
                    
                    for k in range(linea_nombre, min(linea_nombre + 5, len(lines))):  # Expandir búsqueda a 5 líneas
                        line = lines[k]
                        self.stdout.write(f'   📝 Línea {k}: "{line.strip()}"')
                        
                        # Método 1: Después de un CUIL (patrón: XX-XXXXXXXX-X LEGAJO)
                        cuil_legajo_pattern = rf"(\\d{{2}}-\\d{{7,8}}-\\d)\\s+{re.escape(empleado_legajo)}(\\s|$)"
                        if re.search(cuil_legajo_pattern, line):
                            legajo_encontrado = True
                            self.stdout.write(f'   ✅ Legajo encontrado después de CUIL: "{line.strip()}"')
                            break
                        
                        # Método 2: Como número aislado (más tolerante)
                        legajo_patterns = [
                            rf"(^|\\s){re.escape(empleado_legajo)}(\\s|$)",  # Exacto con espacios
                            rf"(^|\\s){re.escape(empleado_legajo)}(\\D|$)",  # Exacto seguido de no-dígito
                            rf"\\s{re.escape(empleado_legajo)}\\s",  # Rodeado de espacios
                            rf"\\s+{re.escape(empleado_legajo)}$",  # Al final de línea con espacios
                        ]
                        
                        for pattern in legajo_patterns:
                            if re.search(pattern, line):
                                # Verificación adicional: asegurarse que no es parte de un CUIL u otro número
                                if not re.search(rf"\\d-{re.escape(empleado_legajo)}-\\d", line):  # No es parte de un CUIL
                                    legajo_encontrado = True
                                    self.stdout.write(f'   ✅ Legajo encontrado como número aislado: "{line.strip()}"')
                                    break
                        
                        if legajo_encontrado:
                            break
                    
                    if legajo_encontrado:
                        pagina_centromedica = i + 1 if i + 1 < len(reader.pages) else None
                        return {
                            'pagina_original': i,
                            'pagina_centromedica': pagina_centromedica
                        }
                        
                except Exception as e:
                    continue
            
            return None
            
        except Exception as e:
            return None

    def generar_pdf_individual_desde_pagina(self, recibo, archivo_masivo, paginas_info):
        """Genera PDFs individuales"""
        try:
            archivo_masivo.seek(0)
            reader = PdfReader(archivo_masivo)
            
            pagina_original = paginas_info['pagina_original']
            pagina_centromedica = paginas_info['pagina_centromedica']
            
            if pagina_original >= len(reader.pages):
                return False
            
            # Generar PDF original
            writer_original = PdfWriter()
            writer_original.add_page(reader.pages[pagina_original])
            
            output_buffer_original = BytesIO()
            writer_original.write(output_buffer_original)
            output_buffer_original.seek(0)
            
            nombre_archivo_original = f"recibo_original_{recibo.empleado.legajo}_{recibo.periodo}_{recibo.anio}.pdf"
            recibo.archivo_pdf.save(
                nombre_archivo_original,
                ContentFile(output_buffer_original.getvalue()),
                save=True
            )
            output_buffer_original.close()
            
            # Generar PDF de Centromédica si existe
            if pagina_centromedica is not None and pagina_centromedica < len(reader.pages):
                writer_centromedica = PdfWriter()
                writer_centromedica.add_page(reader.pages[pagina_centromedica])
                
                output_buffer_centromedica = BytesIO()
                writer_centromedica.write(output_buffer_centromedica)
                output_buffer_centromedica.seek(0)
                
                nombre_archivo_centromedica = f"recibo_centromedica_{recibo.empleado.legajo}_{recibo.periodo}_{recibo.anio}.pdf"
                recibo.archivo_pdf_centromedica.save(
                    nombre_archivo_centromedica,
                    ContentFile(output_buffer_centromedica.getvalue()),
                    save=True
                )
                output_buffer_centromedica.close()
            
            return True
            
        except Exception as e:
            return False
