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
        
        # DIAGNÓSTICO DETALLADO: Verificar qué archivos tiene el recibo
        print(f"\n🔍 DIAGNÓSTICO PARA RECIBO {recibo.id} - LEGAJO {empleado.legajo}")
        print(f"📋 Estado del recibo: {recibo.estado}")
        print(f"📄 archivo_pdf existe: {bool(recibo.archivo_pdf)}")
        print(f"📄 archivo_pdf_centromedica existe: {bool(recibo.archivo_pdf_centromedica)}")
        print(f"📄 archivo_firmado existe: {bool(recibo.archivo_firmado)}")
        
        if recibo.archivo_pdf:
            print(f"📄 archivo_pdf nombre: {recibo.archivo_pdf.name}")
            print(f"📄 archivo_pdf tamaño: {recibo.archivo_pdf.size} bytes")
        
        if recibo.archivo_pdf_centromedica:
            print(f"📄 archivo_pdf_centromedica nombre: {recibo.archivo_pdf_centromedica.name}")
            print(f"📄 archivo_pdf_centromedica tamaño: {recibo.archivo_pdf_centromedica.size} bytes")
        else:
            print(f"❌ archivo_pdf_centromedica NO EXISTE - se generará automáticamente si es necesario")
        
        # LÓGICA SIMPLIFICADA DE VISUALIZACIÓN:
        # Ahora TODOS los archivos tienen formato aplicado, así que la prioridad es:
        # 1. Si está firmado → mostrar archivo_firmado (tiene formato + firma)
        # 2. Si existe archivo_pdf → mostrar archivo_pdf (ya tiene formato aplicado)
        # 3. Como último recurso → mostrar archivo_pdf_centromedica (compatibilidad)
        archivo_a_mostrar = None
        archivo_tipo = ""
        
        # 1. Si está firmado, mostrar archivo firmado (contiene formato + firma)
        if recibo.estado == 'firmado' and recibo.archivo_firmado:
            archivo_a_mostrar = recibo.archivo_firmado
            archivo_tipo = "firmado por empleado (con formato + firma)"
            print(f"➡️ Mostrando PDF firmado por empleado para {empleado.legajo}")
        
        # 2. Si existe archivo_pdf, mostrarlo (ya tiene formato aplicado)
        elif recibo.archivo_pdf:
            archivo_a_mostrar = recibo.archivo_pdf
            archivo_tipo = "con formato Centromédica aplicado (archivo principal)"
            print(f"➡️ Mostrando PDF principal con formato para {empleado.legajo}")
        
        # 3. Fallback: mostrar archivo_pdf_centromedica si existe
        elif recibo.archivo_pdf_centromedica:
            archivo_a_mostrar = recibo.archivo_pdf_centromedica
            archivo_tipo = "con formato Centromédica aplicado (archivo compatibilidad)"
            print(f"➡️ Mostrando PDF de compatibilidad con formato para {empleado.legajo}")
        
        # 4. No hay archivos disponibles
        else:
            print(f"❌ No hay archivos PDF disponibles para el recibo {recibo.id}")
        
        print(f"🎯 RESULTADO: Mostrando archivo {archivo_tipo}")
        
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
        
        # Usar el PDF con formato como base (ya que ahora todos tienen formato)
        if not recibo.archivo_pdf:
            print("Error: No hay PDF con formato para firmar")
            raise Exception("No hay PDF con formato para firmar")
        
        print(f"PDF con formato encontrado: {recibo.archivo_pdf.name}")
        
        # Leer el PDF con formato
        recibo.archivo_pdf.seek(0)
        reader = PdfReader(recibo.archivo_pdf)
        writer = PdfWriter()
        
        print(f"PDF con formato leído exitosamente, {len(reader.pages)} páginas")
        
        # Obtener el tamaño de la primera página del PDF con formato
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
        
        # Fallback: Si hay PDF con formato, devolverlo sin modificar
        if recibo.archivo_pdf:
            try:
                recibo.archivo_pdf.seek(0)
                formatted_content = recibo.archivo_pdf.read()
                print("Usando PDF con formato sin modificar como fallback")
                return formatted_content
            except Exception as fallback_error:
                print(f"Error al leer PDF con formato: {str(fallback_error)}")
        
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


@login_required
def ver_recibo_centromedica(request, recibo_id):
    """Ver/descargar el PDF con formato Centromédica"""
    try:
        empleado = Empleado.objects.get(user=request.user)
        recibo = get_object_or_404(ReciboSueldo, id=recibo_id, empleado=empleado)
        
        # Verificar que pueda ver este recibo
        if not recibo.puede_ver:
            messages.error(request, 'No puedes ver este recibo. Debes firmar el recibo anterior primero.')
            return redirect('recibos:mis_recibos')
        
        # Verificar que el recibo esté firmado (necesario para que exista el archivo de Centromédica)
        if recibo.estado not in ['firmado']:
            messages.error(request, 'El recibo con formato Centromédica solo está disponible después de firmar.')
            return redirect('recibos:mis_recibos')
        
        # Verificar que existe el archivo con formato Centromédica
        if not recibo.archivo_pdf_centromedica:
            messages.error(request, 'No se encontró el archivo con formato Centromédica.')
            return redirect('recibos:mis_recibos')
        
        # Registrar actividad
        ActividadEmpleado.objects.create(
            empleado=empleado,
            descripcion=f"Descargó el recibo con formato Centromédica de {recibo.get_periodo_display()} {recibo.anio}"
        )
        
        # Leer el contenido del archivo con formato Centromédica
        try:
            recibo.archivo_pdf_centromedica.seek(0)
            archivo_content = recibo.archivo_pdf_centromedica.read()
        except Exception as e:
            raise Http404(f"Error al leer el archivo con formato Centromédica: {str(e)}")
        
        response = HttpResponse(archivo_content, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="recibo_centromedica_{recibo.periodo}_{recibo.anio}_{empleado.legajo}.pdf"'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response
        
    except Empleado.DoesNotExist:
        raise Http404("Empleado no encontrado")


def aplicar_formato_centromedica_a_pdf_original(recibo, empleado):
    """Aplica el formato visual de Centromédica al PDF manteniendo el contenido - USANDO FUNCIÓN DE TEST"""
    try:
        print(f"🔄 Aplicando formato de Centromédica COMPLETO para {empleado.user.get_full_name()}")
        
        # USAR la función de TEST que sabemos que funciona
        pdf_formateado = generar_pdf_formato_centromedica_test(recibo, empleado)
        
        if pdf_formateado and len(pdf_formateado) > 1000:
            print(f"✅ Formato aplicado exitosamente: {len(pdf_formateado)} bytes")
            return pdf_formateado
        else:
            print(f"⚠️ Error aplicando formato (tamaño: {len(pdf_formateado) if pdf_formateado else 'None'} bytes)")
            # Fallback: devolver el PDF original sin modificar
            if recibo.archivo_pdf:
                recibo.archivo_pdf.seek(0)
                original_content = recibo.archivo_pdf.read()
                print(f"📋 Devolviendo PDF original como fallback: {len(original_content)} bytes")
                return original_content
            return None
        
    except Exception as e:
        print(f"❌ Error en aplicar_formato_centromedica_a_pdf_original: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def generar_formato_centromedica_completo(recibo, empleado):
    """Genera el formato completo de Centromédica al PDF original manteniendo el contenido"""
    try:
        from PyPDF2 import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        
        print(f"Aplicando formato Centromédica completo al PDF original para {empleado.user.get_full_name()}")
        
        # Verificar que existe el PDF original
        if not recibo.archivo_pdf:
            print("Error: No hay PDF original para formatear")
            return None
        
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
        
        print(f"Tamaño de página original: {page_width} x {page_height}")
        
        # Crear overlay con el formato de Centromédica
        overlay_buffer = BytesIO()
        
        # Usar el tamaño de la página original
        page_size = (page_width, page_height)
        c = canvas.Canvas(overlay_buffer, pagesize=page_size)
        
        # =====================================
        # SECCIÓN 1: ENCABEZADO Y LOGO  
        # =====================================
        c.setStrokeColor(colors.blue)
        c.setLineWidth(0.5)
        
        # Logo desde archivo de imagen
        logo_x = 25
        logo_y = page_height - 100  # Ajustado para acomodar la imagen
        
        try:
            from reportlab.lib.utils import ImageReader
            import os
            
            # Ruta al logo
            logo_path = r"C:\Repositorys\Ayuda-RRHH-Usuarios\static\img\logo.png"
            
            if os.path.exists(logo_path):
                # Cargar y agregar la imagen del logo
                img_reader = ImageReader(logo_path)
                # Ajustar el tamaño del logo (ancho x alto)
                c.drawImage(img_reader, logo_x, logo_y, width=150, height=60,
                           preserveAspectRatio=True, mask='auto')
                print(f"Logo cargado desde: {logo_path}")
            else:
                # Fallback: texto si no se encuentra la imagen
                c.setFillColor(colors.red)
                c.setFont("Helvetica-Bold", 16)
                c.drawString(logo_x, logo_y + 15, "Ayuda")
                c.setFillColor(colors.blue)
                c.drawString(logo_x + 48, logo_y + 15, "Médica")
                print(f"Logo no encontrado en: {logo_path}, usando texto como fallback")
                
        except Exception as e:
            # Fallback en caso de error: usar texto
            print(f"Error cargando logo: {str(e)}")
            c.setFillColor(colors.red)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(logo_x, logo_y + 15, "Ayuda")
            c.setFillColor(colors.blue)
            c.drawString(logo_x + 48, logo_y + 15, "Médica")
        
        # Título "RECIBO DE SUELDO" en la parte superior derecha
        c.setFillColor(colors.blue)
        c.setFont("Helvetica-Bold", 12)
        titulo_x = page_width - 180
        c.drawString(titulo_x, page_height - 75, "RECIBO DE SUELDO")
        

        
        # =====================================
        # ESTRUCTURA PRINCIPAL DE LA TABLA
        # =====================================
        c.setLineWidth(0.5)
        c.setStrokeColor(colors.blue)

        # Definir las dimensiones de la tabla principal
        tabla_x = 25  # Margen izquierdo
        tabla_width = page_width - 50  # Ancho total menos márgenes
        tabla_y_inicio = page_height - 95  # Posición Y de inicio
        tabla_height_total = 600  # Altura total de toda la tabla

        # Rectángulo principal que contiene toda la estructura
        c.setLineWidth(1.0)  
        c.rect(tabla_x, tabla_y_inicio - tabla_height_total, tabla_width, tabla_height_total, fill=0, stroke=1)
        c.setLineWidth(0.5)

        # =====================================
        # COLORES DE FONDO (DIBUJAR PRIMERO - ANTES QUE LAS LÍNEAS)
        # =====================================
        # Ejemplo: Dar color rosa al área de CONCEPTOS
        c.setFillColorRGB(1.0, 0.85, 0.9)  # Rosa claro (R, G, B entre 0 y 1)
        # Nota: Las coordenadas se definirán después cuando tengamos las variables division5_y, etc.
        
        # =====================================
        # LÍNEAS DIVISORIAS HORIZONTALES
        # =====================================
        # Primera división: después del campo CUIT
        division1_y = tabla_y_inicio - 20
        c.line(tabla_x, division1_y, tabla_x + tabla_width, division1_y)

        # Segunda división: después de los datos del domicilio
        division2_y = tabla_y_inicio - 40
        c.line(tabla_x, division2_y, tabla_x + tabla_width, division2_y)

        # Tercera división: después de la tabla de conceptos
        division3_y = tabla_y_inicio - 55
        c.line(tabla_x, division3_y, tabla_x + tabla_width, division3_y)

        # Cuarta división: después de totales
        division4_y = tabla_y_inicio - 80
        c.line(tabla_x, division4_y, tabla_x + tabla_width, division4_y)

        # Para la tabla de conceptos
        col1_x = tabla_x + 470  # Después de CONCEPTO

        c.line(col1_x, division2_y, col1_x, division4_y)

        # Cuarta división: después de totales
        division5_y = tabla_y_inicio - 163
        c.line(tabla_x, division5_y, tabla_x + tabla_width, division5_y)

        # Cuarta división: después de totales
        division6_y = tabla_y_inicio - 175
        c.line(tabla_x, division6_y, tabla_x + tabla_width, division6_y)

        # Para la tabla de conceptos
        col1_x = tabla_x + 250  # Después de CONCEPTO

        c.line(col1_x, division4_y, col1_x, division5_y)

        division6a_y = tabla_y_inicio - 95
        
        # NUEVA LÍNEA HORIZONTAL: Desde col1_x hasta el final de la tabla
        c.line(col1_x, division6a_y, tabla_x + tabla_width, division6a_y)
        
        division6a_y = tabla_y_inicio - 110
        
        # NUEVA LÍNEA HORIZONTAL: Desde col1_x hasta el final de la tabla
        c.line(col1_x, division6a_y, tabla_x + tabla_width, division6a_y)

        division6a_y = tabla_y_inicio - 140
        
        # NUEVA LÍNEA HORIZONTAL: Desde col1_x hasta el final de la tabla
        c.line(col1_x, division6a_y, tabla_x + tabla_width, division6a_y)


        
    
        # Cuarta división: después de totales
        division16_y = tabla_y_inicio - 385
        c.line(tabla_x, division16_y, tabla_x + tabla_width, division16_y)



        # =====================================
        # LÍNEAS DIVISORIAS VERTICALES
        # =====================================
        # Para la tabla de conceptos
        col1_x = tabla_x + 270  # Después de CONCEPTO
        col2_x = tabla_x + 320  # UNIDADES
        col3_x = tabla_x + 400  # REMUNERACIONES
        col4_x = tabla_x + 480  # DESCUENTOS

         # Cuarta división: después de totales
        division17_y = tabla_y_inicio - 405
        c.line(tabla_x, division17_y, tabla_x + tabla_width, division17_y)

         # Cuarta división: después de totales
        division18_y = tabla_y_inicio - 425
        c.line(tabla_x, division18_y, tabla_x + tabla_width, division18_y)
        # Líneas verticales en la sección de conceptos
        c.line(col1_x, division5_y, col1_x, division16_y)
        c.line(col2_x, division5_y, col2_x, division17_y)
        c.line(col3_x, division5_y, col3_x, division17_y)
        c.line(col4_x, division5_y, col4_x, division18_y)

        division19_y = tabla_y_inicio - 455
        c.line(tabla_x, division19_y, tabla_x + tabla_width, division19_y)

        division20_y = tabla_y_inicio - 485 
        c.line(tabla_x, division20_y, tabla_x + tabla_width, division20_y)

        division21_y = tabla_y_inicio - 520 
        c.line(tabla_x, division21_y, tabla_x + tabla_width, division21_y)

        col1_x = tabla_x + 210  # Después de CONCEPTO
        c.line(col1_x, division21_y, col1_x, division21_y -80)



        # =====================================
        # ETIQUETAS Y CAMPOS
        # =====================================
        # Campo CUIT ocupando casi todo el ancho de la página
        c.setFillColor(colors.blue)
        c.setFont("Helvetica-Bold", 6)
        c.drawString(page_width - 140, page_height - 106, "CUIT")
        # Más etiquetas...

        c.drawString(page_width - 565, page_height - 146, "APELLIDO Y NOMBRE")
        c.drawString(page_width - 165, page_height - 146, "CUIL")
        c.drawString(page_width - 70, page_height - 146, "LEGAJO")

        c.drawString(page_width - 300, page_height - 186, "FECHA DE INGRESO")
        c.drawString(page_width - 225, page_height - 186, "REMUNERACION ASIGNADA")
        c.drawString(page_width - 70, page_height - 186, "RECIBO Nº")

        c.drawString(page_width - 565, page_height - 190, "SECCION")
        c.drawString(page_width - 565, page_height - 215, "CATEGORIA")
        c.drawString(page_width - 565, page_height - 240, "CALIFICACION PROFESIONAL")
        
        c.drawString(page_width - 310, page_height - 215, "PERIODO DE PAGO")
        c.drawString(page_width - 310, page_height - 240, "CONTRATACION")

        c.setFont("Helvetica-Bold", 6)
        c.drawString(page_width - 470, page_height - 266, "CONCEPTOS")
        c.drawString(page_width - 288, page_height - 266, "UNIDADES")
        c.drawString(page_width - 235, page_height - 264, "REMUNERACIONES")
        c.drawString(page_width - 240, page_height - 269, "SUJETAS A RETENCION")
        c.drawString(page_width - 153, page_height - 264, "REMUNERACIONES")
        c.drawString(page_width - 142, page_height - 269, "EXENTAS")
        c.drawString(page_width - 73, page_height - 266, "DESCUENTOS")

        c.setFont("Helvetica-Bold", 6)
        c.drawString(page_width - 565, page_height - 516, "LUGAR Y FECHA DE PAGO")
        c.drawString(page_width - 288, page_height - 516, "FORMA DE PAGO")
        c.drawString(page_width - 153, page_height - 516, "TOTAL NETO")

        c.drawString(page_width - 565, page_height - 556, "SON PESOS")

        c.drawString(page_width - 565, page_height - 630, "ART.12 LEY 17250")
        c.drawString(page_width - 565, page_height - 640, "MES")
        c.drawString(page_width - 565, page_height - 650, "BANCO")
        c.drawString(page_width - 565, page_height - 660, "FECHA DEPOSITO")


        # Guardar el overlay
        c.save()
        
        # Combinar el PDF original con el overlay de formato
        overlay_buffer.seek(0)
        overlay_reader = PdfReader(overlay_buffer)
        overlay_page = overlay_reader.pages[0]
        
        # Aplicar el overlay a cada página del PDF original
        for page_num, page in enumerate(reader.pages):
            try:
                # Aplicar overlay profesional con formato Centromédica
                
                print(f"🔗 Procesando página {page_num + 1} con método overlay-debajo...")
                
                page.merge_page(overlay_page)  # Formato DEBAJO del contenido original
                writer.add_page(page)
                
                print(f"✅ Página {page_num + 1} procesada exitosamente")
                        
            except Exception as page_error:
                print(f"⚠️ Error procesando página {page_num + 1}: {str(page_error)}")
                # Si falla, agregar solo el overlay como fallback
                writer.add_page(overlay_page)
                print(f"📄 Página {page_num + 1} agregada como fallback")
        
        # Generar el PDF final
        output_buffer = BytesIO()
        writer.write(output_buffer)
        output_buffer.seek(0)
        
        pdf_content = output_buffer.getvalue()
        
        # Limpiar buffers
        overlay_buffer.close()
        output_buffer.close()
        
        print(f"Formato aplicado exitosamente al PDF original")
        return pdf_content
        
    except Exception as e:
        print(f"Error aplicando formato Centromédica: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def generar_pdf_formato_centromedica_test(recibo, empleado):
    """Función de prueba para aplicar formato profesional de Centromédica al PDF original - VERSIÓN MEJORADA"""
    try:
        print(f"🔄 Iniciando formato de prueba para {empleado.user.get_full_name()}")
        
        # Verificar que el PDF original existe
        if not recibo.archivo_pdf:
            print("❌ Error: No existe archivo PDF original")
            return None
            
        # Leer el PDF original
        recibo.archivo_pdf.seek(0)
        pdf_original_data = recibo.archivo_pdf.read()
        print(f"📄 PDF original leído: {len(pdf_original_data)} bytes")
        
        # Usar la función completa de formato
        pdf_formateado = generar_formato_centromedica_completo(recibo, empleado)
        
        if pdf_formateado and len(pdf_formateado) > 1000:  # Verificar que tenga contenido significativo
            print(f"✅ Formato aplicado exitosamente: {len(pdf_formateado)} bytes")
            return pdf_formateado
        else:
            print(f"⚠️ Formato retornó datos insuficientes: {len(pdf_formateado) if pdf_formateado else 'None'} bytes")
            print("📋 Devolviendo PDF original como fallback")
            return pdf_original_data
        
    except Exception as e:
        print(f"❌ Error en generar_pdf_formato_centromedica_test: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Fallback: devolver el PDF original
        try:
            if recibo.archivo_pdf:
                recibo.archivo_pdf.seek(0)
                return recibo.archivo_pdf.read()
        except:
            pass
        return None
