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
@login_required
def ver_recibo_pdf(request, recibo_id):
    """Ver el PDF del recibo"""
    try:
        empleado = Empleado.objects.get(user=request.user)
        recibo = get_object_or_404(ReciboSueldo, id=recibo_id, empleado=empleado)
        
        # Verificar que pueda ver este recibo
        if not recibo.puede_ver:
            messages.error(request, 'No puedes ver este recibo. Debes firmar el recibo anterior primero.')
            return redirect('recibos:mis_recibos')
        
        if not recibo.archivo_pdf:
            raise Http404("Archivo no encontrado")
        
        # Registrar actividad
        ActividadEmpleado.objects.create(
            empleado=empleado,
            descripcion=f"Consultó el recibo de {recibo.get_periodo_display()} {recibo.anio}"
        )
        
        # Leer el contenido del archivo
        try:
            archivo_content = recibo.archivo_pdf.read()
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
        
        # Generar PDF firmado
        try:
            # Las observaciones vienen del recibo si fue observado previamente
            observaciones_para_pdf = recibo.observaciones_empleado if recibo.observaciones_empleado else ''
            pdf_firmado = generar_pdf_firmado(recibo, empleado, tipo_firma, observaciones_para_pdf)
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


def get_client_ip(request):
    """Obtener IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
