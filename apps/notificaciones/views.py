from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

class NotificacionesListView(LoginRequiredMixin, TemplateView):
    template_name = 'notificaciones/lista.html'

class MarcarLeidaView(LoginRequiredMixin, TemplateView):
    template_name = 'notificaciones/marcar_leida.html'

class MarcarTodasLeidasView(LoginRequiredMixin, TemplateView):
    template_name = 'notificaciones/marcar_todas_leidas.html'
