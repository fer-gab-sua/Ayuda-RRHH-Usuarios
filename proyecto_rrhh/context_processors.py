from apps.empleados.models import Empleado
from apps.notificaciones.models import Notificacion

def empleado_info(request):
    """Context processor para información del empleado"""
    context = {}
    
    if request.user.is_authenticated:
        try:
            empleado = Empleado.objects.get(user=request.user)
            context['empleado'] = empleado
            
            # Contar notificaciones no leídas
            notificaciones_count = Notificacion.objects.filter(
                destinatario=empleado,
                leida=False
            ).count()
            context['notificaciones_count'] = notificaciones_count
            
        except Empleado.DoesNotExist:
            context['empleado'] = None
            context['notificaciones_count'] = 0
    
    return context
