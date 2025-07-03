from django.urls import path
from . import views

app_name = 'solicitudes'

urlpatterns = [
    path('', views.SolicitudesListView.as_view(), name='lista'),
    path('vacaciones/', views.SolicitarVacacionesView.as_view(), name='vacaciones'),
    path('dias-estudio/', views.SolicitarDiasEstudioView.as_view(), name='dias_estudio'),
    path('<int:pk>/detalle/', views.DetalleSolicitudView.as_view(), name='detalle'),
    path('recibos/', views.RecibosListView.as_view(), name='recibos'),
    path('recibos/<int:pk>/firmar/', views.FirmarReciboView.as_view(), name='firmar_recibo'),
]
