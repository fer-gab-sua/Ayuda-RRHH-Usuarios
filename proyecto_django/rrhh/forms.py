from django import forms
from django.contrib.auth.models import User
from .models import Empleado, Solicitud, TipoSolicitud, Documento


class PerfilForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, label='Nombre')
    last_name = forms.CharField(max_length=30, label='Apellido')
    email = forms.EmailField(label='Email')
    
    class Meta:
        model = Empleado
        fields = ['dni', 'fecha_nacimiento', 'telefono', 'direccion', 'ciudad', 
                 'codigo_postal', 'telefono_emergencia', 'contacto_emergencia', 
                 'foto_perfil']
        labels = {
            'dni': 'DNI',
            'fecha_nacimiento': 'Fecha de Nacimiento',
            'telefono': 'Teléfono',
            'direccion': 'Dirección',
            'ciudad': 'Ciudad',
            'codigo_postal': 'Código Postal',
            'telefono_emergencia': 'Teléfono de Emergencia',
            'contacto_emergencia': 'Contacto de Emergencia',
            'foto_perfil': 'Foto de Perfil',
        }
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'direccion': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email


class SolicitudForm(forms.ModelForm):
    class Meta:
        model = Solicitud
        fields = ['tipo', 'fecha_desde', 'fecha_hasta', 'motivo']
        labels = {
            'tipo': 'Tipo de Solicitud',
            'fecha_desde': 'Fecha Desde',
            'fecha_hasta': 'Fecha Hasta',
            'motivo': 'Motivo/Descripción',
        }
        widgets = {
            'fecha_desde': forms.DateInput(attrs={'type': 'date'}),
            'fecha_hasta': forms.DateInput(attrs={'type': 'date'}),
            'motivo': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo'].queryset = TipoSolicitud.objects.filter(activo=True)


class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ['nombre', 'archivo', 'descripcion']
        labels = {
            'nombre': 'Nombre del Documento',
            'archivo': 'Archivo',
            'descripcion': 'Descripción',
        }
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }
