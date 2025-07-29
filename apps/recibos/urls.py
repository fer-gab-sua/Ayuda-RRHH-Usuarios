from django.urls import path
from . import views

app_name = 'recibos'

urlpatterns = [
    path('', views.MisRecibosView.as_view(), name='mis_recibos'),
    path('<int:recibo_id>/visualizar/', views.visualizar_recibo, name='visualizar_recibo'),
    path('<int:recibo_id>/ver/', views.ver_recibo_pdf, name='ver_recibo'),
    path('<int:recibo_id>/firmado/', views.ver_recibo_firmado, name='ver_recibo_firmado'),
    path('<int:recibo_id>/centromedica/', views.ver_recibo_centromedica, name='ver_recibo_centromedica'),
    path('<int:recibo_id>/observar/', views.observar_recibo, name='observar_recibo'),
    path('<int:recibo_id>/procesar-observacion/', views.procesar_observacion_recibo, name='procesar_observacion'),
    path('<int:recibo_id>/firmar/', views.firmar_recibo, name='firmar_recibo'),
    path('<int:recibo_id>/procesar-firma/', views.procesar_firma_recibo, name='procesar_firma'),
]
