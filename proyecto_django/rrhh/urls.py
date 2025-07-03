from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('perfil/', views.perfil, name='perfil'),
    path('recibos/', views.recibos, name='recibos'),
    path('recibos/firmar/<int:recibo_id>/', views.firmar_recibo, name='firmar_recibo'),
    path('solicitudes/', views.solicitudes, name='solicitudes'),
    path('documentos/', views.documentos, name='documentos'),
    path('certificados/', views.certificados, name='certificados'),
    path('notificaciones/', views.notificaciones, name='notificaciones'),
    path('api/notificaciones/count/', views.get_notificaciones_count, name='notificaciones_count'),
]
