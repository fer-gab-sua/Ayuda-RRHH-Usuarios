from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.views import LoginView as AuthLoginView, LogoutView as AuthLogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.decorators.clickjacking import xframe_options_exempt
from django.urls import reverse
import json
import base64
from django.core.files.base import ContentFile
from django.utils import timezone
from .models import Empleado, DomicilioEmpleado, ObraSocialEmpleado, SolicitudCambio, FamiliarEmpleado, ActividadEmpleado
from .forms import PerfilBasicoForm, DatosEmergenciaForm, FamiliarForm, DomicilioForm, ObraSocialForm, DeclaracionJuradaForm, FirmaDigitalForm, SubirFotoForm
from .utils import generar_pdf_declaracion_domicilio, generar_pdf_declaracion_obra_social

def solo_empleados(view_func):
    """Decorador para permitir solo a empleados no-RRHH"""
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                empleado = Empleado.objects.get(user=request.user)
                if empleado.es_rrhh:
                    return redirect('rrhh:dashboard')
            except Empleado.DoesNotExist:
                pass
        return view_func(request, *args, **kwargs)
    return wrapper

class SoloEmpleadosMixin:
    """Mixin para views basadas en clase que solo permite empleados no-RRHH"""
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                empleado = Empleado.objects.get(user=request.user)
                if empleado.es_rrhh:
                    return redirect('rrhh:dashboard')
            except Empleado.DoesNotExist:
                pass
        return super().dispatch(request, *args, **kwargs)

class LoginView(AuthLoginView):
    template_name = 'empleados/login.html'

    def get_success_url(self):
        try:
            empleado = Empleado.objects.get(user=self.request.user)
            if empleado.es_rrhh:
                return '/rrhh/dashboard/'
        except Empleado.DoesNotExist:
            pass
        return '/empleados/dashboard/'

class LogoutView(AuthLogoutView):
    pass

class DashboardView(LoginRequiredMixin, SoloEmpleadosMixin, TemplateView):
    template_name = 'empleados/dashboard.html'

class PerfilView(LoginRequiredMixin, SoloEmpleadosMixin, TemplateView):
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
            }
        )
        
        # Obtener familiares
        familiares = FamiliarEmpleado.objects.filter(empleado=empleado)
        
        # Obtener actividades recientes
        actividades = ActividadEmpleado.objects.filter(empleado=empleado)[:5]
        
        # Verificar solicitudes pendientes por tipo
        solicitudes_pendientes = SolicitudCambio.objects.filter(
            empleado=empleado,
            estado__in=['pendiente', 'en_revision']
        )
        
        # Separar por tipo
        solicitud_domicilio_pendiente = solicitudes_pendientes.filter(tipo='domicilio').first()
        solicitud_obra_social_pendiente = solicitudes_pendientes.filter(tipo='obra_social').first()
        
        context.update({
            'empleado': empleado,
            'domicilio': domicilio,
            'obra_social': obra_social,
            'familiares': familiares,
            'actividades': actividades,
            'solicitudes_pendientes': solicitudes_pendientes,
            'solicitud_domicilio_pendiente': solicitud_domicilio_pendiente,
            'solicitud_obra_social_pendiente': solicitud_obra_social_pendiente,
            'tiene_firma': bool(empleado.firma_imagen),
        })
        return context

class EditarPerfilView(LoginRequiredMixin, SoloEmpleadosMixin, TemplateView):
    template_name = 'empleados/editar_perfil.html'

class CrearFirmaView(LoginRequiredMixin, SoloEmpleadosMixin, TemplateView):
    template_name = 'empleados/crear_firma.html'

class EditarFirmaView(LoginRequiredMixin, SoloEmpleadosMixin, TemplateView):
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
    """Procesar solicitud de cambio de domicilio ya firmada"""
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
                print(f"PIN incorrecto para empleado {empleado.legajo}")
                return JsonResponse({
                    'success': False,
                    'message': 'PIN incorrecto. Verifica tu PIN de firma digital.'
                })
            
            # Recuperar datos del preview de la sesión
            pdf_preview_data = request.session.get('pdf_preview_data')
            if not pdf_preview_data:
                return JsonResponse({
                    'success': False,
                    'message': 'No se encontraron datos del formulario. Por favor, completa el formulario nuevamente.'
                })
            
            # Verificar que no tenga solicitudes pendientes de domicilio
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
            
            # Crear solicitud con los datos del preview
            solicitud = SolicitudCambio.objects.create(
                empleado=empleado,
                tipo='domicilio',
                datos_antiguos=pdf_preview_data['datos_antiguos'],
                datos_nuevos=pdf_preview_data['datos_nuevos'],
                declaracion_jurada="Declaro bajo juramento que los datos proporcionados son veraces y solicito el cambio de domicilio. Firmado digitalmente con PIN autenticado."
            )
            
            # Generar PDF firmado final CON FIRMA
            try:
                pdf_content = generar_pdf_declaracion_domicilio(solicitud, empleado, incluir_firma=True)
                pdf_filename = f"declaracion_domicilio_{empleado.legajo}_{solicitud.id}.pdf"
                
                # Guardar el PDF en el campo del modelo
                solicitud.pdf_declaracion.save(
                    pdf_filename,
                    ContentFile(pdf_content),
                    save=True
                )
                
                print(f"PDF generado exitosamente: {pdf_filename}")
                
            except Exception as e:
                print(f"Error al generar PDF: {str(e)}")
                # Aunque falle el PDF, la solicitud se mantiene
            
            # Limpiar datos de sesión
            if 'pdf_preview_data' in request.session:
                del request.session['pdf_preview_data']
            
            # Registrar actividad
            ActividadEmpleado.objects.create(
                empleado=empleado,
                descripcion="Solicitó cambio de domicilio mediante declaración jurada autenticada con firma digital"
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Solicitud de cambio de domicilio enviada correctamente. Será revisada por RRHH.',
                'solicitud_id': solicitud.id
            })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al procesar solicitud: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required
def solicitar_cambio_obra_social(request):
    """Procesar solicitud de cambio de obra social ya firmada"""
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
            
            # Recuperar datos del preview de la sesión
            pdf_preview_data = request.session.get('pdf_preview_data_obra_social')
            if not pdf_preview_data:
                return JsonResponse({
                    'success': False,
                    'message': 'No se encontraron datos del formulario. Por favor, completa el formulario nuevamente.'
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
            
            # Crear solicitud con los datos del preview
            solicitud = SolicitudCambio.objects.create(
                empleado=empleado,
                tipo='obra_social',
                datos_antiguos=pdf_preview_data['datos_antiguos'],
                datos_nuevos=pdf_preview_data['datos_nuevos'],
                declaracion_jurada="Declaro bajo juramento que los datos proporcionados son veraces y solicito el cambio de obra social. Firmado digitalmente con PIN autenticado."
            )
            
            # Guardar archivo adjunto si existe
            if pdf_preview_data.get('archivo_adjunto'):
                import base64
                from django.core.files.base import ContentFile
                
                archivo_info = pdf_preview_data['archivo_adjunto']
                archivo_content = base64.b64decode(archivo_info['content'])
                archivo_file = ContentFile(archivo_content, name=archivo_info['name'])
                solicitud.archivo_adjunto.save(archivo_info['name'], archivo_file, save=True)
            
            # Generar PDF firmado final CON FIRMA
            try:
                pdf_content = generar_pdf_declaracion_obra_social(solicitud, empleado, incluir_firma=True)
                pdf_filename = f"declaracion_obra_social_{empleado.legajo}_{solicitud.id}.pdf"
                
                # Guardar el PDF en el campo del modelo
                solicitud.pdf_declaracion.save(
                    pdf_filename,
                    ContentFile(pdf_content),
                    save=True
                )
                
                print(f"PDF generado exitosamente: {pdf_filename}")
                
            except Exception as e:
                print(f"Error al generar PDF: {str(e)}")
                # Aunque falle el PDF, la solicitud se mantiene
            
            # Limpiar datos de sesión
            if 'pdf_preview_data_obra_social' in request.session:
                del request.session['pdf_preview_data_obra_social']
            
            # Registrar actividad
            ActividadEmpleado.objects.create(
                empleado=empleado,
                descripcion="Solicitó cambio de obra social mediante declaración jurada autenticada con firma digital"
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Solicitud de cambio de obra social enviada correctamente. Será revisada por RRHH.',
                'solicitud_id': solicitud.id
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

@login_required
@xframe_options_exempt
def ver_pdf_declaracion(request, solicitud_id):
    """Ver PDF de declaración jurada"""
    try:
        solicitud = get_object_or_404(SolicitudCambio, id=solicitud_id, empleado__user=request.user)
        
        if not solicitud.pdf_declaracion:
            return JsonResponse({
                'success': False,
                'message': 'No se encontró el PDF de la declaración jurada'
            })
        
        # Abrir el archivo PDF
        response = HttpResponse(solicitud.pdf_declaracion.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="declaracion_{solicitud.tipo}_{solicitud.id}.pdf"'
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al acceder al PDF: {str(e)}'
        })

@login_required
@xframe_options_exempt
def descargar_pdf_declaracion(request, solicitud_id):
    """Descargar PDF de declaración jurada"""
    try:
        solicitud = get_object_or_404(SolicitudCambio, id=solicitud_id, empleado__user=request.user)
        
        if not solicitud.pdf_declaracion:
            return JsonResponse({
                'success': False,
                'message': 'No se encontró el PDF de la declaración jurada'
            })
        
        # Descargar el archivo PDF
        response = HttpResponse(solicitud.pdf_declaracion.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="declaracion_{solicitud.tipo}_{solicitud.id}.pdf"'
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al descargar el PDF: {str(e)}'
        })

@login_required
def generar_pdf_preview_domicilio(request):
    """Generar PDF preview para mostrar antes de firmar"""
    if request.method == 'POST':
        try:
            empleado = get_object_or_404(Empleado, user=request.user)
            
            # Validar formulario
            domicilio_form = DomicilioForm(request.POST)
            if not domicilio_form.is_valid():
                return JsonResponse({
                    'success': False,
                    'errors': domicilio_form.errors
                })
            
            # Crear solicitud temporal (sin guardar aún)
            datos_antiguos = {}
            domicilio_actual = getattr(empleado, 'domicilio', None)
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
            
            # Crear objeto temporal para generar PDF
            from types import SimpleNamespace
            solicitud_temp = SimpleNamespace(
                id='PREVIEW',
                empleado=empleado,
                fecha_solicitud=timezone.now(),
                datos_antiguos=datos_antiguos,
                datos_nuevos=domicilio_form.cleaned_data,
                tipo='domicilio'
            )
            
            # Generar PDF SIN FIRMA (solo preview)
            pdf_content = generar_pdf_declaracion_domicilio(solicitud_temp, empleado, incluir_firma=False)
            
            # Convertir datos nuevos a formato serializable
            datos_nuevos_serializable = {}
            for key, value in domicilio_form.cleaned_data.items():
                if hasattr(value, 'isoformat'):  # Es una fecha
                    datos_nuevos_serializable[key] = value.isoformat() if value else None
                else:
                    datos_nuevos_serializable[key] = value
            
            # Guardar temporalmente en sesión
            request.session['pdf_preview_data'] = {
                'datos_antiguos': datos_antiguos,
                'datos_nuevos': datos_nuevos_serializable,
                'timestamp': timezone.now().isoformat()
            }
            
            # Retornar PDF como respuesta
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = 'inline; filename="preview_cambio_domicilio.pdf"'
            
            return response
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al generar PDF: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required
def generar_pdf_preview_obra_social(request):
    """Generar PDF preview para cambio de obra social antes de firmar"""
    if request.method == 'POST':
        try:
            # Limpiar datos de sesión previos para evitar conflictos
            if 'pdf_preview_data_obra_social' in request.session:
                del request.session['pdf_preview_data_obra_social']
            
            empleado = get_object_or_404(Empleado, user=request.user)
            
            # Validar formulario
            obra_social_form = ObraSocialForm(request.POST, request.FILES)
            if not obra_social_form.is_valid():
                return JsonResponse({
                    'success': False,
                    'errors': obra_social_form.errors
                })
            
            # Establecer fecha de alta automáticamente como hoy
            datos_formulario = obra_social_form.cleaned_data.copy()
            datos_formulario['fecha_alta'] = timezone.now().date()
            
            # Remover archivo_adjunto de los datos del formulario para evitar problemas de serialización
            if 'archivo_adjunto' in datos_formulario:
                del datos_formulario['archivo_adjunto']
            
            # Crear solicitud temporal (sin guardar aún)
            datos_antiguos = {}
            obra_social_actual = getattr(empleado, 'obra_social', None)
            if obra_social_actual:
                datos_antiguos = {
                    'nombre': obra_social_actual.nombre,
                    'fecha_alta': obra_social_actual.fecha_alta.isoformat() if obra_social_actual.fecha_alta else None,
                    'observaciones': obra_social_actual.observaciones,
                }
            
            # Manejar archivo adjunto
            archivo_adjunto_session = None
            archivo_adjunto_pdf = None
            if 'archivo_adjunto' in request.FILES:
                archivo_adjunto = request.FILES['archivo_adjunto']
                
                # Para el PDF: crear un objeto simple con solo la información necesaria
                from types import SimpleNamespace
                archivo_adjunto_pdf = SimpleNamespace(
                    name=archivo_adjunto.name,
                    size=archivo_adjunto.size
                )
                
                # Para la sesión: guardar en base64
                import base64
                archivo_content = archivo_adjunto.read()
                archivo_adjunto_session = {
                    'name': archivo_adjunto.name,
                    'content': base64.b64encode(archivo_content).decode('utf-8'),
                    'size': archivo_adjunto.size
                }
            # Crear objeto temporal para generar PDF
            from types import SimpleNamespace
            solicitud_temp = SimpleNamespace(
                id='PREVIEW',
                empleado=empleado,
                fecha_solicitud=timezone.now(),
                datos_antiguos=datos_antiguos,
                datos_nuevos=datos_formulario,
                tipo='obra_social',
                archivo_adjunto=archivo_adjunto_pdf
            )
            
            # Generar PDF SIN FIRMA (solo preview)
            pdf_content = generar_pdf_declaracion_obra_social(solicitud_temp, empleado, incluir_firma=False)
            
            # Convertir datos nuevos a formato serializable
            datos_nuevos_serializable = {}
            for key, value in datos_formulario.items():
                if hasattr(value, 'isoformat'):  # Es una fecha
                    datos_nuevos_serializable[key] = value.isoformat() if value else None
                else:
                    datos_nuevos_serializable[key] = value
            
            # Guardar temporalmente en sesión
            request.session['pdf_preview_data_obra_social'] = {
                'datos_antiguos': datos_antiguos,
                'datos_nuevos': datos_nuevos_serializable,
                'archivo_adjunto': archivo_adjunto_session,
                'timestamp': timezone.now().isoformat()
            }
            
            # Retornar PDF como respuesta (igual que domicilio)
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = 'inline; filename="preview_cambio_obra_social.pdf"'
            
            return response
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al generar PDF: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})