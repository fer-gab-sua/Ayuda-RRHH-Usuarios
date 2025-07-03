from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.views import LoginView as AuthLoginView, LogoutView as AuthLogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import base64
from django.core.files.base import ContentFile
from django.utils import timezone
from .models import Empleado, DomicilioEmpleado, ObraSocialEmpleado, SolicitudCambio, FamiliarEmpleado, ActividadEmpleado
from .forms import PerfilBasicoForm, DatosEmergenciaForm, FamiliarForm, DomicilioForm, ObraSocialForm, DeclaracionJuradaForm, FirmaDigitalForm, SubirFotoForm

class LoginView(AuthLoginView):
    template_name = 'empleados/login.html'
    
class LogoutView(AuthLogoutView):
    pass

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'empleados/dashboard.html'

class PerfilView(LoginRequiredMixin, TemplateView):
    template_name = 'empleados/perfil.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener o crear empleado
        empleado, created = Empleado.objects.get_or_create(
            user=self.request.user,
            defaults={
                'legajo': f"EMP{self.request.user.id:04d}",
                'dni': '12345678',
                'cuil': '20-12345678-9',
                'telefono': '+54 11 1234-5678',
                'contacto_emergencia': 'María Pérez',
                'telefono_emergencia': '+54 11 9876-5432',
                'relacion_emergencia': 'Esposa',
                'puesto': 'Desarrollador',
            }
        )
        
        # Obtener o crear domicilio
        domicilio, created = DomicilioEmpleado.objects.get_or_create(
            empleado=empleado,
            defaults={
                'calle': 'Av. Corrientes',
                'numero': '1234',
                'piso': '5',
                'depto': 'B',
                'barrio': 'Centro',
                'localidad': 'CABA',
                'provincia': 'Buenos Aires',
                'codigo_postal': '1043',
                'entre_calles': 'Entre Talcahuano y Uruguay',
            }
        )
        
        # Obtener o crear obra social
        obra_social, created = ObraSocialEmpleado.objects.get_or_create(
            empleado=empleado,
            defaults={
                'nombre': 'OSDE',
                'numero_afiliado': '123456789/01',
                'plan': 'Plan 210',
            }
        )
        
        # Obtener familiares
        familiares = FamiliarEmpleado.objects.filter(empleado=empleado)
        
        # Obtener actividades recientes
        actividades = ActividadEmpleado.objects.filter(empleado=empleado)[:5]
        
        # Verificar solicitudes pendientes
        solicitudes_pendientes = SolicitudCambio.objects.filter(
            empleado=empleado,
            estado__in=['pendiente', 'en_revision']
        ).exists()
        
        context.update({
            'empleado': empleado,
            'domicilio': domicilio,
            'obra_social': obra_social,
            'familiares': familiares,
            'actividades': actividades,
            'solicitudes_pendientes': solicitudes_pendientes,
            'tiene_firma': bool(empleado.firma_imagen),
        })
        return context

class EditarPerfilView(LoginRequiredMixin, TemplateView):
    template_name = 'empleados/editar_perfil.html'

class CrearFirmaView(LoginRequiredMixin, TemplateView):
    template_name = 'empleados/crear_firma.html'

class EditarFirmaView(LoginRequiredMixin, TemplateView):
    template_name = 'empleados/editar_firma.html'


# ====== FUNCIONALIDADES AJAX ======

@login_required
@require_POST
def subir_foto_perfil(request):
    """Subir foto de perfil"""
    try:
        empleado = get_object_or_404(Empleado, user=request.user)
        form = SubirFotoForm(request.POST, request.FILES, instance=empleado)
        
        if form.is_valid():
            form.save()
            
            # Registrar actividad
            ActividadEmpleado.objects.create(
                empleado=empleado,
                descripcion="Actualizó su foto de perfil"
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Foto de perfil actualizada correctamente',
                'foto_url': empleado.foto_perfil.url if empleado.foto_perfil else None
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al subir la foto: {str(e)}'
        })

@login_required
@require_POST
def guardar_datos_basicos(request):
    """Guardar email y teléfono"""
    try:
        empleado = get_object_or_404(Empleado, user=request.user)
        form = PerfilBasicoForm(request.POST, instance=empleado, user=request.user)
        
        if form.is_valid():
            form.save()
            
            # Registrar actividad
            ActividadEmpleado.objects.create(
                empleado=empleado,
                descripcion="Actualizó sus datos de contacto (email/teléfono)"
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Datos actualizados correctamente'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al guardar: {str(e)}'
        })

@login_required
@require_POST
def guardar_datos_emergencia(request):
    """Guardar datos de emergencia"""
    try:
        empleado = get_object_or_404(Empleado, user=request.user)
        form = DatosEmergenciaForm(request.POST, instance=empleado)
        
        if form.is_valid():
            form.save()
            
            # Registrar actividad
            ActividadEmpleado.objects.create(
                empleado=empleado,
                descripcion="Actualizó sus datos de emergencia"
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Datos de emergencia actualizados correctamente'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al guardar: {str(e)}'
        })

@login_required
@require_POST
def agregar_familiar(request):
    """Agregar nuevo familiar"""
    try:
        empleado = get_object_or_404(Empleado, user=request.user)
        form = FamiliarForm(request.POST)
        
        if form.is_valid():
            familiar = form.save(commit=False)
            familiar.empleado = empleado
            familiar.save()
            
            # Registrar actividad
            ActividadEmpleado.objects.create(
                empleado=empleado,
                descripcion=f"Agregó a {familiar.apellido}, {familiar.nombre} como familiar"
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Familiar agregado correctamente',
                'familiar': {
                    'id': familiar.id,
                    'apellido': familiar.apellido,
                    'nombre': familiar.nombre,
                    'fecha_nacimiento': familiar.fecha_nacimiento.strftime('%d/%m/%Y'),
                    'dni': familiar.dni,
                    'parentesco': familiar.get_parentesco_display()
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al agregar familiar: {str(e)}'
        })

@login_required
@require_POST
def eliminar_familiar(request):
    """Eliminar familiar"""
    try:
        familiar_id = request.POST.get('familiar_id')
        empleado = get_object_or_404(Empleado, user=request.user)
        familiar = get_object_or_404(FamiliarEmpleado, id=familiar_id, empleado=empleado)
        
        nombre_familiar = f"{familiar.apellido}, {familiar.nombre}"
        familiar.delete()
        
        # Registrar actividad
        ActividadEmpleado.objects.create(
            empleado=empleado,
            descripcion=f"Eliminó a {nombre_familiar} de su grupo familiar"
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Familiar eliminado correctamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al eliminar familiar: {str(e)}'
        })

@login_required
def solicitar_cambio_domicilio(request):
    """Solicitar cambio de domicilio con declaración jurada"""
    if request.method == 'POST':
        try:
            print(f"Solicitud de cambio de domicilio recibida de usuario: {request.user}")
            print(f"Datos POST: {request.POST}")
            
            empleado = get_object_or_404(Empleado, user=request.user)
            
            # Verificar que tenga firma digital
            if not empleado.firma_imagen:
                return JsonResponse({
                    'success': False,
                    'message': 'Debes crear tu firma digital antes de realizar solicitudes con declaración jurada.'
                })
            
            # Validar PIN de la firma
            pin_ingresado = request.POST.get('pin_firma')
            if not pin_ingresado:
                return JsonResponse({
                    'success': False,
                    'message': 'Debes ingresar el PIN de tu firma digital.'
                })
            
            # Debug logging
            print(f"PIN recibido: '{pin_ingresado}'")
            print(f"PIN almacenado: '{empleado.firma_pin}'")
            print(f"Empleado tiene firma: {bool(empleado.firma_imagen)}")
            
            if empleado.firma_pin != pin_ingresado:
                return JsonResponse({
                    'success': False,
                    'message': 'PIN incorrecto. Verifica tu PIN de firma digital.'
                })
            
            # Verificar que no tenga solicitudes pendientes
            solicitud_pendiente = SolicitudCambio.objects.filter(
                empleado=empleado,
                tipo='domicilio',
                estado__in=['pendiente', 'en_revision']
            ).exists()
            
            if solicitud_pendiente:
                return JsonResponse({
                    'success': False,
                    'message': 'Ya tienes una solicitud de cambio de domicilio pendiente'
                })
            
            # Procesar formularios
            domicilio_form = DomicilioForm(request.POST)
            ddjj_form = DeclaracionJuradaForm(request.POST)
            
            if domicilio_form.is_valid() and ddjj_form.is_valid():
                # Obtener datos actuales
                domicilio_actual = getattr(empleado, 'domicilio', None)
                datos_antiguos = {}
                if domicilio_actual:
                    datos_antiguos = {
                        'calle': domicilio_actual.calle,
                        'numero': domicilio_actual.numero,
                        'piso': domicilio_actual.piso,
                        'depto': domicilio_actual.depto,
                        'barrio': domicilio_actual.barrio,
                        'localidad': domicilio_actual.localidad,
                        'provincia': domicilio_actual.provincia,
                        'codigo_postal': domicilio_actual.codigo_postal,
                        'entre_calles': domicilio_actual.entre_calles,
                        'observaciones': domicilio_actual.observaciones,
                    }
                
                # Crear solicitud
                solicitud = SolicitudCambio.objects.create(
                    empleado=empleado,
                    tipo='domicilio',
                    datos_antiguos=datos_antiguos,
                    datos_nuevos=domicilio_form.cleaned_data,
                    declaracion_jurada="Declaro bajo juramento que los datos proporcionados son veraces y solicito el cambio de domicilio. Firmado digitalmente con PIN autenticado."
                )
                
                # Registrar actividad
                ActividadEmpleado.objects.create(
                    empleado=empleado,
                    descripcion="Solicitó cambio de domicilio mediante declaración jurada autenticada con firma digital"
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Solicitud de cambio de domicilio enviada correctamente. Será revisada por RRHH.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'errors': {**domicilio_form.errors, **ddjj_form.errors}
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al procesar solicitud: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required
def solicitar_cambio_obra_social(request):
    """Solicitar cambio de obra social con declaración jurada"""
    if request.method == 'POST':
        try:
            empleado = get_object_or_404(Empleado, user=request.user)
            
            # Verificar que tenga firma digital
            if not empleado.firma_imagen:
                return JsonResponse({
                    'success': False,
                    'message': 'Debes crear tu firma digital antes de realizar solicitudes con declaración jurada.'
                })
            
            # Validar PIN de la firma
            pin_ingresado = request.POST.get('pin_firma')
            if not pin_ingresado:
                return JsonResponse({
                    'success': False,
                    'message': 'Debes ingresar el PIN de tu firma digital.'
                })
            
            if empleado.firma_pin != pin_ingresado:
                return JsonResponse({
                    'success': False,
                    'message': 'PIN incorrecto. Verifica tu PIN de firma digital.'
                })
            
            # Verificar que no tenga solicitudes pendientes
            solicitud_pendiente = SolicitudCambio.objects.filter(
                empleado=empleado,
                tipo='obra_social',
                estado__in=['pendiente', 'en_revision']
            ).exists()
            
            if solicitud_pendiente:
                return JsonResponse({
                    'success': False,
                    'message': 'Ya tienes una solicitud de cambio de obra social pendiente'
                })
            
            # Procesar formularios
            obra_social_form = ObraSocialForm(request.POST)
            ddjj_form = DeclaracionJuradaForm(request.POST)
            
            if obra_social_form.is_valid() and ddjj_form.is_valid():
                # Obtener datos actuales
                obra_social_actual = getattr(empleado, 'obra_social', None)
                datos_antiguos = {}
                if obra_social_actual:
                    datos_antiguos = {
                        'nombre': obra_social_actual.nombre,
                        'numero_afiliado': obra_social_actual.numero_afiliado,
                        'plan': obra_social_actual.plan,
                        'fecha_alta': obra_social_actual.fecha_alta.isoformat() if obra_social_actual.fecha_alta else None,
                        'observaciones': obra_social_actual.observaciones,
                    }
                
                # Crear solicitud
                solicitud = SolicitudCambio.objects.create(
                    empleado=empleado,
                    tipo='obra_social',
                    datos_antiguos=datos_antiguos,
                    datos_nuevos=obra_social_form.cleaned_data,
                    declaracion_jurada="Declaro bajo juramento que los datos proporcionados son veraces y solicito el cambio de obra social. Firmado digitalmente con PIN autenticado."
                )
                
                # Registrar actividad
                ActividadEmpleado.objects.create(
                    empleado=empleado,
                    descripcion="Solicitó cambio de obra social mediante declaración jurada autenticada con firma digital"
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Solicitud de cambio de obra social enviada correctamente. Será revisada por RRHH.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'errors': {**obra_social_form.errors, **ddjj_form.errors}
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al procesar solicitud: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required
@require_POST
def guardar_firma_digital(request):
    """Guardar firma digital"""
    try:
        empleado = get_object_or_404(Empleado, user=request.user)
        form = FirmaDigitalForm(request.POST)
        
        if form.is_valid():
            # Decodificar la imagen de la firma
            firma_data = form.cleaned_data['firma_data']
            
            # La firma viene como data URL, necesitamos extraer solo los datos base64
            if firma_data.startswith('data:image/'):
                header, data = firma_data.split(',', 1)
                firma_bytes = base64.b64decode(data)
                
                # Crear archivo de imagen
                filename = f"firma_{empleado.user.username}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.png"
                firma_file = ContentFile(firma_bytes, name=filename)
                
                # Guardar en el modelo
                empleado.firma_imagen = firma_file
                empleado.firma_pin = form.cleaned_data['pin']
                empleado.save()
                
                # Registrar actividad
                ActividadEmpleado.objects.create(
                    empleado=empleado,
                    descripcion="Creó/actualizó su firma digital"
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Firma digital guardada correctamente',
                    'firma_url': empleado.firma_imagen.url
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Formato de firma inválido'
                })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al guardar firma: {str(e)}'
        })
