from django.urls import path
from . import views

app_name = 'admin_rrhh'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_admin, name='dashboard'),
    
    # Gestión de empleados
    path('empleados/', views.gestionar_empleados, name='gestionar_empleados'),
    path('empleados/crear/', views.crear_empleado, name='crear_empleado'),
    path('empleados/editar/<int:empleado_id>/', views.editar_empleado, name='editar_empleado'),
    path('empleados/exportar/', views.exportar_empleados, name='exportar_empleados'),
    
    # Gestión de recibos
    path('recibos/', views.gestionar_recibos, name='gestionar_recibos'),
    path('recibos/subir/', views.subir_recibo, name='subir_recibo'),
    
    # Gestión de solicitudes
    path('solicitudes/', views.gestionar_solicitudes, name='gestionar_solicitudes'),
    path('solicitudes/procesar/<int:solicitud_id>/', views.procesar_solicitud, name='procesar_solicitud'),
    
    # Gestión de documentos
    path('documentos/', views.gestionar_documentos, name='gestionar_documentos'),
    path('documentos/subir/<int:empleado_id>/', views.subir_documento_empleado, name='subir_documento'),
    
    # Notificaciones
    path('notificaciones/enviar/', views.enviar_notificacion, name='enviar_notificacion'),
    
    # Reportes
    path('reportes/', views.reportes, name='reportes'),
]
