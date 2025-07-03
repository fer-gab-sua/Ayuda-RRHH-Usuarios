from django.urls import path
from . import views

app_name = 'recibos'

urlpatterns = [
    path('', views.MisRecibosView.as_view(), name='mis_recibos'),
    path('<int:recibo_id>/ver/', views.ver_recibo_pdf, name='ver_recibo'),
    path('<int:recibo_id>/firmar/', views.firmar_recibo, name='firmar_recibo'),
    path('<int:recibo_id>/procesar-firma/', views.procesar_firma_recibo, name='procesar_firma'),
]
