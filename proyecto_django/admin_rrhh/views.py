from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import csv

from rrhh.models import Empleado, ReciboSueldo, Solicitud, TipoSolicitud, Documento, Notificacion
from .models import PerfilRRHH, AprobacionSolicitud, LogActividad
from .forms import (
    SubirReciboForm, CrearEmpleadoForm, EditarEmpleadoForm, 
    NotificacionForm, DocumentoRRHHForm, BusquedaForm
)


def es_usuario_rrhh(user):
    """Verifica si el usuario pertenece a RRHH"""
    return user.is_staff or hasattr(user, 'perfilrrhh')


@login_required
@user_passes_test(es_usuario_rrhh)
def dashboard_admin(request):
    """Dashboard principal de administración RRHH"""
    # Estadísticas generales
    total_empleados = Empleado.objects.count()
    recibos_pendientes = ReciboSueldo.objects.filter(estado='pendiente').count()
    solicitudes_pendientes = Solicitud.objects.filter(estado='pendiente').count()
    notificaciones_no_leidas = Notificacion.objects.filter(leida=False).count()
    
    # Actividad reciente
    actividades_recientes = LogActividad.objects.select_related(
        'usuario_rrhh__user', 'empleado_afectado__user'
    )[:10]
    
    # Solicitudes recientes
    solicitudes_recientes = Solicitud.objects.select_related(
        'empleado__user', 'tipo'
    ).filter(estado='pendiente')[:5]
    
    # Empleados con recibos pendientes
    empleados_recibos_pendientes = Empleado.objects.filter(
        recibosueldo__estado='pendiente'
    ).distinct()[:5]
    
    context = {
        'total_empleados': total_empleados,
        'recibos_pendientes': recibos_pendientes,
        'solicitudes_pendientes': solicitudes_pendientes,
        'notificaciones_no_leidas': notificaciones_no_leidas,
        'actividades_recientes': actividades_recientes,
        'solicitudes_recientes': solicitudes_recientes,
        'empleados_recibos_pendientes': empleados_recibos_pendientes,
    }
    return render(request, 'admin_rrhh/dashboard.html', context)


@login_required
@user_passes_test(es_usuario_rrhh)
def gestionar_empleados(request):
    """Vista para gestionar empleados"""
    busqueda_form = BusquedaForm(request.GET)
    empleados = Empleado.objects.select_related('user').all()
    
    # Aplicar filtros de búsqueda
    if busqueda_form.is_valid():
        query = busqueda_form.cleaned_data.get('query')
        departamento = busqueda_form.cleaned_data.get('departamento')
        
        if query:
            empleados = empleados.filter(
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(dni__icontains=query) |
                Q(puesto__icontains=query)
            )
        
        if departamento:
            empleados = empleados.filter(departamento=departamento)
    
    # Paginación
    paginator = Paginator(empleados, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener departamentos únicos para el filtro
    departamentos = Empleado.objects.values_list('departamento', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'busqueda_form': busqueda_form,
        'departamentos': departamentos,
    }
    return render(request, 'admin_rrhh/gestionar_empleados.html', context)


@login_required
@user_passes_test(es_usuario_rrhh)
def crear_empleado(request):
    """Vista para crear un nuevo empleado"""
    if request.method == 'POST':
        form = CrearEmpleadoForm(request.POST, request.FILES)
        if form.is_valid():
            empleado = form.save()
            
            # Registrar actividad
            perfil_rrhh, _ = PerfilRRHH.objects.get_or_create(user=request.user)
            LogActividad.objects.create(
                usuario_rrhh=perfil_rrhh,
                tipo_actividad='empleado_creado',
                descripcion=f'Empleado {empleado} creado',
                empleado_afectado=empleado
            )
            
            messages.success(request, f'Empleado {empleado} creado exitosamente')
            return redirect('admin_rrhh:gestionar_empleados')
    else:
        form = CrearEmpleadoForm()
    
    return render(request, 'admin_rrhh/crear_empleado.html', {'form': form})


@login_required
@user_passes_test(es_usuario_rrhh)
def editar_empleado(request, empleado_id):
    """Vista para editar un empleado"""
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    if request.method == 'POST':
        form = EditarEmpleadoForm(request.POST, request.FILES, instance=empleado)
        if form.is_valid():
            form.save()
            
            # Registrar actividad
            perfil_rrhh, _ = PerfilRRHH.objects.get_or_create(user=request.user)
            LogActividad.objects.create(
                usuario_rrhh=perfil_rrhh,
                tipo_actividad='empleado_editado',
                descripcion=f'Empleado {empleado} editado',
                empleado_afectado=empleado
            )
            
            messages.success(request, f'Empleado {empleado} actualizado exitosamente')
            return redirect('admin_rrhh:gestionar_empleados')
    else:
        form = EditarEmpleadoForm(instance=empleado)
    
    return render(request, 'admin_rrhh/editar_empleado.html', {
        'form': form, 
        'empleado': empleado
    })


@login_required
@user_passes_test(es_usuario_rrhh)
def gestionar_recibos(request):
    """Vista para gestionar recibos de sueldo"""
    recibos = ReciboSueldo.objects.select_related('empleado__user').all().order_by('-fecha')
    
    # Filtros
    estado = request.GET.get('estado')
    mes = request.GET.get('mes')
    
    if estado:
        recibos = recibos.filter(estado=estado)
    
    if mes:
        try:
            mes_date = datetime.strptime(mes, '%Y-%m')
            recibos = recibos.filter(fecha__year=mes_date.year, fecha__month=mes_date.month)
        except ValueError:
            pass
    
    # Paginación
    paginator = Paginator(recibos, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    stats = {
        'total': recibos.count(),
        'pendientes': recibos.filter(estado='pendiente').count(),
        'firmados': recibos.filter(estado='firmado').count(),
        'disconformidad': recibos.filter(estado='disconformidad').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'estado_actual': estado,
        'mes_actual': mes,
    }
    return render(request, 'admin_rrhh/gestionar_recibos.html', context)


@login_required
@user_passes_test(es_usuario_rrhh)
def subir_recibo(request):
    """Vista para subir recibos de sueldo"""
    if request.method == 'POST':
        form = SubirReciboForm(request.POST, request.FILES)
        if form.is_valid():
            recibo = form.save()
            
            # Registrar actividad
            perfil_rrhh, _ = PerfilRRHH.objects.get_or_create(user=request.user)
            LogActividad.objects.create(
                usuario_rrhh=perfil_rrhh,
                tipo_actividad='recibo_subido',
                descripcion=f'Recibo {recibo.periodo} subido para {recibo.empleado}',
                empleado_afectado=recibo.empleado
            )
            
            # Crear notificación para el empleado
            Notificacion.objects.create(
                empleado=recibo.empleado,
                titulo='Nuevo recibo disponible',
                mensaje=f'Tu recibo de {recibo.periodo} está disponible para firmar.',
                tipo='info'
            )
            
            messages.success(request, f'Recibo subido exitosamente para {recibo.empleado}')
            return redirect('admin_rrhh:gestionar_recibos')
    else:
        form = SubirReciboForm()
    
    return render(request, 'admin_rrhh/subir_recibo.html', {'form': form})


@login_required
@user_passes_test(es_usuario_rrhh)
def gestionar_solicitudes(request):
    """Vista para gestionar solicitudes"""
    solicitudes = Solicitud.objects.select_related('empleado__user', 'tipo').all()
    
    # Filtros
    estado = request.GET.get('estado', 'pendiente')
    tipo_id = request.GET.get('tipo')
    empleado_id = request.GET.get('empleado')
    
    if estado:
        solicitudes = solicitudes.filter(estado=estado)
    
    if tipo_id:
        solicitudes = solicitudes.filter(tipo_id=tipo_id)
    
    if empleado_id:
        solicitudes = solicitudes.filter(empleado_id=empleado_id)
    
    # Paginación
    paginator = Paginator(solicitudes, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Para los filtros
    tipos_solicitud = TipoSolicitud.objects.filter(activo=True)
    empleados = Empleado.objects.select_related('user').all()
    
    context = {
        'page_obj': page_obj,
        'tipos_solicitud': tipos_solicitud,
        'empleados': empleados,
        'estado_actual': estado,
        'tipo_actual': tipo_id,
        'empleado_actual': empleado_id,
    }
    return render(request, 'admin_rrhh/gestionar_solicitudes.html', context)


@login_required
@user_passes_test(es_usuario_rrhh)
def procesar_solicitud(request, solicitud_id):
    """Vista para aprobar/rechazar solicitudes"""
    solicitud = get_object_or_404(Solicitud, id=solicitud_id)
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        observaciones = request.POST.get('observaciones', '')
        
        perfil_rrhh, _ = PerfilRRHH.objects.get_or_create(user=request.user)
        
        if accion == 'aprobar':
            solicitud.estado = 'aprobada'
            solicitud.observaciones_respuesta = observaciones
            solicitud.fecha_respuesta = timezone.now()
            solicitud.save()
            
            # Registrar aprobación
            AprobacionSolicitud.objects.create(
                solicitud=solicitud,
                aprobador=perfil_rrhh,
                comentarios=observaciones
            )
            
            # Log de actividad
            LogActividad.objects.create(
                usuario_rrhh=perfil_rrhh,
                tipo_actividad='solicitud_aprobada',
                descripcion=f'Solicitud de {solicitud.tipo.nombre} aprobada para {solicitud.empleado}',
                empleado_afectado=solicitud.empleado
            )
            
            # Notificación al empleado
            Notificacion.objects.create(
                empleado=solicitud.empleado,
                titulo='Solicitud aprobada',
                mensaje=f'Tu solicitud de {solicitud.tipo.nombre} ha sido aprobada.',
                tipo='info'
            )
            
            messages.success(request, 'Solicitud aprobada exitosamente')
            
        elif accion == 'rechazar':
            solicitud.estado = 'rechazada'
            solicitud.observaciones_respuesta = observaciones
            solicitud.fecha_respuesta = timezone.now()
            solicitud.save()
            
            # Log de actividad
            LogActividad.objects.create(
                usuario_rrhh=perfil_rrhh,
                tipo_actividad='solicitud_rechazada',
                descripcion=f'Solicitud de {solicitud.tipo.nombre} rechazada para {solicitud.empleado}',
                empleado_afectado=solicitud.empleado
            )
            
            # Notificación al empleado
            Notificacion.objects.create(
                empleado=solicitud.empleado,
                titulo='Solicitud rechazada',
                mensaje=f'Tu solicitud de {solicitud.tipo.nombre} ha sido rechazada. Motivo: {observaciones}',
                tipo='alerta'
            )
            
            messages.success(request, 'Solicitud rechazada')
        
        return redirect('admin_rrhh:gestionar_solicitudes')
    
    return render(request, 'admin_rrhh/procesar_solicitud.html', {'solicitud': solicitud})


@login_required
@user_passes_test(es_usuario_rrhh)
def gestionar_documentos(request):
    """Vista para gestionar documentos"""
    documentos = Documento.objects.select_related('empleado__user').all().order_by('-fecha_subida')
    
    # Filtros
    tipo = request.GET.get('tipo')
    empleado_id = request.GET.get('empleado')
    
    if tipo:
        documentos = documentos.filter(tipo=tipo)
    
    if empleado_id:
        documentos = documentos.filter(empleado_id=empleado_id)
    
    # Paginación
    paginator = Paginator(documentos, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    empleados = Empleado.objects.select_related('user').all()
    
    context = {
        'page_obj': page_obj,
        'empleados': empleados,
        'tipo_actual': tipo,
        'empleado_actual': empleado_id,
        'tipos_documento': Documento.TIPOS,
    }
    return render(request, 'admin_rrhh/gestionar_documentos.html', context)


@login_required
@user_passes_test(es_usuario_rrhh)
def subir_documento_empleado(request, empleado_id):
    """Vista para subir documentos a un empleado específico"""
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    if request.method == 'POST':
        form = DocumentoRRHHForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.empleado = empleado
            documento.save()
            
            # Registrar actividad
            perfil_rrhh, _ = PerfilRRHH.objects.get_or_create(user=request.user)
            LogActividad.objects.create(
                usuario_rrhh=perfil_rrhh,
                tipo_actividad='documento_subido',
                descripcion=f'Documento {documento.nombre} subido para {empleado}',
                empleado_afectado=empleado
            )
            
            # Notificar al empleado
            Notificacion.objects.create(
                empleado=empleado,
                titulo='Nuevo documento disponible',
                mensaje=f'Se ha subido un nuevo documento: {documento.nombre}',
                tipo='info'
            )
            
            messages.success(request, f'Documento subido exitosamente para {empleado}')
            return redirect('admin_rrhh:gestionar_documentos')
    else:
        form = DocumentoRRHHForm()
    
    return render(request, 'admin_rrhh/subir_documento.html', {
        'form': form, 
        'empleado': empleado
    })


@login_required
@user_passes_test(es_usuario_rrhh)
def enviar_notificacion(request):
    """Vista para enviar notificaciones"""
    if request.method == 'POST':
        form = NotificacionForm(request.POST)
        if form.is_valid():
            tipo_destinatario = form.cleaned_data['tipo_destinatario']
            titulo = form.cleaned_data['titulo']
            mensaje = form.cleaned_data['mensaje']
            tipo = form.cleaned_data['tipo']
            importante = form.cleaned_data.get('importante', False)
            
            # Determinar qué empleados recibirán la notificación
            empleados = []
            if tipo_destinatario == 'todos':
                empleados = Empleado.objects.all()
            elif tipo_destinatario == 'departamento':
                departamento = form.cleaned_data['departamento']
                empleados = Empleado.objects.filter(departamento=departamento)
            elif tipo_destinatario == 'especifico':
                empleado_especifico = form.cleaned_data['empleado_especifico']
                empleados = [empleado_especifico]
            
            # Crear notificaciones para todos los empleados seleccionados
            notificaciones_creadas = 0
            for empleado in empleados:
                notificacion_data = {
                    'empleado': empleado,
                    'titulo': titulo,
                    'mensaje': mensaje,
                    'tipo': tipo,
                }
                
                # Solo agregar importante si el campo existe en el modelo
                if hasattr(Notificacion, 'importante'):
                    notificacion_data['importante'] = importante
                
                Notificacion.objects.create(**notificacion_data)
                notificaciones_creadas += 1
            
            # Registrar actividad
            perfil_rrhh, _ = PerfilRRHH.objects.get_or_create(user=request.user)
            
            # Descripción más detallada según el tipo de destinatario
            if tipo_destinatario == 'todos':
                descripcion = f'Notificación "{titulo}" enviada a todos los empleados ({notificaciones_creadas})'
            elif tipo_destinatario == 'departamento':
                departamento = form.cleaned_data['departamento']
                descripcion = f'Notificación "{titulo}" enviada al departamento {departamento} ({notificaciones_creadas} empleados)'
            else:
                empleado_especifico = form.cleaned_data['empleado_especifico']
                descripcion = f'Notificación "{titulo}" enviada a {empleado_especifico.user.get_full_name()}'
            
            LogActividad.objects.create(
                usuario_rrhh=perfil_rrhh,
                tipo_actividad='notificacion_enviada',
                descripcion=descripcion
            )
            
            messages.success(request, f'Notificación enviada exitosamente a {notificaciones_creadas} empleado(s)')
            return redirect('admin_rrhh:dashboard')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario')
    else:
        form = NotificacionForm()
    
    return render(request, 'admin_rrhh/enviar_notificacion.html', {'form': form})


@login_required
@user_passes_test(es_usuario_rrhh)
def reportes(request):
    """Vista para generar reportes"""
    # Estadísticas generales
    total_empleados = Empleado.objects.count()
    
    # Empleados por departamento
    empleados_por_dept = Empleado.objects.values('departamento').annotate(
        total=Count('id')
    ).order_by('-total')
    
    # Solicitudes por estado
    solicitudes_stats = Solicitud.objects.values('estado').annotate(
        total=Count('id')
    )
    
    # Recibos por estado
    recibos_stats = ReciboSueldo.objects.values('estado').annotate(
        total=Count('id')
    )
    
    # Actividad reciente
    actividad_reciente = LogActividad.objects.select_related(
        'usuario_rrhh__user'
    )[:20]
    
    context = {
        'total_empleados': total_empleados,
        'empleados_por_dept': empleados_por_dept,
        'solicitudes_stats': solicitudes_stats,
        'recibos_stats': recibos_stats,
        'actividad_reciente': actividad_reciente,
    }
    return render(request, 'admin_rrhh/reportes.html', context)


@login_required
@user_passes_test(es_usuario_rrhh)
def exportar_empleados(request):
    """Exportar lista de empleados a CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="empleados.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Nombre', 'Apellido', 'DNI', 'Email', 'Teléfono', 
        'Puesto', 'Departamento', 'Fecha Ingreso', 'Salario'
    ])
    
    empleados = Empleado.objects.select_related('user').all()
    for empleado in empleados:
        writer.writerow([
            empleado.user.first_name,
            empleado.user.last_name,
            empleado.dni,
            empleado.user.email,
            empleado.telefono,
            empleado.puesto,
            empleado.departamento,
            empleado.fecha_ingreso.strftime('%d/%m/%Y'),
            empleado.salario,
        ])
    
    return response
