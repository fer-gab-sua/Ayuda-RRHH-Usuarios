"""
URL configuration for proyecto_rrhh project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from apps.empleados.models import Empleado

def redirect_by_role(request):
    """Redirige según el rol del usuario"""
    if not request.user.is_authenticated:
        return redirect('empleados:login')
    
    try:
        empleado = Empleado.objects.get(user=request.user)
        if empleado.es_rrhh:
            return redirect('rrhh:dashboard')
        else:
            return redirect('empleados:dashboard')
    except Empleado.DoesNotExist:
        return redirect('empleados:dashboard')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('empleados/', include('apps.empleados.urls')),
    path('documentos/', include('apps.documentos.urls')),
    path('solicitudes/', include('apps.solicitudes.urls')),
    path('notificaciones/', include('apps.notificaciones.urls')),
    path('rrhh/', include('apps.rrhh.urls')),
    path('recibos/', include('apps.recibos.urls')),
    path('', redirect_by_role),  # Redirigir la raíz según el rol del usuario
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
