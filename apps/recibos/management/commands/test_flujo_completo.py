from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.db import transaction
from io import BytesIO
import base64

from apps.recibos.models import ReciboSueldo, FirmaRecibo
from apps.empleados.models import Empleado, ActividadEmpleado
from apps.rrhh.models import CargaMasivaRecibos, LogProcesamientoRecibo


class Command(BaseCommand):
    help = 'Prueba completa del flujo de recibos: visualización, observación y firma'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando prueba completa del flujo de recibos...'))
        
        try:
            # 1. Buscar empleado con firma
            empleado = Empleado.objects.filter(firma_imagen__isnull=False).first()
            if not empleado:
                self.stdout.write(self.style.ERROR('No se encontró ningún empleado con firma digital'))
                return
            
            # 2. Buscar recibo disponible para el empleado
            recibo = ReciboSueldo.objects.filter(
                empleado=empleado,
                archivo_pdf__isnull=False
            ).exclude(estado='no_encontrado').first()
            
            if not recibo:
                self.stdout.write(self.style.ERROR(f'No se encontró ningún recibo con PDF para el empleado {empleado.legajo}'))
                return
            
            self.stdout.write(f'📋 Empleado: {empleado.user.get_full_name()} (Legajo: {empleado.legajo})')
            self.stdout.write(f'📄 Recibo: {recibo.get_periodo_display()} {recibo.anio}')
            self.stdout.write(f'📊 Estado inicial: {recibo.estado}')
            
            # 3. Verificar propiedades del recibo
            self.stdout.write('\\n🔍 Verificando propiedades del recibo:')
            self.stdout.write(f'  - Puede ver: {recibo.puede_ver}')
            self.stdout.write(f'  - Puede observar: {recibo.puede_observar}')
            self.stdout.write(f'  - Puede firmar: {recibo.puede_firmar}')
            self.stdout.write(f'  - Tiene observaciones pendientes: {recibo.tiene_observaciones_pendientes}')
            
            # 4. Verificar secuencia de recibos
            recibos_anteriores = ReciboSueldo.objects.filter(
                empleado=empleado,
                anio__lt=recibo.anio
            ).exclude(estado='firmado').count()
            
            recibos_periodo_anterior = ReciboSueldo.objects.filter(
                empleado=empleado,
                anio=recibo.anio
            ).exclude(estado='firmado').exclude(id=recibo.id).count()
            
            self.stdout.write(f'  - Recibos anteriores sin firmar: {recibos_anteriores}')
            self.stdout.write(f'  - Recibos del período anterior sin firmar: {recibos_periodo_anterior}')
            
            # 5. Simular observación (si puede observar)
            if recibo.puede_observar and recibo.estado == 'pendiente':
                self.stdout.write('\\n📝 Simulando observación...')
                
                observaciones = "Consulta sobre el descuento de obra social. Favor verificar el monto."
                
                # Actualizar recibo con observación
                recibo.observaciones_empleado = observaciones
                recibo.fecha_observacion = timezone.now()
                recibo.estado = 'observado'
                recibo.save()
                
                self.stdout.write(f'  ✓ Observación registrada: {observaciones}')
                self.stdout.write(f'  ✓ Estado actualizado a: {recibo.estado}')
                
                # Simular respuesta de RRHH
                self.stdout.write('\\n💼 Simulando respuesta de RRHH...')
                recibo.respuesta_rrhh = "El descuento corresponde a la obra social según la categoría del empleado. Monto correcto."
                recibo.fecha_respuesta = timezone.now()
                recibo.estado = 'respondido'
                recibo.save()
                
                self.stdout.write(f'  ✓ Respuesta de RRHH: {recibo.respuesta_rrhh}')
                self.stdout.write(f'  ✓ Estado actualizado a: {recibo.estado}')
            
            # 6. Verificar que ahora puede firmar
            recibo.refresh_from_db()
            if recibo.puede_firmar:
                self.stdout.write('\\n✍️ Simulando firma del recibo...')
                
                # Simular proceso de firma
                tipo_firma = 'observado' if recibo.estado == 'respondido' else 'conforme'
                
                # Generar PDF firmado
                from apps.recibos.views import generar_pdf_firmado_sobre_original
                
                observaciones_para_pdf = recibo.observaciones_empleado if recibo.observaciones_empleado else ''
                pdf_firmado = generar_pdf_firmado_sobre_original(
                    recibo, 
                    empleado, 
                    tipo_firma, 
                    observaciones_para_pdf
                )
                
                if pdf_firmado:
                    # Simular guardado del PDF firmado
                    pdf_filename = f"recibo_firmado_{recibo.periodo}_{recibo.anio}_{empleado.legajo}.pdf"
                    
                    self.stdout.write(f'  ✓ PDF firmado generado ({len(pdf_firmado)} bytes)')
                    self.stdout.write(f'  ✓ Nombre de archivo: {pdf_filename}')
                    
                    # Actualizar estado del recibo
                    recibo.estado = 'firmado'
                    recibo.fecha_firma = timezone.now()
                    recibo.save()
                    
                    # Registrar firma para auditoría
                    FirmaRecibo.objects.create(
                        recibo=recibo,
                        empleado=empleado,
                        ip_address='127.0.0.1',
                        user_agent='Test Command',
                        tipo_firma=tipo_firma,
                        observaciones=observaciones_para_pdf
                    )
                    
                    # Registrar actividad
                    descripcion = f"Firmó el recibo de {recibo.get_periodo_display()} {recibo.anio}"
                    if tipo_firma == 'observado':
                        descripcion += " (con observaciones previas resueltas)"
                    
                    ActividadEmpleado.objects.create(
                        empleado=empleado,
                        descripcion=descripcion
                    )
                    
                    self.stdout.write(f'  ✓ Estado actualizado a: {recibo.estado}')
                    self.stdout.write(f'  ✓ Tipo de firma: {tipo_firma}')
                    self.stdout.write(f'  ✓ Firma registrada en auditoría')
                    self.stdout.write(f'  ✓ Actividad registrada')
                    
                else:
                    self.stdout.write(self.style.ERROR('  ✗ Error al generar PDF firmado'))
            else:
                self.stdout.write(self.style.WARNING('\\n⚠️ El recibo no se puede firmar en este momento'))
                self.stdout.write(f'  - Estado actual: {recibo.estado}')
                self.stdout.write(f'  - Puede firmar: {recibo.puede_firmar}')
            
            # 7. Mostrar resumen final
            self.stdout.write('\\n📊 Resumen final:')
            recibo.refresh_from_db()
            self.stdout.write(f'  - Estado final: {recibo.estado}')
            self.stdout.write(f'  - Fecha de firma: {recibo.fecha_firma}')
            self.stdout.write(f'  - Observaciones: {recibo.observaciones_empleado or "Ninguna"}')
            self.stdout.write(f'  - Respuesta RRHH: {recibo.respuesta_rrhh or "Ninguna"}')
            
            # 8. Verificar registros de auditoría
            firmas = FirmaRecibo.objects.filter(recibo=recibo)
            actividades = ActividadEmpleado.objects.filter(empleado=empleado).order_by('-fecha_creacion')[:5]
            
            self.stdout.write(f'  - Firmas registradas: {firmas.count()}')
            self.stdout.write(f'  - Actividades recientes: {actividades.count()}')
            
            if firmas.exists():
                ultima_firma = firmas.first()
                self.stdout.write(f'  - Última firma: {ultima_firma.fecha_creacion} ({ultima_firma.tipo_firma})')
            
            self.stdout.write(self.style.SUCCESS('\\n✅ Prueba completa del flujo de recibos terminada exitosamente'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error durante la prueba: {str(e)}'))
            import traceback
            traceback.print_exc()
