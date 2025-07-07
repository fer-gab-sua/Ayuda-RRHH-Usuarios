from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as AuthLoginView
from django.views.generic import TemplateView, ListView, FormView, UpdateView, CreateView, DetailView
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.clickjacking import xframe_options_exempt
import os
import mimetypes

from apps.empleados.models import Empleado, SolicitudCambio, DomicilioEmpleado
from apps.documentos.models import Documento
from apps.recibos.models import ReciboSueldo
from .forms import SubirRecibosForm, CrearEmpleadoForm, EditarEmpleadoForm, DomicilioEmpleadoForm
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from io import BytesIO

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

class ConfirmarDocumentoView(LoginRequiredMixin, SoloRRHHMixin, TemplateView):
    template_name = 'rrhh/confirmar_documento.html'
    # Aquí se implementaría la lógica de confirmación/rechazo

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
            ReciboSueldo.objects.create(
                empleado=empleado,
                periodo=periodo,
                anio=anio,
                fecha_vencimiento=timezone.now(),
                archivo_pdf=archivo_pdf,
                subido_por=self.request.user
            )
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
