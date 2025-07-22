from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import logout
from apps.empleados.models import Empleado


class CambioPasswordObligatorioMiddleware:
    """
    Middleware que verifica si un usuario autenticado debe cambiar su contraseña
    y lo redirige a la página correspondiente si es necesario.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs que están permitidas cuando el usuario debe cambiar contraseña
        self.allowed_urls = [
            reverse('empleados:cambiar_password_obligatorio'),
            reverse('empleados:logout'),
            '/admin/',  # Permitir acceso al admin de Django
        ]
    
    def __call__(self, request):
        # Verificar solo si el usuario está autenticado
        if request.user.is_authenticated:
            try:
                empleado = Empleado.objects.get(user=request.user)
                
                # Si debe cambiar contraseña y no está en una URL permitida
                if empleado.debe_cambiar_password:
                    current_url = request.path
                    
                    # Verificar si está intentando acceder a una URL no permitida
                    url_permitida = any(current_url.startswith(url) for url in self.allowed_urls)
                    
                    if not url_permitida:
                        return redirect('empleados:cambiar_password_obligatorio')
                        
            except Empleado.DoesNotExist:
                # Si no tiene empleado asociado, permitir continuar
                pass
        
        response = self.get_response(request)
        return response
