from django.urls import path
from . import views

app_name = 'notificaciones'

urlpatterns = [
    path('', views.NotificacionesListView.as_view(), name='lista'),
    path('<int:notificacion_id>/marcar-leida/', views.marcar_leida, name='marcar_leida'),
    path('todas/marcar-leidas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
]
