from django.urls import path
from . import views

app_name = 'rrhh'

urlpatterns = [
    path('login/', views.RRHHLoginView.as_view(), name='login'),
    path('dashboard/', views.RRHHDashboardView.as_view(), name='dashboard'),
    path('empleados/', views.EmpleadosListView.as_view(), name='empleados'),
    path('empleados/crear/', views.CrearEmpleadoView.as_view(), name='crear_empleado'),
    path('empleados/<int:pk>/editar/', views.EditarEmpleadoView.as_view(), name='editar_empleado'),
    path('documentos/', views.DocumentosRRHHListView.as_view(), name='documentos'),
    path('documentos/<int:pk>/aprobar/', views.AprobarDocumentoView.as_view(), name='aprobar_documento'),
    path('solicitudes/', views.SolicitudesRRHHListView.as_view(), name='solicitudes'),
    path('solicitudes/<int:pk>/gestionar/', views.GestionarSolicitudView.as_view(), name='gestionar_solicitud'),
    path('recibos/', views.RecibosRRHHListView.as_view(), name='recibos'),
    path('recibos/subir/', views.SubirReciboView.as_view(), name='subir_recibo'),
]
