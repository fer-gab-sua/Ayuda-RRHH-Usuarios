from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from .models import Empleado, ReciboSueldo, Solicitud, TipoSolicitud, Documento, Notificacion
from .forms import PerfilForm, SolicitudForm, DocumentoForm
import json


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    return render(request, 'registration/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    try:
        empleado = request.user.empleado
    except Empleado.DoesNotExist:
        messages.error(request, 'No se encontró el perfil de empleado')
        return redirect('login')
    
    # Contar recibos pendientes y firmados
    recibos_pendientes = ReciboSueldo.objects.filter(empleado=empleado, estado='pendiente').count()
    recibos_firmados = ReciboSueldo.objects.filter(empleado=empleado, estado__in=['firmado', 'disconformidad']).count()
    
    # Notificaciones no leídas
    notificaciones_count = Notificacion.objects.filter(empleado=empleado, leida=False).count()
    
    context = {
        'empleado': empleado,
        'recibos_pendientes': recibos_pendientes,
        'recibos_firmados': recibos_firmados,
        'notificaciones_count': notificaciones_count,
    }
    return render(request, 'rrhh/dashboard.html', context)


@login_required
def perfil(request):
    empleado = get_object_or_404(Empleado, user=request.user)
    
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=empleado)
        if form.is_valid():
            form.save()
            # También actualizar el usuario
            user = request.user
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.email = request.POST.get('email', user.email)
            user.save()
            messages.success(request, 'Perfil actualizado correctamente')
            return redirect('perfil')
    else:
        form = PerfilForm(instance=empleado)
    
    return render(request, 'rrhh/perfil.html', {'form': form, 'empleado': empleado})


@login_required
def recibos(request):
    empleado = get_object_or_404(Empleado, user=request.user)
    recibos_list = ReciboSueldo.objects.filter(empleado=empleado)
    
    # Contar por estado
    sin_firmar = recibos_list.filter(estado='pendiente').count()
    firmados = recibos_list.exclude(estado='pendiente').count()
    
    context = {
        'recibos': recibos_list,
        'sin_firmar': sin_firmar,
        'firmados': firmados,
    }
    return render(request, 'rrhh/recibos.html', context)


@login_required
def firmar_recibo(request, recibo_id):
    empleado = get_object_or_404(Empleado, user=request.user)
    recibo = get_object_or_404(ReciboSueldo, id=recibo_id, empleado=empleado)
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        observaciones = request.POST.get('observaciones', '')
        
        if accion == 'firmar':
            recibo.estado = 'firmado'
        elif accion == 'disconformidad':
            recibo.estado = 'disconformidad'
        
        recibo.observaciones = observaciones
        recibo.fecha_firma = timezone.now()
        recibo.save()
        
        messages.success(request, 'Recibo firmado correctamente')
        return redirect('recibos')
    
    return render(request, 'rrhh/firmar_recibo.html', {'recibo': recibo})


@login_required
def solicitudes(request):
    empleado = get_object_or_404(Empleado, user=request.user)
    
    if request.method == 'POST':
        form = SolicitudForm(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.empleado = empleado
            solicitud.save()
            messages.success(request, 'Solicitud enviada correctamente')
            return redirect('solicitudes')
    else:
        form = SolicitudForm()
    
    solicitudes_list = Solicitud.objects.filter(empleado=empleado)
    tipos_solicitud = TipoSolicitud.objects.filter(activo=True)
    
    context = {
        'form': form,
        'solicitudes': solicitudes_list,
        'tipos_solicitud': tipos_solicitud,
    }
    return render(request, 'rrhh/solicitudes.html', context)


@login_required
def documentos(request):
    empleado = get_object_or_404(Empleado, user=request.user)
    documentos_list = Documento.objects.filter(empleado=empleado)
    
    context = {
        'documentos': documentos_list,
    }
    return render(request, 'rrhh/documentos.html', context)


@login_required
def certificados(request):
    empleado = get_object_or_404(Empleado, user=request.user)
    
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.empleado = empleado
            documento.tipo = 'certificado'
            documento.save()
            messages.success(request, 'Certificado subido correctamente')
            return redirect('certificados')
    else:
        form = DocumentoForm()
    
    certificados_list = Documento.objects.filter(empleado=empleado, tipo='certificado')
    
    context = {
        'form': form,
        'certificados': certificados_list,
    }
    return render(request, 'rrhh/certificados.html', context)


@login_required
def notificaciones(request):
    empleado = get_object_or_404(Empleado, user=request.user)
    notificaciones_list = Notificacion.objects.filter(empleado=empleado)
    
    # Marcar como leídas
    notificaciones_list.filter(leida=False).update(leida=True)
    
    context = {
        'notificaciones': notificaciones_list,
    }
    return render(request, 'rrhh/notificaciones.html', context)


@login_required
def get_notificaciones_count(request):
    """API endpoint para obtener el número de notificaciones no leídas"""
    empleado = get_object_or_404(Empleado, user=request.user)
    count = Notificacion.objects.filter(empleado=empleado, leida=False).count()
    return JsonResponse({'count': count})
