from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as AuthLoginView
from django.views.generic import TemplateView, ListView, FormView, UpdateView, CreateView, DetailView
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, FileResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile
from django.db import transaction
import os
import mimetypes
import re
import traceback
import PyPDF2
from PyPDF2 import PdfReader, PdfWriter
import threading
from io import BytesIO
from datetime import timedelta

from apps.empleados.models import Empleado, SolicitudCambio, DomicilioEmpleado
from apps.documentos.models import Documento, TipoDocumento, Inasistencia, HistorialDocumento
from apps.documentos.forms import CrearInasistenciaForm
from apps.notificaciones.models import Notificacion
from apps.recibos.models import ReciboSueldo
from apps.recibos.views import aplicar_formato_centromedica_a_pdf_original  # Importar función de formato
from .models import CargaMasivaRecibos, LogProcesamientoRecibo
from .forms import SubirRecibosForm, CrearEmpleadoForm, EditarEmpleadoForm, DomicilioEmpleadoForm, CargaMasivaRecibosForm
from reportlab.lib.pagesizes import A4

class SoloRRHHMixin:
    """Mixin para views basadas en clase que solo permite usuarios RRHH"""
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                empleado = Empleado.objects.get(user=request.user)
                if not empleado.es_rrhh:
                    return redirect('empleados:dashboard')
            except Empleado.DoesNotExist:
                return redirect('empleados:dashboard')
        return super().dispatch(request, *args, **kwargs)

class RRHHLoginView(AuthLoginView):
    template_name = 'rrhh/login.html'

class RRHHDashboardView(LoginRequiredMixin, SoloRRHHMixin, TemplateView):
    template_name = 'rrhh/dashboard.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['empleados_count'] = Empleado.objects.count()
        context['solicitudes_count'] = SolicitudCambio.objects.filter(estado='pendiente').count()
        context['recibos_count'] = ReciboSueldo.objects.count()
        context['documentos_count'] = Documento.objects.filter(estado='pendiente').count()
        context['observaciones_pendientes_count'] = ReciboSueldo.objects.filter(estado='observado').count()
        print(context)
        return context

class EmpleadosListView(LoginRequiredMixin, SoloRRHHMixin, ListView):
    template_name = 'rrhh/empleados.html'
    model = Empleado
    context_object_name = 'empleados'
    paginate_by = 10

    def get_queryset(self):
        queryset = Empleado.objects.select_related('user').all()
        
        # Filtro por búsqueda
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(legajo__icontains=search) |
                Q(dni__icontains=search) |
                Q(puesto__icontains=search) |
                Q(departamento__icontains=search)
            )
        
        # Filtro por departamento
        departamento = self.request.GET.get('departamento')
        if departamento:
            queryset = queryset.filter(departamento=departamento)
        
        # Filtro por tipo de contrato
        tipo_contrato = self.request.GET.get('tipo_contrato')
        if tipo_contrato:
            queryset = queryset.filter(tipo_contrato=tipo_contrato)
        
        # Filtro por RRHH
        es_rrhh = self.request.GET.get('es_rrhh')
        if es_rrhh:
            queryset = queryset.filter(es_rrhh=es_rrhh == 'true')
        
        return queryset.order_by('user__last_name', 'user__first_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departamentos'] = Empleado.objects.values_list('departamento', flat=True).distinct().exclude(departamento='')
        context['tipos_contrato'] = Empleado.TIPO_CONTRATO_CHOICES
        context['search'] = self.request.GET.get('search', '')
        context['departamento_selected'] = self.request.GET.get('departamento', '')
        context['tipo_contrato_selected'] = self.request.GET.get('tipo_contrato', '')
        context['es_rrhh_selected'] = self.request.GET.get('es_rrhh', '')
        print(context)
        return context

class CrearEmpleadoView(LoginRequiredMixin, SoloRRHHMixin, CreateView):
    model = Empleado
    form_class = CrearEmpleadoForm
    template_name = 'rrhh/crear_empleado.html'
    success_url = reverse_lazy('rrhh:empleados')

    def form_valid(self, form):
        # Crear usuario primero
        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            password=form.cleaned_data['password1']
        )
        
        # Crear empleado
        empleado = form.save(commit=False)
        empleado.user = user
        empleado.save()
        
        messages.success(self.request, f'Empleado {user.get_full_name()} creado exitosamente.')
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrija los errores en el formulario.')
        return super().form_invalid(form)

class EditarEmpleadoView(LoginRequiredMixin, SoloRRHHMixin, UpdateView):
    model = Empleado
    form_class = EditarEmpleadoForm
    template_name = 'rrhh/editar_empleado.html'
    success_url = reverse_lazy('rrhh:empleados')

    def form_valid(self, form):
        # Actualizar usuario
        user = self.object.user
        user.username = form.cleaned_data['username']
        user.email = form.cleaned_data['email']
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        user.save()
        
        # Actualizar empleado
        empleado = form.save()
        
        messages.success(self.request, f'Empleado {user.get_full_name()} actualizado exitosamente.')
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, corrija los errores en el formulario.')
        return super().form_invalid(form)

class EmpleadoDetailView(LoginRequiredMixin, SoloRRHHMixin, DetailView):
    model = Empleado
    template_name = 'rrhh/empleado_detail.html'
    context_object_name = 'empleado'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empleado = self.get_object()
        context['recibos'] = ReciboSueldo.objects.filter(empleado=empleado).order_by('-anio', '-periodo')
        context['documentos'] = Documento.objects.filter(empleado=empleado).order_by('-fecha_subida')
        context['solicitudes'] = SolicitudCambio.objects.filter(empleado=empleado).order_by('-fecha_solicitud')
        
        # Obtener o crear domicilio
        try:
            context['domicilio'] = DomicilioEmpleado.objects.get(empleado=empleado)
        except DomicilioEmpleado.DoesNotExist:
            context['domicilio'] = None
            
        return context

class EliminarEmpleadoView(LoginRequiredMixin, SoloRRHHMixin, TemplateView):
    template_name = 'rrhh/eliminar_empleado.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empleado'] = get_object_or_404(Empleado, pk=kwargs['pk'])
        return context

    def post(self, request, *args, **kwargs):
        empleado = get_object_or_404(Empleado, pk=kwargs['pk'])
        user = empleado.user
        nombre_empleado = user.get_full_name()
        
        # Eliminar empleado y usuario
        empleado.delete()
        user.delete()
        
        messages.success(request, f'Empleado {nombre_empleado} eliminado exitosamente.')
        return redirect('rrhh:empleados')

# Vista AJAX para obtener datos del empleado
def empleado_ajax(request, pk):
    try:
        empleado = get_object_or_404(Empleado, pk=pk)
        data = {
            'id': empleado.id,
            'nombre': empleado.user.get_full_name(),
            'legajo': empleado.legajo,
            'dni': empleado.dni,
            'puesto': empleado.puesto,
            'departamento': empleado.departamento,
            'tipo_contrato': empleado.get_tipo_contrato_display(),
            'salario': str(empleado.salario) if empleado.salario else '',
            'fecha_contrato': empleado.fecha_contrato.strftime('%d/%m/%Y') if empleado.fecha_contrato else '',
            'es_rrhh': empleado.es_rrhh,
            'telefono': empleado.telefono,
            'email': empleado.user.email
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)

class DocumentosRRHHListView(LoginRequiredMixin, SoloRRHHMixin, TemplateView):
    template_name = 'rrhh/documentos.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener todos los documentos con información relacionada
        documentos = Documento.objects.select_related(
            'empleado__user', 'tipo_documento', 'revisado_por'
        ).all()
        
        # Aplicar filtros si existen
        estado = self.request.GET.get('estado')
        if estado:
            documentos = documentos.filter(estado=estado)
            
        tipo_documento = self.request.GET.get('tipo_documento')
        if tipo_documento:
            documentos = documentos.filter(tipo_documento_id=tipo_documento)
            
        empleado_search = self.request.GET.get('empleado')
        if empleado_search:
            documentos = documentos.filter(
                Q(empleado__user__first_name__icontains=empleado_search) |
                Q(empleado__user__last_name__icontains=empleado_search) |
                Q(empleado__legajo__icontains=empleado_search)
            )
        
        # Ordenar por fecha de subida descendente
        documentos = documentos.order_by('-fecha_subida')
        
        # Estadísticas
        total_documentos = documentos.count()
        pendientes = documentos.filter(estado='pendiente').count()
        aprobados = documentos.filter(estado='aprobado').count()
        rechazados = documentos.filter(estado='rechazado').count()
        requieren_aclaracion = documentos.filter(estado='requiere_aclaracion').count()
        
        context.update({
            'documentos': documentos[:50],  # Limitar a 50 para rendimiento
            'total_documentos': total_documentos,
            'pendientes': pendientes,
            'aprobados': aprobados,
            'rechazados': rechazados,
            'requieren_aclaracion': requieren_aclaracion,
            'tipos_documento': TipoDocumento.objects.filter(activo=True),
            'estado_selected': estado or '',
            'tipo_documento_selected': tipo_documento or '',
            'empleado_search': empleado_search or '',
        })
        
        return context

class AprobarDocumentoView(LoginRequiredMixin, SoloRRHHMixin, TemplateView):
    template_name = 'rrhh/aprobar_documento.html'

class SolicitudesRRHHListView(LoginRequiredMixin, SoloRRHHMixin, ListView):
    template_name = 'rrhh/solicitudes.html'
    model = SolicitudCambio
    context_object_name = 'solicitudes'
    paginate_by = 10

    def get_queryset(self):
        queryset = SolicitudCambio.objects.select_related('empleado__user').all()
        
        # Filtro por estado
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Filtro por tipo
        tipo = self.request.GET.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        return queryset.order_by('-fecha_solicitud')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estados'] = SolicitudCambio.ESTADO_CHOICES
        context['tipos'] = SolicitudCambio.TIPO_CHOICES
        context['estado_selected'] = self.request.GET.get('estado', '')
        context['tipo_selected'] = self.request.GET.get('tipo', '')
        return context

class GestionarSolicitudView(LoginRequiredMixin, SoloRRHHMixin, DetailView):
    template_name = 'rrhh/gestionar_solicitud.html'
    model = SolicitudCambio
    context_object_name = 'solicitud'

    def post(self, request, *args, **kwargs):
        solicitud = self.get_object()
        accion = request.POST.get('accion')
        
        if accion == 'aprobar':
            solicitud.estado = 'aprobada'
            solicitud.fecha_resolucion = timezone.now()
            solicitud.revisado_por = request.user
            
            # Si es cambio de domicilio, actualizar el domicilio del empleado
            if solicitud.tipo == 'domicilio':
                try:
                    domicilio = DomicilioEmpleado.objects.get(empleado=solicitud.empleado)
                    # Actualizar con los datos nuevos del JSON
                    domicilio.calle = solicitud.datos_nuevos.get('calle', '')
                    domicilio.numero = solicitud.datos_nuevos.get('numero', '')
                    domicilio.piso = solicitud.datos_nuevos.get('piso', '')
                    domicilio.depto = solicitud.datos_nuevos.get('depto', '')
                    domicilio.barrio = solicitud.datos_nuevos.get('barrio', '')
                    domicilio.localidad = solicitud.datos_nuevos.get('localidad', '')
                    domicilio.provincia = solicitud.datos_nuevos.get('provincia', '')
                    domicilio.codigo_postal = solicitud.datos_nuevos.get('codigo_postal', '')
                    domicilio.entre_calles = solicitud.datos_nuevos.get('entre_calles', '')
                    domicilio.observaciones = solicitud.datos_nuevos.get('observaciones', '')
                    domicilio.save()
                    messages.success(request, 'Solicitud aprobada y domicilio actualizado correctamente.')
                except DomicilioEmpleado.DoesNotExist:
                    # Si no existe domicilio, crear uno nuevo
                    DomicilioEmpleado.objects.create(
                        empleado=solicitud.empleado,
                        calle=solicitud.datos_nuevos.get('calle', ''),
                        numero=solicitud.datos_nuevos.get('numero', ''),
                        piso=solicitud.datos_nuevos.get('piso', ''),
                        depto=solicitud.datos_nuevos.get('depto', ''),
                        barrio=solicitud.datos_nuevos.get('barrio', ''),
                        localidad=solicitud.datos_nuevos.get('localidad', ''),
                        provincia=solicitud.datos_nuevos.get('provincia', ''),
                        codigo_postal=solicitud.datos_nuevos.get('codigo_postal', ''),
                        entre_calles=solicitud.datos_nuevos.get('entre_calles', ''),
                        observaciones=solicitud.datos_nuevos.get('observaciones', '')
                    )
                    messages.success(request, 'Solicitud aprobada y domicilio creado correctamente.')
            else:
                messages.success(request, 'Solicitud aprobada correctamente.')
                
        elif accion == 'rechazar':
            solicitud.estado = 'rechazada'
            solicitud.fecha_resolucion = timezone.now()
            solicitud.revisado_por = request.user
            solicitud.observaciones_rrhh = request.POST.get('observaciones', '')
            messages.success(request, 'Solicitud rechazada correctamente.')
        
        solicitud.save()
        return redirect('rrhh:solicitudes')

class RecibosRRHHListView(LoginRequiredMixin, SoloRRHHMixin, TemplateView):
    template_name = 'rrhh/recibos.html'

class SubirReciboView(LoginRequiredMixin, SoloRRHHMixin, TemplateView):
    template_name = 'rrhh/subir_recibo.html'

class DocumentacionConfirmarListView(LoginRequiredMixin, SoloRRHHMixin, ListView):
    template_name = 'rrhh/documentacion_confirmar.html'
    model = Documento
    context_object_name = 'documentos'
    queryset = Documento.objects.filter(estado='pendiente')

class ConfirmarDocumentoView(LoginRequiredMixin, SoloRRHHMixin, DetailView):
    template_name = 'rrhh/confirmar_documento.html'
    model = Documento
    context_object_name = 'documento'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documento = self.object
        
        # Historial del documento
        context['historial'] = documento.historial.all().select_related('usuario').order_by('-fecha')
        
        # Información del empleado
        context['empleado'] = documento.empleado
        
        return context

@login_required
@require_POST
def aprobar_documento(request, documento_id):
    """Vista para aprobar un documento"""
    try:
        # Verificar permisos RRHH
        empleado_rrhh = Empleado.objects.get(user=request.user)
        if not empleado_rrhh.es_rrhh:
            return JsonResponse({'success': False, 'message': 'No tienes permisos para realizar esta acción'})
        
        documento = get_object_or_404(Documento, id=documento_id)
        
        # Obtener comentarios del formulario
        comentarios = request.POST.get('comentarios', '').strip()
        
        # Capturar estado anterior antes de cambiar
        estado_anterior = documento.estado
        
        # Actualizar documento
        documento.estado = 'aprobado'
        documento.revisado_por = request.user
        documento.fecha_revision = timezone.now()
        documento.observaciones_rrhh = comentarios
        documento.save()
        
        # Crear entrada en historial
        from apps.documentos.models import HistorialDocumento
        HistorialDocumento.objects.create(
            documento=documento,
            usuario=request.user,
            estado_anterior=estado_anterior,
            estado_nuevo='aprobado',
            observaciones=comentarios
        )
        
        # Registrar actividad
        from apps.empleados.models import ActividadEmpleado
        ActividadEmpleado.objects.create(
            empleado=documento.empleado,
            descripcion=f"Su documento '{documento.titulo}' fue aprobado por RRHH"
        )
        
        # Crear notificación para el empleado
        try:
            Notificacion.objects.crear_notificacion_documento_revisado(
                empleado=documento.empleado,
                documento=documento,
                estado='aprobado'
            )
        except Exception as e:
            print(f"Error al crear notificación: {e}")
        
        # Si el documento justifica una inasistencia, actualizar su estado
        if documento.inasistencia:
            inasistencia = documento.inasistencia
            nuevo_estado = inasistencia.actualizar_estado_segun_justificaciones()
            
            if nuevo_estado == 'justificada':
                # Registrar actividad adicional
                ActividadEmpleado.objects.create(
                    empleado=documento.empleado,
                    descripcion=f"Su inasistencia del {inasistencia.fecha_desde} al {inasistencia.fecha_hasta} fue marcada como justificada"
                )
        
        messages.success(request, f'Documento "{documento.titulo}" aprobado exitosamente.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Documento aprobado exitosamente'})
        
        return redirect('rrhh:documentos')
        
    except Empleado.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Usuario no autorizado'})
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
        messages.error(request, f'Error al aprobar documento: {str(e)}')
        return redirect('rrhh:documentos')

@login_required
@require_POST
def rechazar_documento(request, documento_id):
    """Vista para rechazar un documento"""
    try:
        # Verificar permisos RRHH
        empleado_rrhh = Empleado.objects.get(user=request.user)
        if not empleado_rrhh.es_rrhh:
            return JsonResponse({'success': False, 'message': 'No tienes permisos para realizar esta acción'})
        
        documento = get_object_or_404(Documento, id=documento_id)
        
        # Obtener comentarios del formulario (obligatorios para rechazo)
        comentarios = request.POST.get('comentarios', '').strip()
        if not comentarios:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Los comentarios son obligatorios para rechazar un documento'})
            messages.error(request, 'Los comentarios son obligatorios para rechazar un documento.')
            return redirect('rrhh:confirmar_documento', pk=documento_id)
        
        # Capturar estado anterior antes de cambiar
        estado_anterior = documento.estado
        
        # Actualizar documento
        documento.estado = 'rechazado'
        documento.revisado_por = request.user
        documento.fecha_revision = timezone.now()
        documento.observaciones_rrhh = comentarios
        documento.save()
        
        # Crear entrada en historial
        from apps.documentos.models import HistorialDocumento
        HistorialDocumento.objects.create(
            documento=documento,
            usuario=request.user,
            estado_anterior=documento.estado,
            estado_nuevo='rechazado',
            observaciones=comentarios
        )
        
        # Registrar actividad
        from apps.empleados.models import ActividadEmpleado
        ActividadEmpleado.objects.create(
            empleado=documento.empleado,
            descripcion=f"Su documento '{documento.titulo}' fue rechazado por RRHH. Motivo: {comentarios}"
        )
        
        # Crear notificación para el empleado
        try:
            Notificacion.objects.crear_notificacion_documento_revisado(
                empleado=documento.empleado,
                documento=documento,
                estado='rechazado'
            )
        except Exception as e:
            print(f"Error al crear notificación: {e}")
        
        # Si el documento justificaba una inasistencia, reevaluar su estado
        if documento.inasistencia:
            inasistencia = documento.inasistencia
            # Verificar si quedan documentos aprobados para esta inasistencia
            documentos_aprobados = inasistencia.documentos.filter(estado='aprobado').count()
            
            if documentos_aprobados == 0:
                # No quedan documentos aprobados, volver a injustificada
                if inasistencia.estado in ['pendiente', 'justificada']:
                    inasistencia.estado = 'injustificada'
                    inasistencia.save()
                    
                    # Registrar actividad adicional
                    ActividadEmpleado.objects.create(
                        empleado=documento.empleado,
                        descripcion=f"Su inasistencia del {inasistencia.fecha_desde} al {inasistencia.fecha_hasta} volvió a estado injustificada"
                    )
        
        messages.success(request, f'Documento "{documento.titulo}" rechazado.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Documento rechazado'})
        
        return redirect('rrhh:documentos')
        
    except Empleado.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Usuario no autorizado'})
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
        messages.error(request, f'Error al rechazar documento: {str(e)}')
        return redirect('rrhh:documentos')

@login_required
@require_POST 
def solicitar_aclaracion_documento(request, documento_id):
    """Vista para solicitar aclaración sobre un documento"""
    try:
        # Verificar permisos RRHH
        empleado_rrhh = Empleado.objects.get(user=request.user)
        if not empleado_rrhh.es_rrhh:
            return JsonResponse({'success': False, 'message': 'No tienes permisos para realizar esta acción'})
        
        documento = get_object_or_404(Documento, id=documento_id)
        
        # Obtener comentarios del formulario (obligatorios)
        comentarios = request.POST.get('comentarios', '').strip()
        if not comentarios:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Los comentarios son obligatorios para solicitar aclaración'})
            messages.error(request, 'Los comentarios son obligatorios para solicitar aclaración.')
            return redirect('rrhh:confirmar_documento', pk=documento_id)
        
        # Capturar estado anterior antes de cambiar
        estado_anterior = documento.estado
        
        # Actualizar documento
        documento.estado = 'requiere_aclaracion'
        documento.revisado_por = request.user
        documento.fecha_revision = timezone.now()
        documento.observaciones_rrhh = comentarios
        documento.save()
        
        # Crear entrada en historial
        from apps.documentos.models import HistorialDocumento
        HistorialDocumento.objects.create(
            documento=documento,
            usuario=request.user,
            estado_anterior=documento.estado,
            estado_nuevo='requiere_aclaracion',
            observaciones=comentarios
        )
        
        # Registrar actividad
        from apps.empleados.models import ActividadEmpleado
        ActividadEmpleado.objects.create(
            empleado=documento.empleado,
            descripcion=f"RRHH solicita aclaración sobre el documento '{documento.titulo}'. Comentarios: {comentarios}"
        )
        
        # Crear notificación para el empleado
        try:
            Notificacion.objects.crear_notificacion_documento_revisado(
                empleado=documento.empleado,
                documento=documento,
                estado='requiere_aclaracion'
            )
        except Exception as e:
            print(f"Error al crear notificación: {e}")
        
        messages.success(request, f'Se solicitó aclaración sobre el documento "{documento.titulo}".')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Aclaración solicitada'})
        
        return redirect('rrhh:documentos')
        
    except Empleado.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Usuario no autorizado'})
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
        messages.error(request, f'Error al solicitar aclaración: {str(e)}')
        return redirect('rrhh:documentos')

class SubirRecibosView(LoginRequiredMixin, SoloRRHHMixin, FormView):
    template_name = 'rrhh/subir_recibos.html'
    form_class = SubirRecibosForm
    success_url = reverse_lazy('rrhh:recibos')

    def form_valid(self, form):
        archivo = form.cleaned_data['archivo']
        import io
        from apps.recibos.models import ReciboSueldo
        from django.core.files.base import ContentFile
        from django.utils import timezone
        from apps.empleados.models import Empleado
        import re
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
        from io import BytesIO
        # Leer el archivo como texto
        contenido = archivo.read().decode('utf-8', errors='ignore')
        recibos = re.split(r'^={3,}.*={3,}$', contenido, flags=re.MULTILINE)
        procesados = 0
        for recibo_texto in recibos:
            # Buscar legajo después del CUIL (formato: XX-XXXXXXXX-X NUMERO)
            cuil_legajo_match = re.search(r'(\d{2}-\d{8}-\d)\s+(\d+)', recibo_texto)
            if cuil_legajo_match:
                legajo = cuil_legajo_match.group(2)
            else:
                # Buscar legajo con formato alternativo
                match = re.search(r'Legajo\s*:?\s*(EMP\d+|\d+)', recibo_texto)
                if not match:
                    continue
                legajo = match.group(1)
            
            # Buscar empleado por legajo
            try:
                if legajo.startswith('EMP'):
                    empleado = Empleado.objects.get(legajo=legajo)
                else:
                    # Si es solo número, buscar por numero_legajo o intentar con formato EMP
                    try:
                        empleado = Empleado.objects.get(numero_legajo=int(legajo))
                    except (Empleado.DoesNotExist, ValueError):
                        empleado = Empleado.objects.get(legajo=f'EMP{legajo.zfill(4)}')
            except Empleado.DoesNotExist:
                continue
            # Extraer período y año del recibo
            # Buscar fecha en formato dd/mm/yyyy
            fecha_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', recibo_texto)
            if fecha_match:
                fecha_str = fecha_match.group(1)
                from datetime import datetime
                fecha = datetime.strptime(fecha_str, '%d/%m/%Y')
                anio = fecha.year
                meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                        'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
                periodo = meses[fecha.month - 1]
            else:
                # Buscar período y año por separado
                periodo_match = re.search(r'Per[ií]odo\s*:?\s*(\w+)', recibo_texto)
                anio_match = re.search(r'A[nñ]o\s*:?\s*(\d{4})', recibo_texto)
                periodo = periodo_match.group(1).lower() if periodo_match else 'enero'
                anio = int(anio_match.group(1)) if anio_match else timezone.now().year
            
            # Extraer nombre del empleado
            nombre_match = re.search(r'([A-ZÁÉÍÓÚÑ\s]+),\s*([A-ZÁÉÍÓÚÑ\s]+)', recibo_texto)
            nombre_empleado = f"{nombre_match.group(2)} {nombre_match.group(1)}" if nombre_match else empleado.nombre
            
            # Generar PDF con formato mejorado
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            
            # Encabezado
            c.setFont("Helvetica-Bold", 16)
            c.drawString(30*mm, 280*mm, "RECIBO DE SUELDO")
            
            # Datos del empleado
            c.setFont("Helvetica", 10)
            c.drawString(30*mm, 265*mm, f"Empleado: {nombre_empleado}")
            c.drawString(30*mm, 260*mm, f"Legajo: {legajo}")
            c.drawString(30*mm, 255*mm, f"Período: {periodo.capitalize()} {anio}")
            
            # Línea separadora
            c.line(30*mm, 250*mm, 180*mm, 250*mm)
            
            # Contenido del recibo
            c.setFont("Helvetica", 9)
            y = 240
            for linea in recibo_texto.splitlines():
                linea = linea.strip()
                if linea:
                    c.drawString(30*mm, y*mm, linea)
                    y -= 4
                    if y < 20:
                        c.showPage()
                        c.setFont("Helvetica", 9)
                        y = 280
            
            c.save()
            buffer.seek(0)
            nombre_archivo = f"recibo_{periodo}_{anio}_{legajo}.pdf"
            archivo_pdf = ContentFile(buffer.read(), name=nombre_archivo)
            
            # Crear el recibo
            recibo = ReciboSueldo.objects.create(
                empleado=empleado,
                periodo=periodo,
                anio=anio,
                fecha_vencimiento=timezone.now(),
                archivo_pdf=archivo_pdf,
                subido_por=self.request.user
            )
            
            # ===================================================================
            # APLICAR FORMATO CENTROMÉDICA A TODOS LOS PDFs
            # ===================================================================
            try:
                print(f"🔄 Aplicando formato Centromédica a TODOS los archivos para legajo: {empleado.legajo}")
                print(f"📄 PDF original disponible: {bool(recibo.archivo_pdf)}")
                print(f"📄 Tamaño PDF original: {recibo.archivo_pdf.size if recibo.archivo_pdf else 'N/A'} bytes")
                
                pdf_con_formato = aplicar_formato_centromedica_a_pdf_original(recibo, empleado)
                
                if pdf_con_formato:
                    # REEMPLAZAR el archivo_pdf original con la versión formateada
                    nombre_archivo_con_formato = f"recibo_{periodo}_{anio}_{legajo}.pdf"
                    
                    # Eliminar el archivo original sin formato
                    if recibo.archivo_pdf:
                        recibo.archivo_pdf.delete(save=False)
                    
                    # Guardar el PDF CON FORMATO como archivo principal
                    recibo.archivo_pdf.save(
                        nombre_archivo_con_formato,
                        ContentFile(pdf_con_formato),
                        save=True
                    )
                    
                    # También guardarlo como archivo_pdf_centromedica para compatibilidad
                    nombre_archivo_centromedica = f"recibo_centromedica_{legajo}_{periodo}_{anio}.pdf"
                    recibo.archivo_pdf_centromedica.save(
                        nombre_archivo_centromedica,
                        ContentFile(pdf_con_formato),
                        save=True
                    )
                    
                    print(f"✅ Formato Centromédica aplicado a TODOS los archivos de {empleado.legajo}")
                    print(f"💾 Archivo principal: {nombre_archivo_con_formato}")
                    print(f"💾 Archivo Centromédica: {nombre_archivo_centromedica}")
                    print(f"📊 Tamaño PDF con formato: {len(pdf_con_formato)} bytes")
                else:
                    print(f"⚠️ No se pudo aplicar formato Centromédica a {empleado.legajo} - función retornó None")
                    
            except Exception as format_error:
                print(f"❌ Error aplicando formato Centromédica a {empleado.legajo}: {str(format_error)}")
                import traceback
                traceback.print_exc()
                # El proceso continúa aunque falle el formato
            
            procesados += 1
        messages.success(self.request, f'Recibos procesados: {procesados}')
        return super().form_valid(form)

class EditarDomicilioEmpleadoView(LoginRequiredMixin, SoloRRHHMixin, UpdateView):
    model = DomicilioEmpleado
    form_class = DomicilioEmpleadoForm
    template_name = 'rrhh/editar_domicilio.html'
    
    def get_object(self, queryset=None):
        empleado_pk = self.kwargs.get('empleado_pk')
        empleado = get_object_or_404(Empleado, pk=empleado_pk)
        domicilio, created = DomicilioEmpleado.objects.get_or_create(empleado=empleado)
        return domicilio
    
    def get_success_url(self):
        return reverse_lazy('rrhh:empleado_detail', kwargs={'pk': self.object.empleado.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Domicilio de {self.object.empleado.user.get_full_name()} actualizado exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empleado'] = self.object.empleado
        return context

@login_required
@xframe_options_exempt
def servir_pdf_declaracion(request, solicitud_id):
    """Vista para servir PDFs de declaraciones juradas de forma segura"""
    try:
        # Verificar que el usuario tenga permisos RRHH
        empleado = Empleado.objects.get(user=request.user)
        if not empleado.es_rrhh:
            return HttpResponse("No tienes permisos para acceder a este archivo", status=403)
        
        # Obtener la solicitud
        solicitud = get_object_or_404(SolicitudCambio, id=solicitud_id)
        
        # Debug: imprimir información
        print(f"Solicitud ID: {solicitud_id}")
        print(f"PDF field: {solicitud.pdf_declaracion}")
        print(f"PDF name: {solicitud.pdf_declaracion.name if solicitud.pdf_declaracion else 'None'}")
        
        # Verificar que tenga PDF
        if not solicitud.pdf_declaracion:
            return HttpResponse("No se encontró el archivo PDF", status=404)
        
        print(f"Intentando leer archivo PDF...")
        
        # Usar el mismo método que funciona en empleados
        response = HttpResponse(solicitud.pdf_declaracion.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="declaracion_{solicitud.tipo}_{solicitud_id}.pdf"'
        
        print(f"PDF servido exitosamente")
        return response
        
    except Empleado.DoesNotExist:
        return HttpResponse("Usuario no encontrado", status=404)
    except Exception as e:
        print(f"Error en servir_pdf_declaracion: {str(e)}")
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Error al acceder al archivo: {str(e)}", status=500)

# Vista principal de RRHH para recibos
class RRHHRecibosView(LoginRequiredMixin, TemplateView):
    """Vista principal de gestión de recibos para RRHH"""
    template_name = 'rrhh/recibos/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas de cargas masivas
        cargas_recientes = CargaMasivaRecibos.objects.all()[:5]
        total_cargas = CargaMasivaRecibos.objects.count()
        cargas_pendientes = CargaMasivaRecibos.objects.filter(estado='pendiente').count()
        cargas_error = CargaMasivaRecibos.objects.filter(estado='error').count()
        
        # Estadísticas de recibos
        total_recibos = ReciboSueldo.objects.count()
        recibos_pendientes = ReciboSueldo.objects.filter(estado='pendiente').count()
        recibos_firmados = ReciboSueldo.objects.filter(estado='firmado').count()
        recibos_observados = ReciboSueldo.objects.filter(estado='observado').count()
        
        context.update({
            'cargas_recientes': cargas_recientes,
            'total_cargas': total_cargas,
            'cargas_pendientes': cargas_pendientes,
            'cargas_error': cargas_error,
            'total_recibos': total_recibos,
            'recibos_pendientes': recibos_pendientes,
            'recibos_firmados': recibos_firmados,
            'recibos_observados': recibos_observados,
        })
        
        return context


class CargaMasivaCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear una nueva carga masiva de recibos"""
    model = CargaMasivaRecibos
    form_class = CargaMasivaRecibosForm
    template_name = 'rrhh/recibos/cargar_masivo.html'
    success_url = reverse_lazy('rrhh:recibos_dashboard')
    
    def form_valid(self, form):
        print(f"DEBUG: form_valid llamado")
        print(f"DEBUG: tipo_recibo = {form.cleaned_data.get('tipo_recibo')}")
        print(f"DEBUG: periodo = {form.cleaned_data.get('periodo')}")
        print(f"DEBUG: anio = {form.cleaned_data.get('anio')}")
        
        form.instance.usuario_carga = self.request.user
        response = super().form_valid(form)
        
        # Si es una petición AJAX, retornar JSON con el ID
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            print(f"DEBUG: Petición AJAX detectada")
            # Inicializar el estado
            self.object.estado = 'procesando'
            self.object.fecha_procesamiento = timezone.now()
            self.object.save()
            
            # Procesar el archivo en un hilo separado para no bloquear la respuesta
            def procesar_async():
                from django.db import connection
                try:
                    print(f"Iniciando procesamiento asíncrono para carga ID: {self.object.id}")
                    self.procesar_archivo_recibos(self.object)
                    print(f"Procesamiento completado para carga ID: {self.object.id}")
                except Exception as e:
                    print(f"Error en procesamiento asíncrono: {e}")
                    # Marcar como error
                    self.object.estado = 'error'
                    self.object.errores_procesamiento = str(e)
                    self.object.save()
                finally:
                    connection.close()
            
            print(f"Iniciando hilo de procesamiento para carga ID: {self.object.id}")
            threading.Thread(target=procesar_async, daemon=True).start()
            
            return JsonResponse({
                'success': True,
                'carga_id': self.object.id,
                'message': 'Archivo cargado exitosamente. El procesamiento ha comenzado.'
            })
        
        # Procesar el archivo en background (por ahora de forma síncrona)
        self.procesar_archivo_recibos(self.object)
        
        messages.success(self.request, 'Archivo cargado exitosamente. El procesamiento ha comenzado.')
        return response
    
    def form_invalid(self, form):
        print(f"DEBUG: form_invalid llamado")
        print(f"DEBUG: Errores del formulario: {form.errors}")
        
        # Si es una petición AJAX, retornar JSON con errores
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors,
                'message': 'Error en la validación del formulario'
            }, status=400)
        
        return super().form_invalid(form)
    
    def procesar_archivo_recibos(self, carga_masiva):
        """Procesa el archivo PDF y genera recibos individuales"""
        try:
            # El estado ya está configurado como 'procesando' antes de llamar a esta función
            
            # Obtener todos los empleados activos, excluyendo solo empleados sin datos válidos
            empleados = Empleado.objects.select_related('user').filter(
                user__first_name__isnull=False,  # Debe tener nombre
                user__last_name__isnull=False,   # Debe tener apellido
                user__first_name__gt='',         # Nombre no vacío
                user__last_name__gt='',          # Apellido no vacío
                legajo__isnull=False,            # Debe tener legajo
                legajo__gt=''                    # Legajo no vacío
            ).exclude(
                legajo__in=['LEG001', 'EMP0001', 'ADMIN', 'TEST']  # Excluir solo legajos administrativos específicos
            )
            carga_masiva.total_empleados = empleados.count()
            carga_masiva.save()
            
            recibos_generados = 0
            errores = []
            
            # Por cada empleado, verificar si existe en el PDF antes de crear el recibo
            for empleado in empleados:
                try:
                    # Verificar que no exista ya un recibo para este período y tipo
                    if ReciboSueldo.objects.filter(
                        empleado=empleado,
                        periodo=carga_masiva.periodo,
                        anio=carga_masiva.anio,
                        tipo_recibo=carga_masiva.tipo_recibo
                    ).exists():
                        LogProcesamientoRecibo.objects.create(
                            carga_masiva=carga_masiva,
                            legajo_empleado=empleado.legajo,
                            nombre_empleado=empleado.user.get_full_name(),
                            estado='error',
                            mensaje=f'Ya existe un recibo de {carga_masiva.get_tipo_recibo_display()} para {carga_masiva.periodo} {carga_masiva.anio}'
                        )
                        continue
                    
                    # PRIMERO verificar si el empleado tiene recibo en el PDF
                    paginas_encontradas = self.buscar_empleado_en_pdf(empleado, carga_masiva.archivo_pdf)
                    
                    if paginas_encontradas is not None:
                        # Solo crear el recibo si se encontró en el PDF
                        recibo = ReciboSueldo.objects.create(
                            empleado=empleado,
                            periodo=carga_masiva.periodo,
                            anio=carga_masiva.anio,
                            tipo_recibo=carga_masiva.tipo_recibo,
                            fecha_vencimiento=carga_masiva.fecha_vencimiento_calculada,
                            estado='pendiente',
                            subido_por=self.request.user
                        )
                        
                        # Generar PDFs individuales (original y centromédica)
                        recibo_generado = self.generar_pdf_individual_desde_pagina(recibo, carga_masiva.archivo_pdf, paginas_encontradas)
                        
                        if recibo_generado:
                            recibos_generados += 1
                            pagina_original = paginas_encontradas['pagina_original']
                            pagina_centromedica = paginas_encontradas.get('pagina_centromedica')
                            mensaje_paginas = f'página original {pagina_original + 1}'
                            if pagina_centromedica is not None:
                                mensaje_paginas += f' y página Centromédica {pagina_centromedica + 1}'
                            
                            LogProcesamientoRecibo.objects.create(
                                carga_masiva=carga_masiva,
                                legajo_empleado=empleado.legajo,
                                nombre_empleado=empleado.user.get_full_name(),
                                estado='exitoso',
                                mensaje=f'Recibo de {carga_masiva.get_tipo_recibo_display()} generado exitosamente ({mensaje_paginas})'
                            )
                        else:
                            # Si falla la generación del PDF, eliminar el recibo
                            recibo.delete()
                            LogProcesamientoRecibo.objects.create(
                                carga_masiva=carga_masiva,
                                legajo_empleado=empleado.legajo,
                                nombre_empleado=empleado.user.get_full_name(),
                                estado='error',
                                mensaje=f'Error al generar PDF individual'
                            )
                            errores.append(f"Empleado {empleado.legajo} ({empleado.user.get_full_name()}): Error al generar PDF")
                    else:
                        # NO crear recibo si no se encuentra en el PDF - solo log
                        LogProcesamientoRecibo.objects.create(
                            carga_masiva=carga_masiva,
                            legajo_empleado=empleado.legajo,
                            nombre_empleado=empleado.user.get_full_name(),
                            estado='no_encontrado',
                            mensaje=f'No se encontró recibo para este empleado en el PDF. DEBE ser revisado manualmente por RRHH.'
                        )
                        errores.append(f"Empleado {empleado.legajo} ({empleado.user.get_full_name()}): No se encontró en el PDF - NO SE CREÓ RECIBO")
                    
                except Exception as e:
                    errores.append(f"Error con empleado {empleado.legajo}: {str(e)}")
                    LogProcesamientoRecibo.objects.create(
                        carga_masiva=carga_masiva,
                        legajo_empleado=empleado.legajo,
                        nombre_empleado=empleado.user.get_full_name(),
                        estado='error',
                        mensaje=str(e)
                    )
            
            # Actualizar el estado de la carga
            carga_masiva.recibos_generados = recibos_generados
            carga_masiva.errores_procesamiento = '\n'.join(errores) if errores else ''
            carga_masiva.estado = 'completado' if not errores else 'error'
            carga_masiva.save()
            
            # ===================================================================
            # LIMPIEZA GENERAL DE ARCHIVOS TEMPORALES
            # ===================================================================
            try:
                import os
                import glob
                from django.conf import settings
                
                media_root = getattr(settings, 'MEDIA_ROOT', None)
                if media_root:
                    recibos_dir = os.path.join(media_root, 'recibos_sueldos')
                    if os.path.exists(recibos_dir):
                        # Buscar todos los archivos temporales con patrones específicos
                        temp_patterns = [
                            'temp_original_*.pdf',
                            'temp_centromedica_*.pdf'
                        ]
                        
                        archivos_eliminados = 0
                        for pattern in temp_patterns:
                            pattern_path = os.path.join(recibos_dir, pattern)
                            temp_files = glob.glob(pattern_path)
                            
                            for temp_file in temp_files:
                                try:
                                    os.remove(temp_file)
                                    archivos_eliminados += 1
                                    print(f"🗑️ Archivo temporal eliminado: {os.path.basename(temp_file)}")
                                except Exception as cleanup_error:
                                    print(f"⚠️ Error eliminando {os.path.basename(temp_file)}: {str(cleanup_error)}")
                        
                        if archivos_eliminados > 0:
                            print(f"🧹 Limpieza completada: {archivos_eliminados} archivos temporales eliminados")
                        else:
                            print(f"ℹ️ No se encontraron archivos temporales para eliminar")
                            
            except Exception as cleanup_error:
                print(f"⚠️ Error durante limpieza general de archivos temporales: {str(cleanup_error)}")
            
        except Exception as e:
            carga_masiva.estado = 'error'
            carga_masiva.errores_procesamiento = str(e)
            carga_masiva.save()
    
    def buscar_empleado_en_pdf(self, empleado, archivo_masivo):
        """Busca un empleado específico en el PDF usando CUIL + nombre - BÚSQUEDA SEGURA"""
        try:
            # Filtro adicional: no procesar empleados administrativos (pero SÍ empleados de RRHH)
            if empleado.legajo in ['LEG001', 'EMP0001', 'ADMIN', 'TEST']:
                print(f"Empleado administrativo no procesado: {empleado.legajo}")
                return None
                
            archivo_masivo.seek(0)
            reader = PdfReader(archivo_masivo)
            
            # Validaciones previas: verificar que el empleado tenga datos válidos
            empleado_cuil = empleado.cuil.strip() if empleado.cuil else ""
            empleado_apellido = empleado.user.last_name.upper().strip() if empleado.user.last_name else ""
            empleado_nombre = empleado.user.first_name.upper().strip() if empleado.user.first_name else ""
            
            # Si el empleado no tiene CUIL válido o nombre/apellido, no buscar
            if not empleado_cuil or len(empleado_cuil) < 11:
                print(f"Empleado sin CUIL válido: {empleado.user.get_full_name()} - CUIL: '{empleado_cuil}'")
                return None
                
            if not empleado_apellido or not empleado_nombre:
                print(f"Empleado sin nombre/apellido válido: {empleado.legajo} - '{empleado_nombre}' '{empleado_apellido}'")
                return None
            
            # VALIDACIONES ADICIONALES: nombres muy cortos o genéricos no son confiables
            if len(empleado_apellido) < 3 or len(empleado_nombre) < 3:
                print(f"Empleado con nombre/apellido demasiado corto para coincidencia confiable: {empleado.legajo} - '{empleado_nombre}' '{empleado_apellido}'")
                return None
            
            print(f"Buscando empleado: {empleado_apellido}, {empleado_nombre} (CUIL: {empleado_cuil})")
            
            # NUEVA ESTRATEGIA SEGURA: Buscar CUIL + validar que el nombre esté cerca
            for i, page in enumerate(reader.pages):
                try:
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    # Normalizar el texto para búsqueda
                    text_upper = text.upper()
                    
                    # Buscar el CUIL específico
                    if empleado_cuil in text_upper:
                        print(f"CUIL {empleado_cuil} encontrado en página {i+1}")
                        
                        # Verificar que el nombre también esté en la misma página
                        # Ser flexible con los espacios alrededor de la coma
                        patrones_nombre = [
                            f"{empleado_apellido}, {empleado_nombre}",      # Formato normal
                            f"{empleado_apellido} , {empleado_nombre}",     # Con espacio antes de coma
                            f"{empleado_apellido},{empleado_nombre}",       # Sin espacio después de coma
                            f"{empleado_apellido} ,{empleado_nombre}",      # Espacio antes, no después
                        ]
                        
                        nombre_encontrado = False
                        for patron in patrones_nombre:
                            if patron in text_upper:
                                print(f"Nombre encontrado con patrón: '{patron}' en página {i+1}")
                                nombre_encontrado = True
                                break
                        
                        if nombre_encontrado:
                            print(f"COINCIDENCIA EXACTA ENCONTRADA - {empleado_apellido}, {empleado_nombre} (CUIL: {empleado_cuil}) en página {i+1}")
                            
                            # Verificar si existe la página siguiente (recibo firmado por Centromédica)
                            pagina_centromedica = i + 1 if i + 1 < len(reader.pages) else None
                            
                            return {
                                'pagina_original': i,
                                'pagina_centromedica': pagina_centromedica
                            }
                        else:
                            print(f"CUIL encontrado pero nombre NO coincide en página {i+1}")
                            # Debug: mostrar fragmento del texto para verificar
                            fragmento = text_upper[:500] if len(text_upper) > 500 else text_upper
                            print(f"Fragmento de texto: {fragmento}")
                        
                except Exception as e:
                    print(f"Error en búsqueda para página {i}: {str(e)}")
                    continue
            
            # NO encontrado - retornar None
            print(f"NO ENCONTRADO - {empleado_apellido}, {empleado_nombre} (CUIL: {empleado_cuil}) NO tiene coincidencia exacta en el PDF")
            return None
            
        except Exception as e:
            print(f"Error buscando empleado en PDF: {str(e)}")
            return None

    
    def generar_pdf_individual_desde_pagina(self, recibo, archivo_masivo, paginas_info):
        """Genera PDFs individuales extrayendo las páginas específicas del PDF masivo"""
        try:
            archivo_masivo.seek(0)
            reader = PdfReader(archivo_masivo)
            
            pagina_original = paginas_info['pagina_original']
            pagina_centromedica = paginas_info['pagina_centromedica']
            
            if pagina_original >= len(reader.pages):
                return False
            
            # ===================================================================
            # EXTRAER PÁGINA 1: PARA EL EMPLEADO
            # ===================================================================
            
            # PASO 1: Extraer página sin formato para que firme el empleado
            writer_empleado = PdfWriter()
            writer_empleado.add_page(reader.pages[pagina_original])
            
            output_buffer_empleado = BytesIO()
            writer_empleado.write(output_buffer_empleado)
            output_buffer_empleado.seek(0)
            
            # Guardar temporalmente para aplicar formato después
            nombre_archivo_empleado = f"recibo_empleado_{recibo.empleado.legajo}_{recibo.periodo}_{recibo.anio}.pdf"
            recibo.archivo_pdf.save(
                nombre_archivo_empleado,
                ContentFile(output_buffer_empleado.getvalue()),
                save=True
            )
            print(f"📄 PDF temporal guardado para aplicar formato a {recibo.empleado.legajo}")
            
            # ===================================================================
            # PASO 2: APLICAR FORMATO A LA PÁGINA DEL EMPLEADO (archivo_pdf)
            # ===================================================================
            try:
                print(f"🔄 Aplicando formato Centromédica a página del empleado de {recibo.empleado.legajo}")
                
                from apps.recibos.views import generar_pdf_formato_centromedica_test
                
                # Aplicar formato usando el archivo que acabamos de guardar (página 1)
                pdf_empleado_con_formato = generar_pdf_formato_centromedica_test(recibo, recibo.empleado)
                
                if pdf_empleado_con_formato and len(pdf_empleado_con_formato) > 1000:
                    # REEMPLAZAR el archivo_pdf original con la versión formateada
                    if recibo.archivo_pdf:
                        recibo.archivo_pdf.delete(save=False)
                    
                    # Guardar PDF CON FORMATO como archivo principal (archivo_pdf)
                    recibo.archivo_pdf.save(
                        nombre_archivo_empleado,
                        ContentFile(pdf_empleado_con_formato),
                        save=True
                    )
                    
                    print(f"✅ PDF del empleado CON FORMATO guardado: {nombre_archivo_empleado}")
                    print(f"📊 Tamaño PDF empleado con formato: {len(pdf_empleado_con_formato)} bytes")
                else:
                    print(f"⚠️ Error aplicando formato a página del empleado para {recibo.empleado.legajo}")
                    
            except Exception as format_error:
                print(f"❌ Error aplicando formato a página del empleado {recibo.empleado.legajo}: {str(format_error)}")
            
            # ===================================================================
            # PASO 3: PROCESAR PÁGINA 2 DE CENTROMÉDICA (archivo_pdf_centromedica)
            # ===================================================================
            pagina_centromedica_real = paginas_info.get('pagina_centromedica')
            if pagina_centromedica_real is not None and pagina_centromedica_real < len(reader.pages):
                print(f"📄 Procesando página {pagina_centromedica_real + 1} (firmada por Centromédica)")
                
                try:
                    # Extraer la página de Centromédica del archivo masivo
                    writer_centromedica = PdfWriter()
                    writer_centromedica.add_page(reader.pages[pagina_centromedica_real])
                    
                    # Crear PDF en memoria
                    output_buffer_centromedica = BytesIO()
                    writer_centromedica.write(output_buffer_centromedica)
                    output_buffer_centromedica.seek(0)
                    
                    # Crear un objeto temporal para aplicar formato a la página de Centromédica
                    class TempArchivoPDF:
                        def __init__(self, buffer):
                            self.buffer = buffer
                        
                        def read(self, size=-1):
                            if size == -1:
                                return self.buffer.getvalue()
                            else:
                                current_pos = self.buffer.tell()
                                data = self.buffer.read(size)
                                return data
                        
                        def seek(self, pos, whence=0):
                            return self.buffer.seek(pos, whence)
                        
                        def tell(self):
                            return self.buffer.tell()
                    
                    recibo_temp_centromedica = type('ReciboCentromedica', (), {})()
                    recibo_temp_centromedica.archivo_pdf = TempArchivoPDF(output_buffer_centromedica)
                    
                    # Aplicar formato a la página de Centromédica
                    print(f"🎨 Aplicando formato a la página firmada por Centromédica")
                    pdf_centromedica_con_formato = generar_pdf_formato_centromedica_test(recibo_temp_centromedica, recibo.empleado)
                    
                    if pdf_centromedica_con_formato and len(pdf_centromedica_con_formato) > 1000:
                        # Guardar la página de Centromédica formateada
                        nombre_archivo_centromedica = f"recibo_centromedica_{recibo.empleado.legajo}_{recibo.periodo}_{recibo.anio}.pdf"
                        recibo.archivo_pdf_centromedica.save(
                            nombre_archivo_centromedica,
                            ContentFile(pdf_centromedica_con_formato),
                            save=True
                        )
                        print(f"✅ PDF de Centromédica CON FORMATO guardado: {nombre_archivo_centromedica}")
                        print(f"📊 Tamaño PDF Centromédica con formato: {len(pdf_centromedica_con_formato)} bytes")
                    else:
                        # Fallback: guardar la página de Centromédica sin formato
                        print(f"⚠️ Error aplicando formato, guardando página de Centromédica sin formato")
                        nombre_archivo_centromedica = f"recibo_centromedica_{recibo.empleado.legajo}_{recibo.periodo}_{recibo.anio}.pdf"
                        recibo.archivo_pdf_centromedica.save(
                            nombre_archivo_centromedica,
                            ContentFile(output_buffer_centromedica.getvalue()),
                            save=True
                        )
                        
                    output_buffer_centromedica.close()
                    
                except Exception as centromedica_error:
                    print(f"❌ Error procesando página de Centromédica: {str(centromedica_error)}")
                    
            else:
                print(f"� Solo hay una página por empleado, no hay página firmada por Centromédica")
                # Si no hay página 2, crear una copia del archivo del empleado para compatibilidad
                if recibo.archivo_pdf:
                    try:
                        recibo.archivo_pdf.seek(0)
                        pdf_empleado_content = recibo.archivo_pdf.read()
                        nombre_archivo_centromedica = f"recibo_centromedica_{recibo.empleado.legajo}_{recibo.periodo}_{recibo.anio}.pdf"
                        recibo.archivo_pdf_centromedica.save(
                            nombre_archivo_centromedica,
                            ContentFile(pdf_empleado_content),
                            save=True
                        )
                        print(f"📋 Archivo de compatibilidad creado: {nombre_archivo_centromedica}")
                    except Exception as copy_error:
                        print(f"⚠️ Error creando archivo de compatibilidad: {str(copy_error)}")
            
            # Limpiar buffer empleado
            output_buffer_empleado.close()
            
            # ===================================================================
            # LIMPIEZA DE ARCHIVOS TEMPORALES EXISTENTES (POR SEGURIDAD)
            # ===================================================================
            # NOTA: Ya no creamos archivos temporales, pero limpiamos cualquiera que pueda existir de versiones anteriores
            try:
                # Limpiar archivos temporales que puedan haber quedado
                import os
                from django.conf import settings
                
                # Patrones de archivos temporales a limpiar
                temp_patterns = [
                    f"temp_original_{recibo.empleado.legajo}_{recibo.periodo}_{recibo.anio}.pdf",
                    f"temp_centromedica_{recibo.empleado.legajo}.pdf"
                ]
                
                media_root = getattr(settings, 'MEDIA_ROOT', None)
                if media_root:
                    recibos_dir = os.path.join(media_root, 'recibos_sueldos')
                    if os.path.exists(recibos_dir):
                        for pattern in temp_patterns:
                            temp_file_path = os.path.join(recibos_dir, pattern)
                            if os.path.exists(temp_file_path):
                                try:
                                    os.remove(temp_file_path)
                                    print(f"🗑️ Archivo temporal eliminado: {pattern}")
                                except Exception as cleanup_error:
                                    print(f"⚠️ Error eliminando archivo temporal {pattern}: {str(cleanup_error)}")
                
            except Exception as cleanup_error:
                print(f"⚠️ Error durante limpieza de archivos temporales: {str(cleanup_error)}")
            
            print(f"✅ Procesamiento completo para empleado {recibo.empleado.legajo}")
            return True
            
        except Exception as e:
            print(f"Error generando PDFs individuales: {str(e)}")
            return False
    
    def generar_pdf_individual(self, recibo, archivo_masivo):
        """Genera un PDF individual para un empleado extrayendo su página específica - BÚSQUEDA MUY ESTRICTA"""
        try:
            archivo_masivo.seek(0)
            reader = PdfReader(archivo_masivo)
            
            empleado_legajo = recibo.empleado.legajo
            empleado_apellido = recibo.empleado.user.last_name.upper().strip() if recibo.empleado.user.last_name else ""
            empleado_nombre = recibo.empleado.user.first_name.upper().strip() if recibo.empleado.user.first_name else ""
            empleado_dni = recibo.empleado.dni if hasattr(recibo.empleado, 'dni') and recibo.empleado.dni else None
            
            # Validaciones previas
            if not empleado_legajo or not empleado_apellido or not empleado_nombre:
                print(f"Error: Empleado {empleado_legajo} tiene datos incompletos")
                return False
            
            # VALIDACIONES ADICIONALES: nombres muy cortos o genéricos no son confiables
            if len(empleado_apellido) < 3 or len(empleado_nombre) < 3:
                print(f"Error: Empleado con nombre/apellido demasiado corto para coincidencia confiable: {empleado_legajo} - '{empleado_nombre}' '{empleado_apellido}'")
                return False
            
            pagina_empleado = None
            encontrado_especifico = False
            
            print(f"Generando PDF para empleado: {empleado_apellido}, {empleado_nombre} (legajo: {empleado_legajo})")
            
            # ÚNICA ESTRATEGIA ESTRICTA: Buscar EXACTAMENTE el patrón APELLIDO, NOMBRE seguido de CUIL y legajo
            for i, page in enumerate(reader.pages):
                try:
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    # Normalizar el texto para búsqueda
                    text_upper = text.upper()
                    lines = text_upper.split('\n')
                    
                    # Buscar el patrón EXACTO: "APELLIDO, NOMBRE" seguido de CUIL y el legajo específico
                    apellido_nombre_exacto = f"{empleado_apellido}, {empleado_nombre}"
                    
                    # Verificar que el patrón completo esté presente
                    encontrado_nombre_completo = False
                    linea_nombre = -1
                    
                    for j, line in enumerate(lines):
                        if apellido_nombre_exacto in line:
                            encontrado_nombre_completo = True
                            linea_nombre = j
                            print(f"Encontrado nombre completo exacto en línea {j}: {line.strip()}")
                            break
                    
                    if not encontrado_nombre_completo:
                        continue  # Si no se encuentra el nombre completo exacto, continuar con la siguiente página
                    
                    # Verificar que el legajo aparezca después del nombre (en la misma línea o líneas siguientes)
                    legajo_encontrado = False
                    for k in range(linea_nombre, min(linea_nombre + 3, len(lines))):
                        line = lines[k]
                        
                        # Buscar el legajo de forma exacta
                        # Método 1: Después de un CUIL (patrón: XX-XXXXXXXX-X LEGAJO)
                        cuil_legajo_pattern = rf"(\d{{2}}-\d{{7,8}}-\d)\s+{re.escape(empleado_legajo)}(\s|$)"
                        if re.search(cuil_legajo_pattern, line):
                            legajo_encontrado = True
                            print(f"Encontrado legajo después de CUIL en línea {k}: {line.strip()}")
                            break
                        
                        # Método 2: Como número aislado (asegurarse que es exacto)
                        # Solo buscar si es un número aislado, no parte de otro número
                        legajo_aislado_pattern = rf"(^|\s){re.escape(empleado_legajo)}(\s|$)"
                        if re.search(legajo_aislado_pattern, line):
                            # Verificación adicional: asegurarse que no es parte de un CUIL u otro número
                            if not re.search(rf"\d-{re.escape(empleado_legajo)}-\d", line):  # No es parte de un CUIL
                                legajo_encontrado = True
                                print(f"Encontrado legajo aislado en línea {k}: {line.strip()}")
                                break
                    
                    if legajo_encontrado:
                        pagina_empleado = i
                        encontrado_especifico = True
                        print(f"COINCIDENCIA EXACTA ENCONTRADA - {empleado_apellido}, {empleado_nombre} (legajo {empleado_legajo}) en página {i+1}")
                        break
                    else:
                        print(f"Nombre encontrado pero legajo NO coincide para {empleado_apellido}, {empleado_nombre}")
                        
                except Exception as e:
                    print(f"Error en búsqueda para página {i}: {str(e)}")
                    continue
            
            # Solo generar PDF si se encontró específicamente
            if pagina_empleado is not None and encontrado_especifico:
                # Crear un nuevo PDF con solo la página del empleado
                writer = PdfWriter()
                writer.add_page(reader.pages[pagina_empleado])
                
                # Guardar el PDF individual
                output_buffer = BytesIO()
                writer.write(output_buffer)
                output_buffer.seek(0)
                
                filename = f"recibo_{recibo.periodo}_{recibo.anio}_{recibo.empleado.legajo}.pdf"
                recibo.archivo_pdf.save(filename, output_buffer)
                
                # Log para debug
                print(f"PDF generado exitosamente para {empleado_apellido}, {empleado_nombre} (legajo {empleado_legajo}) desde página {pagina_empleado + 1}")
                
                return True
            else:
                # NO generar PDF si no se encontró específicamente
                print(f"NO SE GENERA PDF - {empleado_apellido}, {empleado_nombre} (legajo {empleado_legajo}) NO tiene coincidencia exacta en el PDF")
                return False
            
        except Exception as e:
            print(f"Error en generar_pdf_individual: {str(e)}")
            return False


class CargaMasivaListView(LoginRequiredMixin, ListView):
    """Vista para listar todas las cargas masivas"""
    model = CargaMasivaRecibos
    template_name = 'rrhh/recibos/lista_cargas.html'
    context_object_name = 'cargas'
    paginate_by = 20
    ordering = ['-fecha_carga']


class CargaMasivaDetailView(LoginRequiredMixin, DetailView):
    """Vista para ver detalles de una carga masiva"""
    model = CargaMasivaRecibos
    template_name = 'rrhh/recibos/detalle_carga.html'
    context_object_name = 'carga'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['logs'] = self.object.logs_procesamiento.all()[:50]
        context['recibos'] = self.object.get_recibos_generados()
        return context

@login_required
@require_POST  
def validar_carga_masiva(request, pk):
    """Validar una carga masiva de recibos"""
    carga = get_object_or_404(CargaMasivaRecibos, pk=pk)
    
    # Permitir validar si hay recibos generados, incluso si hay errores
    if carga.recibos_generados == 0:
        return JsonResponse({
            'success': False,
            'message': 'No se pueden validar cargas sin recibos generados exitosamente.'
        })
    
    if carga.validado:
        return JsonResponse({
            'success': False,
            'message': 'Esta carga ya fue validada anteriormente.'
        })
    
    # Validar la carga
    carga.validado = True
    carga.fecha_validacion = timezone.now()
    carga.validado_por = request.user
    carga.save()
    
    messages.success(request, 'Carga validada exitosamente. Ahora puedes hacer visibles los recibos para los empleados.')
    
    return JsonResponse({
        'success': True,
        'message': 'Carga validada exitosamente.',
        'redirect_url': reverse('rrhh:detalle_carga_masiva', kwargs={'pk': pk})
    })


@login_required
@require_POST
def hacer_visible_recibos(request, pk):
    """Hacer visibles los recibos de una carga para los empleados"""
    carga = get_object_or_404(CargaMasivaRecibos, pk=pk)
    
    if not carga.puede_hacer_visible:
        return JsonResponse({
            'success': False,
            'message': 'Los recibos no pueden hacerse visibles en este momento.'
        })
    
    # Hacer visibles los recibos
    carga.visible_empleados = True
    carga.save()
    
    # Opcional: Enviar notificaciones a los empleados
    # Aquí podrías agregar lógica para notificar a los empleados
    
    messages.success(request, 'Los recibos ahora son visibles para los empleados.')
    
    return JsonResponse({
        'success': True,
        'message': 'Los recibos ahora son visibles para los empleados.',
        'redirect_url': reverse('rrhh:detalle_carga_masiva', kwargs={'pk': pk})
    })

@login_required
@require_POST
def eliminar_carga_masiva(request, pk):
    """Eliminar una carga masiva de recibos y todos los recibos generados"""
    carga = get_object_or_404(CargaMasivaRecibos, pk=pk)
    
    # Solo se puede eliminar si no está validada
    if carga.validado:
        return JsonResponse({
            'success': False,
            'message': 'No se puede eliminar una carga que ya fue validada.'
        })
    
    try:
        # Eliminar todos los recibos generados por esta carga
        recibos_eliminados = 0
        recibos = carga.get_recibos_generados()
        
        for recibo in recibos:
            # Eliminar archivos PDF asociados
            if recibo.archivo_pdf:
                try:
                    recibo.archivo_pdf.delete(save=False)
                except Exception:
                    pass  # Continuar aunque falle la eliminación del archivo
            
            if recibo.archivo_pdf_centromedica:
                try:
                    recibo.archivo_pdf_centromedica.delete(save=False)
                except Exception:
                    pass
            
            if recibo.archivo_firmado:
                try:
                    recibo.archivo_firmado.delete(save=False)
                except Exception:
                    pass
            
            recibo.delete()
            recibos_eliminados += 1
        
        # Eliminar logs de procesamiento
        carga.logs_procesamiento.all().delete()
        
        # Eliminar archivo PDF original
        if carga.archivo_pdf:
            try:
                carga.archivo_pdf.delete(save=False)
            except Exception:
                pass
        
        # Eliminar la carga masiva
        periodo_anio = f"{carga.get_periodo_display()} {carga.anio}"
        carga.delete()
        
        # ===================================================================
        # LIMPIEZA DE ARCHIVOS TEMPORALES RELACIONADOS
        # ===================================================================
        try:
            import os
            import glob
            from django.conf import settings
            
            media_root = getattr(settings, 'MEDIA_ROOT', None)
            if media_root:
                recibos_dir = os.path.join(media_root, 'recibos_sueldos')
                if os.path.exists(recibos_dir):
                    # Buscar archivos temporales que puedan estar relacionados con esta carga
                    temp_patterns = [
                        'temp_original_*.pdf',
                        'temp_centromedica_*.pdf'
                    ]
                    
                    archivos_temporales_eliminados = 0
                    for pattern in temp_patterns:
                        pattern_path = os.path.join(recibos_dir, pattern)
                        temp_files = glob.glob(pattern_path)
                        
                        for temp_file in temp_files:
                            try:
                                os.remove(temp_file)
                                archivos_temporales_eliminados += 1
                            except Exception:
                                pass  # Ignorar errores de limpieza
                    
                    if archivos_temporales_eliminados > 0:
                        print(f"🧹 Eliminados {archivos_temporales_eliminados} archivos temporales durante la limpieza de la carga")
                        
        except Exception:
            pass  # No fallar la eliminación por errores de limpieza
        
        messages.success(request, f'Carga masiva de {periodo_anio} eliminada exitosamente. Se eliminaron {recibos_eliminados} recibos.')
        
        return JsonResponse({
            'success': True,
            'message': f'Carga eliminada exitosamente. Se eliminaron {recibos_eliminados} recibos.',
            'redirect_url': reverse('rrhh:lista_cargas_masivas')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al eliminar la carga: {str(e)}'
        })

@login_required
@require_POST
def corregir_recibo_no_encontrado(request, pk):
    """Corregir un recibo marcado como 'no_encontrado' después de revisión manual"""
    from apps.recibos.models import ReciboSueldo
    
    recibo = get_object_or_404(ReciboSueldo, pk=pk)
    
    # Solo se pueden corregir recibos en estado 'no_encontrado'
    if recibo.estado != 'no_encontrado':
        return JsonResponse({
            'success': False,
            'message': 'Solo se pueden corregir recibos en estado "No Encontrado".'
        })
    
    # Verificar que el usuario tenga permisos RRHH
    try:
        empleado_rrhh = Empleado.objects.get(user=request.user)
        if not empleado_rrhh.es_rrhh:
            return JsonResponse({
                'success': False,
                'message': 'No tienes permisos para realizar esta acción.'
            })
    except Empleado.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Usuario no encontrado.'
        })
    
    try:
        # Cambiar estado a pendiente
        recibo.estado = 'pendiente'
        recibo.save()
        
        # Registrar la corrección en el log
        from apps.rrhh.models import CargaMasivaRecibos, LogProcesamientoRecibo
        
        # Encontrar la carga masiva correspondiente
        carga_masiva = CargaMasivaRecibos.objects.filter(
            periodo=recibo.periodo,
            anio=recibo.anio,
            usuario_carga=recibo.subido_por
        ).first()
        
        if carga_masiva:
            LogProcesamientoRecibo.objects.create(
                carga_masiva=carga_masiva,
                legajo_empleado=recibo.empleado.legajo,
                nombre_empleado=recibo.empleado.user.get_full_name(),
                estado='exitoso',
                mensaje=f'Recibo corregido manualmente por {request.user.get_full_name()} - Estado cambiado de "No Encontrado" a "Pendiente"'
            )
        
        messages.success(request, f'Recibo de {recibo.empleado.user.get_full_name()} corregido exitosamente.')
        
        return JsonResponse({
            'success': True,
            'message': 'Recibo corregido exitosamente.',
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al corregir el recibo: {str(e)}'
        })


# Vista para gestionar inasistencias desde RRHH
class InasistenciasRRHHListView(LoginRequiredMixin, SoloRRHHMixin, ListView):
    """Vista para listar y gestionar inasistencias desde RRHH"""
    template_name = 'rrhh/inasistencias.html'
    model = Inasistencia
    context_object_name = 'inasistencias'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Inasistencia.objects.select_related('empleado__user').order_by('-fecha_desde')
        
        # Filtros
        empleado_search = self.request.GET.get('empleado')
        estado = self.request.GET.get('estado')
        tipo = self.request.GET.get('tipo')
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        
        if empleado_search:
            queryset = queryset.filter(
                Q(empleado__user__first_name__icontains=empleado_search) |
                Q(empleado__user__last_name__icontains=empleado_search) |
                Q(empleado__legajo__icontains=empleado_search)
            )
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        if fecha_desde:
            queryset = queryset.filter(fecha_desde__gte=fecha_desde)
        
        if fecha_hasta:
            queryset = queryset.filter(fecha_hasta__lte=fecha_hasta)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas
        total_inasistencias = self.get_queryset().count()
        pendientes = self.get_queryset().filter(estado='pendiente').count()
        justificadas = self.get_queryset().filter(estado='justificada').count()
        injustificadas = self.get_queryset().filter(estado='injustificada').count()
        
        context.update({
            'total_inasistencias': total_inasistencias,
            'pendientes': pendientes,
            'justificadas': justificadas,
            'injustificadas': injustificadas,
            'tipos_inasistencia': Inasistencia.TIPO_CHOICES,
            'estados_inasistencia': Inasistencia.ESTADO_CHOICES,
            # Filtros actuales
            'empleado_search': self.request.GET.get('empleado', ''),
            'estado_selected': self.request.GET.get('estado', ''),
            'tipo_selected': self.request.GET.get('tipo', ''),
            'fecha_desde_selected': self.request.GET.get('fecha_desde', ''),
            'fecha_hasta_selected': self.request.GET.get('fecha_hasta', ''),
        })
        
        return context


class CrearInasistenciaView(LoginRequiredMixin, SoloRRHHMixin, CreateView):
    """Vista para crear una nueva inasistencia desde RRHH"""
    model = Inasistencia
    form_class = CrearInasistenciaForm
    template_name = 'rrhh/crear_inasistencia.html'
    success_url = reverse_lazy('rrhh:inasistencias')
    
    def form_valid(self, form):
        # Establecer quien creó la inasistencia
        form.instance.creado_por = self.request.user
        
        response = super().form_valid(form)
        
        # Crear notificación para el empleado
        try:
            Notificacion.objects.crear_notificacion_inasistencia(
                empleado=self.object.empleado,
                inasistencia=self.object
            )
        except Exception as e:
            # Log del error pero no fallar la creación de la inasistencia
            print(f"Error al crear notificación: {e}")
        
        messages.success(
            self.request, 
            f'Inasistencia creada exitosamente para {self.object.empleado.user.get_full_name()}. '
            f'El empleado ha sido notificado y podrá justificarla subiendo documentos.'
        )
        
        return response


class EditarInasistenciaView(LoginRequiredMixin, SoloRRHHMixin, UpdateView):
    """Vista para editar una inasistencia desde RRHH"""
    model = Inasistencia
    form_class = CrearInasistenciaForm
    template_name = 'rrhh/editar_inasistencia.html'
    success_url = reverse_lazy('rrhh:inasistencias')
    
    def form_valid(self, form):
        # Registrar quien modificó la inasistencia
        form.instance.modificado_por = self.request.user
        
        response = super().form_valid(form)
        
        messages.success(
            self.request, 
            f'Inasistencia de {self.object.empleado.user.get_full_name()} actualizada exitosamente.'
        )
        
        return response


@login_required
@require_POST
def cambiar_estado_inasistencia(request, inasistencia_id):
    """Vista para cambiar el estado de una inasistencia"""
    try:
        # Verificar que sea usuario RRHH
        empleado = Empleado.objects.get(user=request.user)
        if not empleado.es_rrhh:
            return JsonResponse({'success': False, 'message': 'Sin permisos'})
        
        inasistencia = get_object_or_404(Inasistencia, id=inasistencia_id)
        nuevo_estado = request.POST.get('estado')
        observaciones = request.POST.get('observaciones', '')
        
        if nuevo_estado not in ['pendiente', 'justificada', 'injustificada']:
            return JsonResponse({
                'success': False, 
                'message': 'Estado no válido'
            })
        
        estado_anterior = inasistencia.estado
        inasistencia.estado = nuevo_estado
        if observaciones:
            inasistencia.observaciones_rrhh = observaciones
        inasistencia.modificado_por = request.user
        inasistencia.save()
        
        messages.success(
            request, 
            f'Estado de inasistencia cambiado de "{inasistencia.get_estado_display()}" a "{dict(Inasistencia.ESTADO_CHOICES)[nuevo_estado]}"'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Estado actualizado exitosamente',
            'nuevo_estado': nuevo_estado,
            'nuevo_estado_display': dict(Inasistencia.ESTADO_CHOICES)[nuevo_estado]
        })
        
    except Empleado.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Usuario no encontrado'})
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'Error: {str(e)}'
        })


@login_required
def obtener_progreso_carga(request, carga_id):
    """Endpoint para obtener el progreso de una carga masiva"""
    print(f"Consultando progreso para carga ID: {carga_id}")
    try:
        carga_masiva = CargaMasivaRecibos.objects.get(id=carga_id)
        print(f"Estado de la carga: {carga_masiva.estado}")
        
        # Calcular progreso basado en los recibos procesados
        total_empleados = carga_masiva.total_empleados or 0
        
        # Buscar recibos relacionados por período, año y usuario
        from apps.recibos.models import ReciboSueldo
        recibos_creados = ReciboSueldo.objects.filter(
            periodo=carga_masiva.periodo,
            anio=carga_masiva.anio,
            subido_por=carga_masiva.usuario_carga
        ).count()
        
        # Contar logs de procesamiento
        logs_procesados = carga_masiva.logs_procesamiento.count()
        errores_count = carga_masiva.logs_procesamiento.filter(estado='error').count()
        
        # El progreso se basa en todos los empleados que se han procesado (exitosos + errores)
        procesados = logs_procesados
        
        if total_empleados > 0:
            porcentaje = min(int((procesados / total_empleados) * 100), 100)
        else:
            porcentaje = 0
        
        print(f"Progreso: {procesados}/{total_empleados} = {porcentaje}%")
            
        resultado = {
            'estado': carga_masiva.estado,
            'total_empleados': total_empleados,
            'procesados': procesados,
            'recibos_creados': recibos_creados,
            'errores': errores_count,
            'porcentaje': porcentaje,
            'completado': carga_masiva.estado in ['completado', 'error'],
            'mensaje': 'Procesamiento completado' if carga_masiva.estado == 'completado' else 'Procesando...'
        }
        
        print(f"Retornando: {resultado}")
        return JsonResponse(resultado)
        
    except CargaMasivaRecibos.DoesNotExist:
        return JsonResponse({'error': 'Carga no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class ObservacionesRecibosListView(LoginRequiredMixin, TemplateView):
    """Vista para mostrar todos los recibos con observaciones pendientes"""
    template_name = 'rrhh/observaciones_recibos.html'
    
    def dispatch(self, request, *args, **kwargs):
        try:
            empleado = Empleado.objects.get(user=request.user)
            if not empleado.es_rrhh:
                messages.error(request, "No tienes permisos para acceder a esta página.")
                return redirect('empleados:dashboard')
        except Empleado.DoesNotExist:
            messages.error(request, "Usuario no encontrado.")
            return redirect('empleados:dashboard')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.recibos.models import ReciboSueldo
        
        # Recibos con observaciones pendientes (estado 'observado')
        recibos_observados = ReciboSueldo.objects.filter(
            estado='observado'
        ).select_related('empleado__user').order_by('-fecha_observacion')
        
        # Recibos con observaciones ya respondidas (estado 'respondido')
        recibos_respondidos = ReciboSueldo.objects.filter(
            estado='respondido'
        ).select_related('empleado__user').order_by('-fecha_respuesta_rrhh')
        
        context.update({
            'recibos_observados': recibos_observados,
            'recibos_respondidos': recibos_respondidos,
            'total_observaciones_pendientes': recibos_observados.count(),
            'total_observaciones_respondidas': recibos_respondidos.count(),
        })
        
        return context


@login_required
def responder_observacion_recibo(request, recibo_id):
    """Vista para responder a una observación de recibo"""
    from apps.recibos.models import ReciboSueldo
    from apps.notificaciones.models import Notificacion
    from django.utils import timezone
    
    recibo = get_object_or_404(ReciboSueldo, pk=recibo_id)
    
    # Verificar permisos de RRHH
    try:
        empleado_rrhh = Empleado.objects.get(user=request.user)
        if not empleado_rrhh.es_rrhh:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'No tienes permisos para responder observaciones.'
                })
            messages.error(request, "No tienes permisos para responder observaciones.")
            return redirect('empleados:dashboard')
    except Empleado.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Usuario no encontrado.'
            })
        messages.error(request, "Usuario no encontrado.")
        return redirect('empleados:dashboard')
    
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Respuesta AJAX
            respuesta = request.POST.get('respuesta_rrhh', '').strip()
            
            if not respuesta:
                return JsonResponse({
                    'success': False,
                    'message': 'La respuesta no puede estar vacía.'
                })
            
            # Solo se pueden responder recibos con estado 'observado'
            if recibo.estado != 'observado':
                return JsonResponse({
                    'success': False,
                    'message': 'Solo se pueden responder observaciones en estado pendiente.'
                })
            
            # Actualizar el recibo
            recibo.observaciones_rrhh = respuesta
            recibo.fecha_respuesta_rrhh = timezone.now()
            recibo.respondido_por = request.user
            recibo.estado = 'respondido'
            recibo.save()
            
            # Crear notificación para el empleado
            try:
                Notificacion.objects.create(
                    usuario=recibo.empleado.user,
                    tipo='respuesta_observacion',
                    titulo='Respuesta a tu observación',
                    descripcion=f'RRHH ha respondido a tu observación sobre el recibo de {recibo.get_tipo_recibo_display()} {recibo.get_periodo_display()} {recibo.anio}'
                )
            except Exception as e:
                print(f"Error creando notificación: {e}")
            
            return JsonResponse({
                'success': True,
                'message': 'Respuesta enviada correctamente.',
                'nuevo_estado': recibo.get_estado_display()
            })
        
        else:
            # Respuesta tradicional (formulario)
            respuesta = request.POST.get('respuesta_rrhh', '').strip()
            
            if respuesta and recibo.estado == 'observado':
                recibo.observaciones_rrhh = respuesta
                recibo.fecha_respuesta_rrhh = timezone.now()
                recibo.respondido_por = request.user
                recibo.estado = 'respondido'
                recibo.save()
                
                # Crear notificación para el empleado
                try:
                    Notificacion.objects.create(
                        usuario=recibo.empleado.user,
                        tipo='respuesta_observacion',
                        titulo='Respuesta a tu observación',
                        descripcion=f'RRHH ha respondido a tu observación sobre el recibo de {recibo.get_tipo_recibo_display()} {recibo.get_periodo_display()} {recibo.anio}'
                    )
                except Exception as e:
                    print(f"Error creando notificación: {e}")
                
                messages.success(request, 'Respuesta enviada correctamente.')
            else:
                messages.error(request, 'Error al procesar la respuesta.')
            
            return redirect('rrhh:observaciones_recibos')
    
    # GET: Mostrar el formulario (si no es AJAX)
    return render(request, 'rrhh/responder_observacion_recibo.html', {
        'recibo': recibo
    })


@login_required
def ver_recibo_rrhh(request, recibo_id):
    """Vista para que RRHH pueda ver cualquier recibo (sin restricciones de empleado)"""
    from apps.recibos.models import ReciboSueldo
    
    recibo = get_object_or_404(ReciboSueldo, pk=recibo_id)
    
    # Verificar permisos de RRHH
    try:
        empleado_rrhh = Empleado.objects.get(user=request.user)
        if not empleado_rrhh.es_rrhh:
            messages.error(request, "No tienes permisos para ver este recibo.")
            return redirect('empleados:dashboard')
    except Empleado.DoesNotExist:
        messages.error(request, "Usuario no encontrado.")
        return redirect('empleados:dashboard')
    
    # RRHH puede ver cualquier archivo (centromédica si existe, si no el original)
    if recibo.archivo_pdf_centromedica:
        response = FileResponse(
            recibo.archivo_pdf_centromedica.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'inline; filename="{recibo.nombre_archivo}"'
        return response
    elif recibo.archivo_pdf:
        response = FileResponse(
            recibo.archivo_pdf.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'inline; filename="{recibo.nombre_archivo}"'
        return response
    else:
        messages.error(request, "Archivo de recibo no encontrado.")
        return redirect('rrhh:observaciones_recibos')
