from django.urls import path
from . import views

app_name = 'documentos'

urlpatterns = [
    # URLs para empleados
    path('', views.MisDocumentosView.as_view(), name='mis_documentos'),
    path('subir/', views.SubirDocumentoView.as_view(), name='subir'),
    path('<int:pk>/editar/', views.EditarDocumentoView.as_view(), name='editar'),
    path('<int:pk>/detalle/', views.DetalleDocumentoView.as_view(), name='detalle'),
    path('<int:pk>/ver/', views.VerDocumentoView.as_view(), name='ver_archivo'),
    
    # Inasistencias del empleado
    path('inasistencias/', views.MisInasistenciasView.as_view(), name='mis_inasistencias'),
    path('justificar/', views.JustificarInasistenciaView.as_view(), name='justificar'),
    path('inasistencias/<int:pk>/justificar/', views.JustificarInasistenciaView.as_view(), name='justificar_inasistencia'),
    
    # AJAX
    path('ajax/eliminar/', views.eliminar_documento, name='eliminar'),
]
