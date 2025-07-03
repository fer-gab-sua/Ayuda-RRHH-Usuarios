from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

class DocumentosListView(LoginRequiredMixin, TemplateView):
    template_name = 'documentos/lista.html'

class SubirDocumentoView(LoginRequiredMixin, TemplateView):
    template_name = 'documentos/subir.html'

class FirmarDocumentoView(LoginRequiredMixin, TemplateView):
    template_name = 'documentos/firmar.html'

class DetalleDocumentoView(LoginRequiredMixin, TemplateView):
    template_name = 'documentos/detalle.html'
