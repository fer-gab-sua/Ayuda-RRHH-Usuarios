from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Notificacion
from apps.empleados.models import Empleado

class NotificacionesListView(LoginRequiredMixin, ListView):
    """Vista para mostrar las notificaciones del empleado"""
    model = Notificacion
    template_name = 'notificaciones/lista.html'
    context_object_name = 'notificaciones'
    paginate_by = 20
    
    def get_queryset(self):
        try:
            empleado = Empleado.objects.get(user=self.request.user)
            return Notificacion.objects.filter(destinatario=empleado).order_by('-fecha_creacion')
        except Empleado.DoesNotExist:
            return Notificacion.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            empleado = Empleado.objects.get(user=self.request.user)
            notificaciones = self.get_queryset()
            
            # Estadísticas
            context['total_notificaciones'] = notificaciones.count()
            context['no_leidas'] = notificaciones.filter(leida=False).count()
            context['leidas'] = notificaciones.filter(leida=True).count()
            
        except Empleado.DoesNotExist:
            pass
        
        return context

@login_required
@require_POST
def marcar_leida(request, notificacion_id):
    """Vista AJAX para marcar una notificación como leída"""
    try:
        empleado = Empleado.objects.get(user=request.user)
        notificacion = get_object_or_404(Notificacion, id=notificacion_id, destinatario=empleado)
        
        if not notificacion.leida:
            notificacion.marcar_como_leida()
        
        return JsonResponse({
            'success': True,
            'message': 'Notificación marcada como leída'
        })
        
    except Empleado.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Usuario no autorizado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@login_required
@require_POST
def marcar_todas_leidas(request):
    """Vista AJAX para marcar todas las notificaciones como leídas"""
    try:
        empleado = Empleado.objects.get(user=request.user)
        notificaciones_no_leidas = Notificacion.objects.filter(
            destinatario=empleado, 
            leida=False
        )
        
        count = 0
        for notificacion in notificaciones_no_leidas:
            notificacion.marcar_como_leida()
            count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'{count} notificaciones marcadas como leídas'
        })
        
    except Empleado.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Usuario no autorizado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })
