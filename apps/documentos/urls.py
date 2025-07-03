from django.urls import path
from . import views

app_name = 'documentos'

urlpatterns = [
    path('', views.DocumentosListView.as_view(), name='lista'),
    path('subir/', views.SubirDocumentoView.as_view(), name='subir'),
    path('<int:pk>/firmar/', views.FirmarDocumentoView.as_view(), name='firmar'),
    path('<int:pk>/detalle/', views.DetalleDocumentoView.as_view(), name='detalle'),
]
