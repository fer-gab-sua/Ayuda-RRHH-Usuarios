from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as AuthLoginView
from django.views.generic import TemplateView

class RRHHLoginView(AuthLoginView):
    template_name = 'rrhh/login.html'

class RRHHDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'rrhh/dashboard.html'

class EmpleadosListView(LoginRequiredMixin, TemplateView):
    template_name = 'rrhh/empleados.html'

class CrearEmpleadoView(LoginRequiredMixin, TemplateView):
    template_name = 'rrhh/crear_empleado.html'

class EditarEmpleadoView(LoginRequiredMixin, TemplateView):
    template_name = 'rrhh/editar_empleado.html'

class DocumentosRRHHListView(LoginRequiredMixin, TemplateView):
    template_name = 'rrhh/documentos.html'

class AprobarDocumentoView(LoginRequiredMixin, TemplateView):
    template_name = 'rrhh/aprobar_documento.html'

class SolicitudesRRHHListView(LoginRequiredMixin, TemplateView):
    template_name = 'rrhh/solicitudes.html'

class GestionarSolicitudView(LoginRequiredMixin, TemplateView):
    template_name = 'rrhh/gestionar_solicitud.html'

class RecibosRRHHListView(LoginRequiredMixin, TemplateView):
    template_name = 'rrhh/recibos.html'

class SubirReciboView(LoginRequiredMixin, TemplateView):
    template_name = 'rrhh/subir_recibo.html'
