from django.core.management.base import BaseCommand
from apps.recibos.models import ReciboSueldo
from apps.recibos.views import generar_pdf_formato_centromedica_test
from django.core.files.base import ContentFile
import os

# Imports para convertir PDF a imagen
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class Command(BaseCommand):
    help = 'Prueba la generación de PDF con formato profesional de Centromédica'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recibo-id', 
            type=int, 
            help='ID del recibo a usar para la prueba'
        )
        parser.add_argument(
            '--legajo',
            type=str,
            help='Legajo del empleado para buscar un recibo'
        )

    def handle(self, *args, **options):
        try:
            recibo = None
            
            # Buscar recibo por ID si se especifica
            if options['recibo_id']:
                try:
                    recibo = ReciboSueldo.objects.get(id=options['recibo_id'])
                    self.stdout.write(f"Usando recibo ID {options['recibo_id']}")
                except ReciboSueldo.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"No se encontró recibo con ID {options['recibo_id']}"))
                    return
            
            # Buscar recibo por legajo si se especifica
            elif options['legajo']:
                try:
                    recibo = ReciboSueldo.objects.filter(
                        empleado__legajo=options['legajo']
                    ).first()
                    
                    if not recibo:
                        self.stdout.write(self.style.ERROR(f"No se encontró recibo para legajo {options['legajo']}"))
                        return
                    
                    self.stdout.write(f"Usando recibo para legajo {options['legajo']}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error buscando recibo: {str(e)}"))
                    return
            
            # Si no se especifica nada, usar el primer recibo disponible
            else:
                recibo = ReciboSueldo.objects.select_related('empleado', 'empleado__user').first()
                if not recibo:
                    self.stdout.write(self.style.ERROR("No hay recibos disponibles para probar"))
                    return
                
                self.stdout.write(f"Usando primer recibo disponible (ID: {recibo.id})")
            
            # Información del recibo
            empleado = recibo.empleado
            self.stdout.write(f"Empleado: {empleado.user.get_full_name()}")
            self.stdout.write(f"Legajo: {empleado.legajo}")
            self.stdout.write(f"Período: {recibo.get_periodo_display()} {recibo.anio}")
            
            # Generar PDF con formato profesional
            self.stdout.write("Generando PDF con formato profesional...")
            pdf_content = generar_pdf_formato_centromedica_test(recibo, empleado)
            
            if pdf_content:
                # Guardar el PDF de prueba
                filename = f"recibo_formato_test_{empleado.legajo}_{recibo.periodo}_{recibo.anio}.pdf"
                
                # Crear directorio de pruebas si no existe
                test_dir = "media/test_pdfs"
                os.makedirs(test_dir, exist_ok=True)
                
                # Guardar archivo
                filepath = os.path.join(test_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(pdf_content)
                
                self.stdout.write(
                    self.style.SUCCESS(f"PDF de prueba generado exitosamente: {filepath}")
                )
                
                # Mostrar información del archivo
                file_size = len(pdf_content)
                self.stdout.write(f"Tamaño del archivo: {file_size} bytes")
                
                # Convertir PDF a imagen para validación visual
                if PYMUPDF_AVAILABLE:
                    try:
                        self.stdout.write("Convirtiendo PDF a imagen usando PyMuPDF...")
                        
                        # Abrir PDF con PyMuPDF
                        pdf_doc = fitz.open(stream=pdf_content, filetype="pdf")
                        
                        # Convertir primera página a imagen
                        page = pdf_doc[0]
                        mat = fitz.Matrix(2.0, 2.0)  # Factor de escala para mejor calidad
                        pix = page.get_pixmap(matrix=mat)
                        
                        # Guardar como PNG
                        image_filename = filename.replace('.pdf', '.png')
                        image_filepath = os.path.join(test_dir, image_filename)
                        
                        pix.save(image_filepath)
                        pdf_doc.close()
                        
                        self.stdout.write(
                            self.style.SUCCESS(f"Imagen generada exitosamente: {image_filepath}")
                        )
                        
                        # Mostrar información de la imagen
                        image_size = os.path.getsize(image_filepath)
                        self.stdout.write(f"Tamaño de la imagen: {image_size} bytes")
                        self.stdout.write(f"Dimensiones: {pix.width}x{pix.height} pixels")
                        
                    except Exception as img_error:
                        self.stdout.write(
                            self.style.WARNING(f"Error generando imagen con PyMuPDF: {str(img_error)}")
                        )
                        
                elif PDF2IMAGE_AVAILABLE and PIL_AVAILABLE:
                    try:
                        self.stdout.write("Convirtiendo PDF a imagen usando pdf2image...")
                        
                        # Convertir PDF a imagen
                        images = convert_from_bytes(pdf_content, dpi=150, first_page=1, last_page=1)
                        
                        if images:
                            # Guardar la primera página como imagen
                            image_filename = filename.replace('.pdf', '.png')
                            image_filepath = os.path.join(test_dir, image_filename)
                            
                            images[0].save(image_filepath, 'PNG')
                            
                            self.stdout.write(
                                self.style.SUCCESS(f"Imagen generada exitosamente: {image_filepath}")
                            )
                            
                            # Mostrar información de la imagen
                            image_size = os.path.getsize(image_filepath)
                            self.stdout.write(f"Tamaño de la imagen: {image_size} bytes")
                            self.stdout.write(f"Dimensiones: {images[0].size[0]}x{images[0].size[1]} pixels")
                            
                    except Exception as img_error:
                        self.stdout.write(
                            self.style.WARNING(f"Error generando imagen con pdf2image: {str(img_error)}")
                        )
                        self.stdout.write("El PDF se generó correctamente, pero no se pudo crear la imagen.")
                
                else:
                    self.stdout.write(
                        self.style.WARNING("Para generar imágenes, instala: pip install PyMuPDF")
                    )
                    self.stdout.write("Alternativa: pip install pdf2image Pillow (requiere poppler)")
                
                # Opcionalmente, también guardarlo en el modelo para comparar
                # (esto no afecta la lógica existente)
                save_to_model = input("¿Guardar también en el modelo como archivo de prueba? (y/N): ")
                if save_to_model.lower() == 'y':
                    test_filename = f"test_formato_{filename}"
                    
                    # Crear un campo temporal (esto requeriría agregar un campo al modelo)
                    # Por ahora solo lo mencionamos
                    self.stdout.write("Para guardar en el modelo, necesitarías agregar un campo 'archivo_test' al modelo ReciboSueldo")
                
            else:
                self.stdout.write(self.style.ERROR("Error generando el PDF"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error en la prueba: {str(e)}"))
            import traceback
            traceback.print_exc()
