from django.urls import path
from . import views

app_name = 'empleados'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('cambiar-password/', views.CambiarPasswordObligatorioView.as_view(), name='cambiar_password_obligatorio'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('perfil/', views.PerfilView.as_view(), name='perfil'),
    path('perfil/editar/', views.EditarPerfilView.as_view(), name='editar_perfil'),
    path('firma/crear/', views.CrearFirmaView.as_view(), name='crear_firma'),
    path('firma/editar/', views.EditarFirmaView.as_view(), name='editar_firma'),
    
    # URLs AJAX para funcionalidades del perfil
    path('ajax/subir-foto/', views.subir_foto_perfil, name='subir_foto_perfil'),
    path('ajax/guardar-datos-basicos/', views.guardar_datos_basicos, name='guardar_datos_basicos'),
    path('ajax/guardar-datos-emergencia/', views.guardar_datos_emergencia, name='guardar_datos_emergencia'),
    path('ajax/agregar-familiar/', views.agregar_familiar, name='agregar_familiar'),
    path('ajax/eliminar-familiar/', views.eliminar_familiar, name='eliminar_familiar'),
    path('ajax/solicitar-cambio-domicilio/', views.solicitar_cambio_domicilio, name='solicitar_cambio_domicilio'),
    path('ajax/generar-pdf-preview-domicilio/', views.generar_pdf_preview_domicilio, name='generar_pdf_preview_domicilio'),
    path('ajax/solicitar-cambio-obra-social/', views.solicitar_cambio_obra_social, name='solicitar_cambio_obra_social'),
    path('ajax/guardar-firma/', views.guardar_firma_digital, name='guardar_firma_digital'),
    path('ajax/generar-pdf-preview-obra-social/', views.generar_pdf_preview_obra_social, name='generar_pdf_preview_obra_social'),
    
    # URLs para PDFs
    path('pdf/declaracion/<int:solicitud_id>/', views.ver_pdf_declaracion, name='ver_pdf_declaracion'),
    path('pdf/declaracion/<int:solicitud_id>/descargar/', views.descargar_pdf_declaracion, name='descargar_pdf_declaracion'),
]
