from django.urls import path
from . import views

app_name = 'notificaciones'

urlpatterns = [
    path('', views.NotificacionesListView.as_view(), name='lista'),
    path('<int:pk>/marcar-leida/', views.MarcarLeidaView.as_view(), name='marcar_leida'),
    path('todas/marcar-leidas/', views.MarcarTodasLeidasView.as_view(), name='marcar_todas_leidas'),
]
