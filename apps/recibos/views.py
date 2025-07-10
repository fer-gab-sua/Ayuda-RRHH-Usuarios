from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.http import JsonResponse, HttpResponse, Http404
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
from django.core.files.base import ContentFile
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import base64

from .models import ReciboSueldo, FirmaRecibo
from apps.empleados.models import Empleado, ActividadEmpleado


class MisRecibosView(LoginRequiredMixin, ListView):
    """Vista para mostrar los recibos del empleado"""
    model = ReciboSueldo
    template_name = 'recibos/mis_recibos.html'
    context_object_name = 'recibos'
    paginate_by = 10
    
    def get_queryset(self):
        """Obtener todos los recibos del empleado logueado ordenados cronológicamente"""
        try:
            empleado = Empleado.objects.get(user=self.request.user)
            # Obtener todos los recibos del empleado ordenados cronológicamente
            return ReciboSueldo.objects.filter(empleado=empleado).extra(
                select={'orden': 'anio * 100 + CASE '
                               'WHEN periodo = "enero" THEN 1 '
                               'WHEN periodo = "febrero" THEN 2 '
                               'WHEN periodo = "marzo" THEN 3 '
                               'WHEN periodo = "abril" THEN 4 '
                               'WHEN periodo = "mayo" THEN 5 '
                               'WHEN periodo = "junio" THEN 6 '
                               'WHEN periodo = "julio" THEN 7 '
                               'WHEN periodo = "agosto" THEN 8 '
                               'WHEN periodo = "septiembre" THEN 9 '
                               'WHEN periodo = "octubre" THEN 10 '
                               'WHEN periodo = "noviembre" THEN 11 '
                               'WHEN periodo = "diciembre" THEN 12 '
                               'ELSE 0 END'}
            ).order_by('orden')
        except Empleado.DoesNotExist:
            return ReciboSueldo.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener todos los recibos del empleado (que ya están en el queryset)
        todos_recibos = self.get_queryset()
        
        # Estadísticas generales
        context['total_recibos'] = todos_recibos.count()
        context['pendientes'] = todos_recibos.filter(estado='pendiente').count()
        context['observados'] = todos_recibos.filter(estado='observado').count()
        context['respondidos'] = todos_recibos.filter(estado='respondido').count()
        context['firmados'] = todos_recibos.filter(estado='firmado').count()
        context['vencidos'] = todos_recibos.filter(estado='vencido').count()
        
        # Próximo recibo que puede firmar
        puede_firmar = next((r for r in todos_recibos if r.puede_firmar), None)
        context['puede_firmar'] = puede_firmar
        
        # Verificar si hay observaciones pendientes que bloquean el flujo
        tiene_observaciones_pendientes = todos_recibos.filter(estado='observado').exists()
        context['tiene_observaciones_pendientes'] = tiene_observaciones_pendientes
        
        # Información sobre el flujo secuencial
        recibos_visibles = [r for r in todos_recibos if r.puede_ver]
        context['recibos_visibles_count'] = len(recibos_visibles)
        
        if recibos_visibles:
            ultimo_visible = recibos_visibles[-1]
            context['ultimo_recibo_visible'] = ultimo_visible
            
            # Verificar si hay más recibos después del último visible
            context['hay_recibos_bloqueados'] = len(recibos_visibles) < todos_recibos.count()
        
        return context


@login_required
def ver_recibo_pdf(request, recibo_id):
    """Ver el PDF del recibo - muestra el firmado por Centromédica si existe, sino el original"""
    try:
        empleado = Empleado.objects.get(user=request.user)
        recibo = get_object_or_404(ReciboSueldo, id=recibo_id, empleado=empleado)
        
        # Verificar que pueda ver este recibo
        if not recibo.puede_ver:
            messages.error(request, 'No puedes ver este recibo. Debes firmar el recibo anterior primero.')
            return redirect('recibos:mis_recibos')
        
        # Priorizar mostrar el PDF firmado por el empleado si existe, 
        # luego el firmado por Centromédica, y finalmente el original
        archivo_a_mostrar = None
        archivo_tipo = ""
        
        if recibo.estado == 'firmado' and recibo.archivo_firmado:
            archivo_a_mostrar = recibo.archivo_firmado
            archivo_tipo = "firmado por empleado"
            print(f"Mostrando PDF firmado por empleado para {empleado.legajo}")
        elif recibo.archivo_pdf_centromedica:
            archivo_a_mostrar = recibo.archivo_pdf_centromedica
            archivo_tipo = "firmado por Centromédica"
            print(f"Mostrando PDF de Centromédica para {empleado.legajo}")
        elif recibo.archivo_pdf:
            archivo_a_mostrar = recibo.archivo_pdf
            archivo_tipo = "original"
            print(f"Mostrando PDF original para {empleado.legajo}")
        
        if not archivo_a_mostrar:
            raise Http404("Archivo no encontrado")
        
        # Registrar actividad
        ActividadEmpleado.objects.create(
            empleado=empleado,
            descripcion=f"Consultó el recibo de {recibo.get_periodo_display()} {recibo.anio}"
        )
        
        # Leer el contenido del archivo
        try:
            archivo_content = archivo_a_mostrar.read()
        except Exception as e:
            raise Http404(f"Error al leer el archivo: {str(e)}")
        
        response = HttpResponse(archivo_content, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{recibo.nombre_archivo}"'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response
        
    except Empleado.DoesNotExist:
        raise Http404("Empleado no encontrado")


@login_required
def observar_recibo(request, recibo_id):
    """Mostrar formulario para observar recibo"""
    try:
        empleado = Empleado.objects.get(user=request.user)
        recibo = get_object_or_404(ReciboSueldo, id=recibo_id, empleado=empleado)
        
        # Verificar que pueda ver este recibo
        if not recibo.puede_ver:
            messages.error(request, 'No puedes ver este recibo. Debes firmar el recibo anterior primero.')
            return redirect('recibos:mis_recibos')
        
        # Verificar que pueda observar este recibo
        if not recibo.puede_observar:
            messages.error(request, 'No puedes hacer observaciones sobre este recibo en este momento.')
            return redirect('recibos:mis_recibos')
        
        context = {
            'recibo': recibo,
            'empleado': empleado,
        }
        
        return render(request, 'recibos/observar_recibo.html', context)
        
    except Empleado.DoesNotExist:
        raise Http404("Empleado no encontrado")


@login_required
@require_POST
def procesar_observacion_recibo(request, recibo_id):
    """Procesar la observación del recibo"""
    try:
        empleado = Empleado.objects.get(user=request.user)
        recibo = get_object_or_404(ReciboSueldo, id=recibo_id, empleado=empleado)
        
        if not recibo.puede_observar:
            return JsonResponse({
                'success': False,
                'message': 'No puedes hacer observaciones sobre este recibo en este momento.'
            })
        
        observaciones = request.POST.get('observaciones', '').strip()
        if not observaciones:
            return JsonResponse({
                'success': False,
                'message': 'Debes ingresar una observación.'
            })
        
        # Actualizar el recibo con la observación
        recibo.observaciones_empleado = observaciones
        recibo.fecha_observacion = timezone.now()
        recibo.estado = 'observado'
        recibo.save()
        
        # Registrar actividad
        ActividadEmpleado.objects.create(
            empleado=empleado,
            descripcion=f"Realizó observaciones sobre el recibo de {recibo.get_periodo_display()} {recibo.anio}"
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Observación enviada correctamente. RRHH revisará tu consulta.'
        })
        
    except Empleado.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Empleado no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al procesar la observación: {str(e)}'
        })


@login_required
def firmar_recibo(request, recibo_id):
    """Mostrar formulario para firmar recibo"""
    try:
        empleado = Empleado.objects.get(user=request.user)
        recibo = get_object_or_404(ReciboSueldo, id=recibo_id, empleado=empleado)
        
        # Verificar que pueda ver este recibo
        if not recibo.puede_ver:
            messages.error(request, 'No puedes ver este recibo. Debes firmar el recibo anterior primero.')
            return redirect('recibos:mis_recibos')
        
        # Verificar que pueda firmar este recibo
        if not recibo.puede_firmar:
            # Verificar si hay observaciones pendientes
            if empleado.recibos_sueldo.filter(estado='observado').exists():
                messages.error(request, 'No puedes firmar recibos mientras tengas observaciones pendientes de respuesta.')
            else:
                messages.error(request, 'Este recibo no puede ser firmado en este momento.')
            return redirect('recibos:mis_recibos')
        
        # Verificar que tenga firma digital
        if not empleado.firma_imagen:
            messages.error(request, 'Debes crear tu firma digital antes de firmar recibos.')
            return redirect('empleados:crear_firma')
        
        context = {
            'recibo': recibo,
            'empleado': empleado,
        }
        
        return render(request, 'recibos/firmar_recibo.html', context)
        
    except Empleado.DoesNotExist:
        raise Http404("Empleado no encontrado")


@login_required
@require_POST
def procesar_firma_recibo(request, recibo_id):
    """Procesar la firma del recibo"""
    try:
        empleado = Empleado.objects.get(user=request.user)
        recibo = get_object_or_404(ReciboSueldo, id=recibo_id, empleado=empleado)
        
        if not recibo.puede_firmar:
            return JsonResponse({
                'success': False,
                'message': 'Este recibo no puede ser firmado en este momento.'
            })
        
        # Verificar que tenga firma digital
        if not empleado.firma_imagen:
            return JsonResponse({
                'success': False,
                'message': 'Debes crear tu firma digital antes de firmar recibos.'
            })
        
        # Validar PIN
        pin_ingresado = request.POST.get('pin_firma')
        if not pin_ingresado:
            return JsonResponse({
                'success': False,
                'message': 'Debes ingresar tu PIN de firma digital.'
            })
        
        if empleado.firma_pin != pin_ingresado:
            return JsonResponse({
                'success': False,
                'message': 'PIN incorrecto. Verifica tu PIN de firma digital.'
            })
        
        # Tipo de firma (siempre conforme, pero puede haber sido observado previamente)
        tipo_firma = 'observado' if recibo.estado == 'respondido' else 'conforme'
        
        # Actualizar estado del recibo (siempre firmado, sin disconformidad)
        recibo.estado = 'firmado'
        recibo.fecha_firma = timezone.now()
        recibo.save()
        
        # Generar PDF firmado usando el PDF original
        try:
            # Las observaciones vienen del recibo si fue observado previamente
            observaciones_para_pdf = recibo.observaciones_empleado if recibo.observaciones_empleado else ''
            pdf_firmado = generar_pdf_firmado_sobre_original(recibo, empleado, tipo_firma, observaciones_para_pdf)
            pdf_filename = f"recibo_firmado_{recibo.periodo}_{recibo.anio}_{empleado.legajo}.pdf"
            recibo.archivo_firmado.save(pdf_filename, ContentFile(pdf_firmado), save=True)
        except Exception as e:
            print(f"Error al generar PDF firmado: {str(e)}")
        
        # Registrar firma para auditoría
        FirmaRecibo.objects.create(
            recibo=recibo,
            empleado=empleado,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
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
        
        mensaje_success = 'Recibo firmado correctamente.'
        if tipo_firma == 'observado':
            mensaje_success += ' Las observaciones previas fueron consideradas.'
        
        return JsonResponse({
            'success': True,
            'message': mensaje_success
        })
        
    except Empleado.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Empleado no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al procesar la firma: {str(e)}'
        })


@login_required
def visualizar_recibo(request, recibo_id):
    """Vista para visualizar recibo con opciones de firmar y observar"""
    try:
        empleado = Empleado.objects.get(user=request.user)
        recibo = get_object_or_404(ReciboSueldo, id=recibo_id, empleado=empleado)
        
        if not recibo.puede_ver:
            messages.error(request, 'No tienes permiso para ver este recibo.')
            return redirect('recibos:mis_recibos')
        
        # Registrar actividad
        ActividadEmpleado.objects.create(
            empleado=empleado,
            descripcion=f"Visualizó el recibo de {recibo.get_periodo_display()} {recibo.anio}"
        )
        
        context = {
            'recibo': recibo,
            'empleado': empleado,
            'puede_firmar': recibo.puede_firmar,
            'puede_observar': recibo.puede_observar,
            'tiene_observaciones_pendientes': recibo.tiene_observaciones_pendientes,
            'empleado_tiene_observaciones_pendientes': recibo.empleado_tiene_observaciones_pendientes(),
        }
        
        return render(request, 'recibos/visualizar_recibo.html', context)
        
    except Empleado.DoesNotExist:
        raise Http404("Empleado no encontrado")


def generar_pdf_firmado(recibo, empleado, tipo_firma, observaciones):
    """Generar PDF del recibo con firma digital"""
    buffer = BytesIO()
    
    # Crear documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    story.append(Paragraph("RECIBO DE SUELDO", title_style))
    story.append(Spacer(1, 20))
    
    # Información del empleado
    emp_info = [
        ['Empleado:', f"{empleado.user.get_full_name()}"],
        ['Legajo:', empleado.legajo],
        ['Período:', f"{recibo.get_periodo_display()} {recibo.anio}"],
        ['Fecha de Emisión:', recibo.fecha_emision.strftime('%d/%m/%Y')],
        ['Fecha de Firma:', recibo.fecha_firma.strftime('%d/%m/%Y %H:%M') if recibo.fecha_firma else 'No firmado'],
    ]
    
    emp_table = Table(emp_info, colWidths=[2*inch, 4*inch])
    emp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(emp_table)
    story.append(Spacer(1, 20))
    
    # Datos del recibo
    if recibo.sueldo_bruto:
        sueldo_info = [
            ['Concepto', 'Monto'],
            ['Sueldo Bruto', f"${recibo.sueldo_bruto:,.2f}"],
            ['Descuentos', f"${recibo.descuentos:,.2f}" if recibo.descuentos else "$0.00"],
            ['Sueldo Neto', f"${recibo.sueldo_neto:,.2f}"],
        ]
        
        sueldo_table = Table(sueldo_info, colWidths=[3*inch, 2*inch])
        sueldo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(sueldo_table)
        story.append(Spacer(1, 30))
    
    # Información de la firma
    firma_style = ParagraphStyle(
        'FirmaStyle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=10,
        alignment=TA_LEFT,
        textColor=colors.darkgreen if tipo_firma == 'conforme' else colors.red
    )
    
    estado_texto = "FIRMADO" if tipo_firma == 'conforme' else "FIRMADO EN DISCONFORMIDAD"
    story.append(Paragraph(f"<b>Estado:</b> {estado_texto}", firma_style))
    story.append(Paragraph(f"<b>Fecha de Firma:</b> {recibo.fecha_firma.strftime('%d/%m/%Y %H:%M')}", firma_style))
    
    if observaciones:
        story.append(Paragraph(f"<b>Observaciones:</b> {observaciones}", firma_style))
    
    story.append(Spacer(1, 20))
    
    # Firma digital
    if empleado.firma_imagen:
        story.append(Paragraph("<b>Firma Digital:</b>", styles['Normal']))
        story.append(Spacer(1, 10))
        
        # Aquí podrías agregar la imagen de la firma si es necesario
        # story.append(Image(empleado.firma_imagen.path, width=2*inch, height=1*inch))
    
    # Información de autenticidad
    story.append(Spacer(1, 30))
    auth_style = ParagraphStyle(
        'AuthStyle',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    story.append(Paragraph("Este documento ha sido firmado digitalmente y cuenta con validez legal.", auth_style))
    story.append(Paragraph(f"Firmado electrónicamente el {recibo.fecha_firma.strftime('%d/%m/%Y a las %H:%M')}", auth_style))
    
    # Construir PDF
    doc.build(story)
    
    # Obtener contenido del buffer
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content


def generar_pdf_firmado_sobre_original(recibo, empleado, tipo_firma, observaciones):
    """Generar PDF firmado usando el PDF original como base y agregando la firma"""
    try:
        from PyPDF2 import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.utils import ImageReader
        import base64
        import os
        
        print(f"Iniciando generación de PDF firmado para recibo {recibo.id}")
        
        # Usar el PDF original como base
        if not recibo.archivo_pdf:
            print("Error: No hay PDF original para firmar")
            raise Exception("No hay PDF original para firmar")
        
        print(f"PDF original encontrado: {recibo.archivo_pdf.name}")
        
        # Leer el PDF original
        recibo.archivo_pdf.seek(0)
        reader = PdfReader(recibo.archivo_pdf)
        writer = PdfWriter()
        
        print(f"PDF original leído exitosamente, {len(reader.pages)} páginas")
        
        # Obtener el tamaño de la primera página del PDF original
        first_page = reader.pages[0]
        mediabox = first_page.mediabox
        page_width = float(mediabox.width)
        page_height = float(mediabox.height)
        
        print(f"Tamaño de página: {page_width} x {page_height}")
        
        # Crear overlay con la firma
        overlay_buffer = BytesIO()
        
        # Usar el tamaño de la página original o A4 como fallback
        if page_width > 0 and page_height > 0:
            page_size = (page_width, page_height)
        else:
            page_size = A4
            page_width, page_height = A4
        
        c = canvas.Canvas(overlay_buffer, pagesize=page_size)
        
        # Posición para la firma (pegado al margen derecho)
        firma_x = page_width - 160  # Más pegado al margen derecho
        firma_y = 180  # Altura apropiada
        
        # Asegurarse de que la firma no se salga de la página
        if firma_x < 50:
            firma_x = 50
        if firma_y < 120:
            firma_y = 120
        
        print(f"Posición de firma: x={firma_x}, y={firma_y}")
        
        # Configurar fuente
        c.setFont("Helvetica-Bold", 9)
        
        # Crear un fondo sutil para la firma (sin tapar contenido)
        c.setFillColorRGB(0.99, 0.99, 0.99, alpha=0.9)  # Fondo blanco casi transparente
        c.setStrokeColorRGB(0.7, 0.7, 0.7)  # Borde gris muy suave
        c.rect(firma_x - 5, firma_y - 100, 155, 140, fill=1, stroke=1)  # Caja más compacta
        
        # Agregar información de la firma
        c.setFillColorRGB(0, 0, 0)  # Texto negro
        c.setFont("Helvetica-Bold", 9)
        c.drawString(firma_x, firma_y + 80, "FIRMADO DIGITALMENTE")
        
        c.setFont("Helvetica", 7)
        c.drawString(firma_x, firma_y + 65, f"Empleado: {empleado.user.get_full_name()}")
        c.drawString(firma_x, firma_y + 52, f"Legajo: {empleado.legajo}")
        c.drawString(firma_x, firma_y + 39, f"Fecha: {timezone.now().strftime('%d/%m/%Y %H:%M')}")
        
        # Estado de la firma
        c.setFont("Helvetica-Bold", 7)
        if tipo_firma == 'conforme':
            c.setFillColorRGB(0, 0.5, 0)  # Verde
            estado_texto = "CONFORME"
        else:
            c.setFillColorRGB(0.8, 0.4, 0)  # Naranja
            estado_texto = "CON OBSERVACIONES"
        
        c.drawString(firma_x, firma_y + 26, f"Estado: {estado_texto}")
        
        # Resetear color para el resto del contenido
        c.setFillColorRGB(0, 0, 0)
        
        # Agregar imagen de firma si existe
        if empleado.firma_imagen:
            try:
                # Verificar si es un string base64 o un archivo de imagen
                if hasattr(empleado.firma_imagen, 'read'):
                    # Es un ImageFieldFile, leer el contenido
                    empleado.firma_imagen.seek(0)
                    image_bytes = empleado.firma_imagen.read()
                    temp_image = BytesIO(image_bytes)
                    img_reader = ImageReader(temp_image)
                    
                    # Agregar la imagen al PDF con tamaño más compacto
                    c.drawImage(img_reader, firma_x + 2, firma_y - 30, width=100, height=35, 
                               preserveAspectRatio=True, mask='auto')
                    
                    temp_image.close()
                    print("Imagen de firma agregada exitosamente (desde archivo)")
                
                elif isinstance(empleado.firma_imagen, str):
                    # Es un string, procesar como base64
                    if empleado.firma_imagen.startswith("data:image/"):
                        header, image_data = empleado.firma_imagen.split(',', 1)
                        image_bytes = base64.b64decode(image_data)
                        
                        # Crear un ImageReader desde los bytes
                        temp_image = BytesIO(image_bytes)
                        img_reader = ImageReader(temp_image)
                        
                        # Agregar la imagen al PDF con tamaño más compacto
                        c.drawImage(img_reader, firma_x + 2, firma_y - 30, width=100, height=35, 
                                   preserveAspectRatio=True, mask='auto')
                        
                        temp_image.close()
                        print("Imagen de firma agregada exitosamente (desde base64)")
                        
                    elif empleado.firma_imagen.strip():
                        # Si no tiene el formato data:image/, intentar decodificar directamente
                        try:
                            image_bytes = base64.b64decode(empleado.firma_imagen)
                            temp_image = BytesIO(image_bytes)
                            img_reader = ImageReader(temp_image)
                            
                            c.drawImage(img_reader, firma_x + 2, firma_y - 30, width=100, height=35, 
                                       preserveAspectRatio=True, mask='auto')
                            
                            temp_image.close()
                            print("Imagen de firma agregada exitosamente (formato alternativo)")
                        except Exception as decode_error:
                            print(f"Error al decodificar imagen alternativa: {str(decode_error)}")
                            raise decode_error
                    else:
                        print("String de firma vacío o solo espacios")
                        raise ValueError("Firma imagen vacía")
                else:
                    print(f"Tipo de firma_imagen no reconocido: {type(empleado.firma_imagen)}")
                    raise ValueError("Tipo de firma imagen no válido")
                    
            except Exception as img_error:
                print(f"Error al agregar imagen de firma: {str(img_error)}")
                print(f"Tipo de firma_imagen: {type(empleado.firma_imagen)}")
                
                # Agregar texto alternativo si falla la imagen
                c.setFillColorRGB(0, 0, 0)
                c.setFont("Helvetica-Oblique", 9)
                c.drawString(firma_x + 2, firma_y - 10, "[Firma Digital]")
        else:
            # Si no hay imagen de firma, mostrar texto alternativo
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Oblique", 9)
            c.drawString(firma_x + 2, firma_y - 10, "[Firma Digital - Sin imagen]")
        
        # Agregar observaciones si existen
        if observaciones:
            c.setFont("Helvetica", 7)
            y_obs = firma_y - 55
            c.drawString(firma_x, y_obs, "Observaciones:")
            
            # Dividir observaciones en líneas que quepan en el espacio
            max_chars_per_line = 35
            words = observaciones.split()
            line = ""
            y_current = y_obs - 10
            
            for word in words:
                if len(line + word) < max_chars_per_line:
                    line += word + " "
                else:
                    if line.strip():
                        c.drawString(firma_x, y_current, line.strip())
                        y_current -= 8
                    line = word + " "
                    
                    # Evitar que el texto se salga de la página
                    if y_current < 20:
                        c.drawString(firma_x, y_current, "...")
                        break
            
            if line.strip() and y_current > 20:
                c.drawString(firma_x, y_current, line.strip())
        
        c.save()
        
        # Crear el overlay PDF
        overlay_buffer.seek(0)
        overlay_reader = PdfReader(overlay_buffer)
        overlay_page = overlay_reader.pages[0]
        
        # Combinar cada página del PDF original con el overlay
        for page_num, page in enumerate(reader.pages):
            if page_num == 0:  # Solo agregar firma en la primera página
                try:
                    page.merge_page(overlay_page)
                except Exception as merge_error:
                    print(f"Error al hacer merge de la página: {str(merge_error)}")
                    # Continuar sin el overlay si falla
            writer.add_page(page)
        
        # Generar el PDF final
        output_buffer = BytesIO()
        writer.write(output_buffer)
        output_buffer.seek(0)
        
        pdf_content = output_buffer.getvalue()
        
        # Limpiar buffers
        overlay_buffer.close()
        output_buffer.close()
        
        return pdf_content
        
    except Exception as e:
        print(f"Error en generar_pdf_firmado_sobre_original: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Fallback: Si hay PDF original, devolverlo sin modificar
        if recibo.archivo_pdf:
            try:
                recibo.archivo_pdf.seek(0)
                original_content = recibo.archivo_pdf.read()
                print("Usando PDF original sin modificar como fallback")
                return original_content
            except Exception as fallback_error:
                print(f"Error al leer PDF original: {str(fallback_error)}")
        
        # Último recurso: generar PDF básico
        print("Generando PDF básico como último recurso")
        return generar_pdf_firmado(recibo, empleado, tipo_firma, observaciones)


def get_client_ip(request):
    """Obtener IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def ver_recibo_firmado(request, recibo_id):
    """Ver el PDF firmado por el empleado"""
    try:
        empleado = Empleado.objects.get(user=request.user)
        recibo = get_object_or_404(ReciboSueldo, id=recibo_id, empleado=empleado)
        
        # Verificar que pueda ver este recibo
        if not recibo.puede_ver:
            messages.error(request, 'No puedes ver este recibo. Debes firmar el recibo anterior primero.')
            return redirect('recibos:mis_recibos')
        
        # Verificar que el recibo esté firmado
        if recibo.estado != 'firmado':
            messages.error(request, 'Este recibo no ha sido firmado aún.')
            return redirect('recibos:mis_recibos')
        
        # Verificar que existe el archivo firmado
        if not recibo.archivo_firmado:
            messages.error(request, 'No se encontró el archivo firmado.')
            return redirect('recibos:mis_recibos')
        
        # Registrar actividad
        ActividadEmpleado.objects.create(
            empleado=empleado,
            descripcion=f"Consultó el recibo firmado de {recibo.get_periodo_display()} {recibo.anio}"
        )
        
        # Leer el contenido del archivo firmado
        try:
            recibo.archivo_firmado.seek(0)
            archivo_content = recibo.archivo_firmado.read()
        except Exception as e:
            raise Http404(f"Error al leer el archivo firmado: {str(e)}")
        
        response = HttpResponse(archivo_content, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="recibo_firmado_{recibo.periodo}_{recibo.anio}_{empleado.legajo}.pdf"'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response
        
    except Empleado.DoesNotExist:
        raise Http404("Empleado no encontrado")
