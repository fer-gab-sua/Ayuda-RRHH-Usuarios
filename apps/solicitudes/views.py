from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

class SolicitudesListView(LoginRequiredMixin, TemplateView):
    template_name = 'solicitudes/lista.html'

class SolicitarVacacionesView(LoginRequiredMixin, TemplateView):
    template_name = 'solicitudes/vacaciones.html'

class SolicitarDiasEstudioView(LoginRequiredMixin, TemplateView):
    template_name = 'solicitudes/dias_estudio.html'

class DetalleSolicitudView(LoginRequiredMixin, TemplateView):
    template_name = 'solicitudes/detalle.html'

class RecibosListView(LoginRequiredMixin, TemplateView):
    template_name = 'solicitudes/recibos.html'

class FirmarReciboView(LoginRequiredMixin, TemplateView):
    template_name = 'solicitudes/firmar_recibo.html'
