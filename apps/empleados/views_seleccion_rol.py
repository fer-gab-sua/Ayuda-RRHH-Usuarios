"""
Vistas para selección de rol de usuario
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.urls import reverse
from django.contrib import messages
from .models import Empleado


@login_required
def seleccionar_rol(request):
    """Vista para que el usuario seleccione su rol (empleado o RRHH)"""
    try:
        empleado = Empleado.objects.get(user=request.user)
        
        # Si no es RRHH, redirigir directamente al dashboard de empleado
        if not empleado.es_rrhh:
            return redirect('empleados:dashboard')
            
        # Si es RRHH, mostrar la página de selección
        if request.method == 'POST':
            rol_seleccionado = request.POST.get('rol')
            
            if rol_seleccionado == 'rrhh':
                # Guardar en la sesión que eligió RRHH
                request.session['rol_activo'] = 'rrhh'
                messages.success(request, '¡Bienvenido al Panel de RRHH!')
                return redirect('rrhh:dashboard')
            elif rol_seleccionado == 'empleado':
                # Guardar en la sesión que eligió empleado
                request.session['rol_activo'] = 'empleado'
                messages.success(request, '¡Bienvenido al Portal del Empleado!')
                return redirect('empleados:dashboard')
            else:
                messages.error(request, 'Debes seleccionar un rol válido.')
        
        # Mostrar la página de selección
        context = {
            'empleado': empleado,
            'user': request.user,
        }
        return render(request, 'empleados/seleccionar_rol.html', context)
        
    except Empleado.DoesNotExist:
        messages.error(request, 'No se encontró el perfil de empleado.')
        return redirect('empleados:login')


@login_required 
def cambiar_rol(request):
    """Vista para cambiar de rol sin cerrar sesión"""
    try:
        empleado = Empleado.objects.get(user=request.user)
        
        # Solo permitir si es RRHH
        if not empleado.es_rrhh:
            messages.error(request, 'No tienes permisos para cambiar de rol.')
            return redirect('empleados:dashboard')
        
        # Limpiar el rol activo de la sesión para forzar nueva selección
        if 'rol_activo' in request.session:
            del request.session['rol_activo']
            
        messages.info(request, 'Selecciona tu rol para continuar.')
        return redirect('empleados:seleccionar_rol')
        
    except Empleado.DoesNotExist:
        messages.error(request, 'No se encontró el perfil de empleado.')
        return redirect('empleados:login')


class SeleccionRolMixin:
    """Mixin para verificar que se haya seleccionado un rol"""
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                empleado = Empleado.objects.get(user=request.user)
                
                # Si es RRHH y no ha seleccionado rol, redirigir a selección
                if empleado.es_rrhh and 'rol_activo' not in request.session:
                    return redirect('empleados:seleccionar_rol')
                    
            except Empleado.DoesNotExist:
                pass
                
        return super().dispatch(request, *args, **kwargs)


class SoloEmpleadosConRolMixin(SeleccionRolMixin):
    """Mixin para views de empleados que verifica rol activo"""
    
    def dispatch(self, request, *args, **kwargs):
        # Primero verificar selección de rol
        response = super().dispatch(request, *args, **kwargs)
        if hasattr(response, 'status_code') and response.status_code == 302:
            return response
            
        if request.user.is_authenticated:
            try:
                empleado = Empleado.objects.get(user=request.user)
                
                # Si es RRHH y tiene rol activo "rrhh", redirigir al panel RRHH
                if empleado.es_rrhh and request.session.get('rol_activo') == 'rrhh':
                    return redirect('rrhh:dashboard')
                    
            except Empleado.DoesNotExist:
                pass
                
        return super(SeleccionRolMixin, self).dispatch(request, *args, **kwargs)


class SoloRRHHConRolMixin(SeleccionRolMixin):
    """Mixin para views de RRHH que verifica rol activo"""
    
    def dispatch(self, request, *args, **kwargs):
        # Primero verificar selección de rol
        response = super().dispatch(request, *args, **kwargs)
        if hasattr(response, 'status_code') and response.status_code == 302:
            return response
            
        if request.user.is_authenticated:
            try:
                empleado = Empleado.objects.get(user=request.user)
                
                # Si no es RRHH, redirigir al dashboard de empleado
                if not empleado.es_rrhh:
                    return redirect('empleados:dashboard')
                
                # Si es RRHH pero tiene rol activo "empleado", redirigir al dashboard de empleado
                if empleado.es_rrhh and request.session.get('rol_activo') == 'empleado':
                    return redirect('empleados:dashboard')
                    
            except Empleado.DoesNotExist:
                return redirect('empleados:dashboard')
                
        return super(SeleccionRolMixin, self).dispatch(request, *args, **kwargs)
