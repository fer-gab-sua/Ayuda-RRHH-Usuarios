from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.http import JsonResponse, HttpResponse, Http404
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q

from .models import Documento, TipoDocumento, Inasistencia, HistorialDocumento
from .forms import DocumentoForm, JustificarInasistenciaForm, FiltroDocumentosForm
from apps.empleados.models import Empleado, ActividadEmpleado


class MisDocumentosView(LoginRequiredMixin, ListView):
    """Vista para que el empleado vea sus documentos"""
    model = Documento
    template_name = 'documentos/mis_documentos.html'
    context_object_name = 'documentos'
    paginate_by = 10

    def get_queryset(self):
        try:
            empleado = Empleado.objects.get(user=self.request.user)
            queryset = Documento.objects.filter(empleado=empleado)
            
            # Aplicar filtros si existen
            form = FiltroDocumentosForm(self.request.GET)
            if form.is_valid():
                if form.cleaned_data['estado']:
                    queryset = queryset.filter(estado=form.cleaned_data['estado'])
                if form.cleaned_data['tipo_documento']:
                    queryset = queryset.filter(tipo_documento=form.cleaned_data['tipo_documento'])
                if form.cleaned_data['fecha_desde']:
                    queryset = queryset.filter(fecha_subida__date__gte=form.cleaned_data['fecha_desde'])
                if form.cleaned_data['fecha_hasta']:
                    queryset = queryset.filter(fecha_subida__date__lte=form.cleaned_data['fecha_hasta'])
            
            return queryset.select_related('tipo_documento', 'inasistencia').order_by('-fecha_subida')
        except Empleado.DoesNotExist:
            return Documento.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            empleado = Empleado.objects.get(user=self.request.user)
            documentos = self.get_queryset()
            
            # Estadísticas
            context['total_documentos'] = documentos.count()
            context['pendientes'] = documentos.filter(estado='pendiente').count()
            context['aprobados'] = documentos.filter(estado='aprobado').count()
            context['rechazados'] = documentos.filter(estado='rechazado').count()
            context['requieren_aclaracion'] = documentos.filter(estado='requiere_aclaracion').count()
            
            # Formulario de filtros
            context['filtro_form'] = FiltroDocumentosForm(self.request.GET)
            context['empleado'] = empleado
            
        except Empleado.DoesNotExist:
            pass
        
        return context


class SubirDocumentoView(LoginRequiredMixin, CreateView):
    """Vista para subir un nuevo documento"""
    model = Documento
    form_class = DocumentoForm
    template_name = 'documentos/subir_documento.html'
    success_url = reverse_lazy('documentos:mis_documentos')

    def form_valid(self, form):
        try:
            empleado = Empleado.objects.get(user=self.request.user)
            form.instance.empleado = empleado
            
            response = super().form_valid(form)
            
            # Registrar actividad
            ActividadEmpleado.objects.create(
                empleado=empleado,
                descripcion=f"Subió un documento: {form.instance.titulo} ({form.instance.tipo_documento.nombre})"
            )
            
            messages.success(self.request, '¡Documento subido exitosamente! RRHH lo revisará pronto.')
            return response
            
        except Empleado.DoesNotExist:
            messages.error(self.request, 'Error: No se encontró el perfil de empleado.')
            return redirect('empleados:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipos_documento'] = TipoDocumento.objects.filter(activo=True)
        return context


class EditarDocumentoView(LoginRequiredMixin, UpdateView):
    """Vista para editar un documento (solo si está pendiente o requiere aclaración)"""
    model = Documento
    form_class = DocumentoForm
    template_name = 'documentos/editar_documento.html'
    success_url = reverse_lazy('documentos:mis_documentos')

    def get_queryset(self):
        try:
            empleado = Empleado.objects.get(user=self.request.user)
            return Documento.objects.filter(empleado=empleado)
        except Empleado.DoesNotExist:
            return Documento.objects.none()

    def dispatch(self, request, *args, **kwargs):
        documento = self.get_object()
        if not documento.puede_editar:
            messages.error(request, 'Este documento no puede ser editado porque ya fue procesado por RRHH.')
            return redirect('documentos:mis_documentos')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Capturar el estado anterior antes de guardar
        estado_anterior = form.instance.estado
        
        # Si el documento requería aclaración, cambiar a pendiente cuando se edite
        if estado_anterior == 'requiere_aclaracion':
            form.instance.estado = 'pendiente'
            form.instance.fecha_revision = None
            form.instance.revisado_por = None
            # Limpiar las observaciones de RRHH ya que se está reeditando
            # form.instance.observaciones_rrhh = None  # Comentado para mantener historial
        
        response = super().form_valid(form)
        
        # Crear entrada en el historial si cambió de estado
        if estado_anterior == 'requiere_aclaracion':
            HistorialDocumento.objects.create(
                documento=form.instance,
                usuario=self.request.user,
                estado_anterior=estado_anterior,
                estado_nuevo='pendiente',
                observaciones='Documento editado por el empleado para proporcionar aclaraciones'
            )
        
        # Registrar actividad
        try:
            empleado = Empleado.objects.get(user=self.request.user)
            descripcion_base = f"Editó el documento: {form.instance.titulo}"
            if estado_anterior == 'requiere_aclaracion':
                descripcion_base += " (proporcionando aclaraciones solicitadas)"
            
            ActividadEmpleado.objects.create(
                empleado=empleado,
                descripcion=descripcion_base
            )
        except Empleado.DoesNotExist:
            pass
        
        if estado_anterior == 'requiere_aclaracion':
            messages.success(self.request, 'Documento actualizado exitosamente. Ha sido enviado nuevamente a RRHH para revisión.')
        else:
            messages.success(self.request, 'Documento actualizado exitosamente.')
        
        return response


class DetalleDocumentoView(LoginRequiredMixin, DetailView):
    """Vista para ver el detalle de un documento"""
    model = Documento
    template_name = 'documentos/detalle_documento.html'
    context_object_name = 'documento'

    def get_queryset(self):
        try:
            empleado = Empleado.objects.get(user=self.request.user)
            return Documento.objects.filter(empleado=empleado).select_related(
                'tipo_documento', 'inasistencia', 'revisado_por'
            )
        except Empleado.DoesNotExist:
            return Documento.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener historial del documento
        context['historial'] = self.object.historial.all().select_related('usuario')
        return context


class VerDocumentoView(LoginRequiredMixin, DetailView):
    """Vista para ver/descargar el archivo del documento"""
    model = Documento

    def get_queryset(self):
        try:
            empleado = Empleado.objects.get(user=self.request.user)
            return Documento.objects.filter(empleado=empleado)
        except Empleado.DoesNotExist:
            return Documento.objects.none()

    def get(self, request, *args, **kwargs):
        documento = self.get_object()
        
        if not documento.archivo:
            raise Http404("Archivo no encontrado")
        
        try:
            # Registrar actividad
            empleado = Empleado.objects.get(user=request.user)
            ActividadEmpleado.objects.create(
                empleado=empleado,
                descripcion=f"Consultó el documento: {documento.titulo}"
            )
        except Empleado.DoesNotExist:
            pass

        # Leer el archivo
        try:
            with open(documento.archivo.path, 'rb') as archivo:
                response = HttpResponse(archivo.read())
                
                # Determinar content type basado en la extensión
                nombre_archivo = documento.nombre_archivo
                if nombre_archivo.lower().endswith('.pdf'):
                    response['Content-Type'] = 'application/pdf'
                elif nombre_archivo.lower().endswith(('.jpg', '.jpeg')):
                    response['Content-Type'] = 'image/jpeg'
                elif nombre_archivo.lower().endswith('.png'):
                    response['Content-Type'] = 'image/png'
                elif nombre_archivo.lower().endswith(('.doc', '.docx')):
                    response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                else:
                    response['Content-Type'] = 'application/octet-stream'
                
                response['Content-Disposition'] = f'inline; filename="{nombre_archivo}"'
                return response
                
        except FileNotFoundError:
            raise Http404("Archivo no encontrado en el servidor")


class MisInasistenciasView(LoginRequiredMixin, ListView):
    """Vista para que el empleado vea sus inasistencias"""
    model = Inasistencia
    template_name = 'documentos/mis_inasistencias.html'
    context_object_name = 'inasistencias'
    paginate_by = 10

    def get_queryset(self):
        try:
            empleado = Empleado.objects.get(user=self.request.user)
            return Inasistencia.objects.filter(empleado=empleado).order_by('-fecha_desde')
        except Empleado.DoesNotExist:
            return Inasistencia.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            empleado = Empleado.objects.get(user=self.request.user)
            inasistencias = self.get_queryset()
            
            # Estadísticas
            context['total_inasistencias'] = inasistencias.count()
            context['pendientes'] = inasistencias.filter(estado='pendiente').count()
            context['justificadas'] = inasistencias.filter(estado='justificada').count()
            context['injustificadas'] = inasistencias.filter(estado='injustificada').count()
            
            context['empleado'] = empleado
            
        except Empleado.DoesNotExist:
            pass
        
        return context


class JustificarInasistenciaView(LoginRequiredMixin, CreateView):
    """Vista para justificar una inasistencia con un documento"""
    model = Documento
    form_class = JustificarInasistenciaForm
    template_name = 'documentos/justificar_inasistencia.html'
    success_url = reverse_lazy('documentos:mis_inasistencias')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        try:
            kwargs['empleado'] = Empleado.objects.get(user=self.request.user)
        except Empleado.DoesNotExist:
            kwargs['empleado'] = None
        return kwargs

    def form_valid(self, form):
        try:
            empleado = Empleado.objects.get(user=self.request.user)
            form.instance.empleado = empleado
            
            # Establecer fechas del documento basadas en la inasistencia
            inasistencia = form.cleaned_data['inasistencia']
            form.instance.fecha_desde = inasistencia.fecha_desde
            form.instance.fecha_hasta = inasistencia.fecha_hasta
            
            response = super().form_valid(form)
            
            # Registrar actividad
            ActividadEmpleado.objects.create(
                empleado=empleado,
                descripcion=f"Subió documento justificativo para inasistencia del {inasistencia.fecha_desde} al {inasistencia.fecha_hasta}"
            )
            
            messages.success(self.request, '¡Documento justificativo subido exitosamente! RRHH lo revisará.')
            return response
            
        except Empleado.DoesNotExist:
            messages.error(self.request, 'Error: No se encontró el perfil de empleado.')
            return redirect('empleados:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener la inasistencia específica si se pasa como parámetro
        inasistencia_id = self.kwargs.get('pk')
        if inasistencia_id:
            try:
                empleado = Empleado.objects.get(user=self.request.user)
                inasistencia = get_object_or_404(
                    Inasistencia, 
                    id=inasistencia_id, 
                    empleado=empleado,
                    estado='pendiente'
                )
                context['inasistencia_especifica'] = inasistencia
            except Empleado.DoesNotExist:
                pass
        
        return context


@login_required
@require_POST
def eliminar_documento(request):
    """Vista AJAX para eliminar un documento"""
    try:
        empleado = Empleado.objects.get(user=request.user)
        documento_id = request.POST.get('documento_id')
        
        if not documento_id:
            return JsonResponse({
                'success': False,
                'message': 'ID de documento no proporcionado.'
            })
        
        documento = get_object_or_404(Documento, id=documento_id, empleado=empleado)
        
        # Solo permitir eliminar si está pendiente o requiere aclaración
        if not documento.puede_editar:
            return JsonResponse({
                'success': False,
                'message': 'No puedes eliminar este documento porque ya fue procesado por RRHH.'
            })
        
        titulo = documento.titulo
        documento.delete()
        
        # Registrar actividad
        ActividadEmpleado.objects.create(
            empleado=empleado,
            descripcion=f"Eliminó el documento: {titulo}"
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Documento eliminado exitosamente.'
        })
        
    except Empleado.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Error: No se encontró el perfil de empleado.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al eliminar el documento: {str(e)}'
        })
