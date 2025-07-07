from django.urls import path
from . import views

app_name = 'rrhh'

urlpatterns = [
    path('login/', views.RRHHLoginView.as_view(), name='login'),
    path('dashboard/', views.RRHHDashboardView.as_view(), name='dashboard'),
    
    # Empleados
    path('empleados/', views.EmpleadosListView.as_view(), name='empleados'),
    path('empleados/crear/', views.CrearEmpleadoView.as_view(), name='crear_empleado'),
    path('empleados/<int:pk>/', views.EmpleadoDetailView.as_view(), name='empleado_detail'),
    path('empleados/<int:pk>/editar/', views.EditarEmpleadoView.as_view(), name='editar_empleado'),
    path('empleados/<int:pk>/eliminar/', views.EliminarEmpleadoView.as_view(), name='eliminar_empleado'),
    path('empleados/<int:empleado_pk>/domicilio/', views.EditarDomicilioEmpleadoView.as_view(), name='editar_domicilio'),
    path('empleados/<int:pk>/ajax/', views.empleado_ajax, name='empleado_ajax'),
    
    # Documentos
    path('documentos/', views.DocumentosRRHHListView.as_view(), name='documentos'),
    path('documentos/confirmar/', views.DocumentacionConfirmarListView.as_view(), name='documentacion_confirmar'),
    path('documentos/<int:pk>/confirmar/', views.ConfirmarDocumentoView.as_view(), name='confirmar_documento'),
    
    # Solicitudes
    path('solicitudes/', views.SolicitudesRRHHListView.as_view(), name='solicitudes'),
    path('solicitudes/<int:pk>/gestionar/', views.GestionarSolicitudView.as_view(), name='gestionar_solicitud'),
    path('solicitudes/<int:solicitud_id>/pdf/', views.servir_pdf_declaracion, name='servir_pdf_declaracion'),
    
    # Recibos
    path('recibos/', views.RecibosRRHHListView.as_view(), name='recibos'),
    path('recibos/subir/', views.SubirRecibosView.as_view(), name='subir_recibos'),
]
