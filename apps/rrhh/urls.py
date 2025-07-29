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
    path('documentos/<int:documento_id>/aprobar/', views.aprobar_documento, name='aprobar_documento'),
    path('documentos/<int:documento_id>/rechazar/', views.rechazar_documento, name='rechazar_documento'),
    path('documentos/<int:documento_id>/aclaracion/', views.solicitar_aclaracion_documento, name='solicitar_aclaracion_documento'),
    
    # Solicitudes
    path('solicitudes/', views.SolicitudesRRHHListView.as_view(), name='solicitudes'),
    path('solicitudes/<int:pk>/gestionar/', views.GestionarSolicitudView.as_view(), name='gestionar_solicitud'),
    path('solicitudes/<int:solicitud_id>/pdf/', views.servir_pdf_declaracion, name='servir_pdf_declaracion'),
    
    # Recibos
    path('recibos/', views.RRHHRecibosView.as_view(), name='recibos_dashboard'),
    path('recibos/cargar/', views.CargaMasivaCreateView.as_view(), name='cargar_recibos_masivo'),
    path('recibos/progreso/<int:carga_id>/', views.obtener_progreso_carga, name='progreso_carga'),
    path('recibos/lista/', views.CargaMasivaListView.as_view(), name='lista_cargas_masivas'),
    path('recibos/carga/<int:pk>/', views.CargaMasivaDetailView.as_view(), name='detalle_carga_masiva'),
    path('recibos/carga/<int:pk>/validar/', views.validar_carga_masiva, name='validar_carga_masiva'),
    path('recibos/carga/<int:pk>/hacer-visible/', views.hacer_visible_recibos, name='hacer_visible_recibos'),
    path('recibos/carga/<int:pk>/eliminar/', views.eliminar_carga_masiva, name='eliminar_carga_masiva'),
    path('recibos/recibo/<int:pk>/corregir/', views.corregir_recibo_no_encontrado, name='corregir_recibo_no_encontrado'),
    path('recibos/subir/', views.SubirRecibosView.as_view(), name='subir_recibos'),
    
    # Inasistencias
    path('inasistencias/', views.InasistenciasRRHHListView.as_view(), name='inasistencias'),
    path('inasistencias/crear/', views.CrearInasistenciaView.as_view(), name='crear_inasistencia'),
    path('inasistencias/<int:pk>/editar/', views.EditarInasistenciaView.as_view(), name='editar_inasistencia'),
    path('inasistencias/<int:inasistencia_id>/cambiar-estado/', views.cambiar_estado_inasistencia, name='cambiar_estado_inasistencia'),
]
