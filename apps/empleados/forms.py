from django import forms
from django.contrib.auth.models import User
from .models import Empleado, FamiliarEmpleado, DomicilioEmpleado, ObraSocialEmpleado, SolicitudCambio

class PerfilBasicoForm(forms.ModelForm):
    """Formulario para campos básicos editables del perfil"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Empleado
        fields = ['telefono']
        widgets = {
            'telefono': forms.TextInput(attrs={'class': 'form-control'})
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['email'].initial = self.user.email

    def save(self, commit=True):
        empleado = super().save(commit=False)
        if commit:
            empleado.save()
            # Actualizar email del usuario
            if self.user:
                self.user.email = self.cleaned_data['email']
                self.user.save()
        return empleado

class DatosEmergenciaForm(forms.ModelForm):
    """Formulario para datos de emergencia"""
    class Meta:
        model = Empleado
        fields = ['contacto_emergencia', 'telefono_emergencia', 'relacion_emergencia']
        widgets = {
            'contacto_emergencia': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_emergencia': forms.TextInput(attrs={'class': 'form-control'}),
            'relacion_emergencia': forms.TextInput(attrs={'class': 'form-control'}),
        }

class FamiliarForm(forms.ModelForm):
    """Formulario para agregar/editar familiares"""
    class Meta:
        model = FamiliarEmpleado
        fields = ['apellido', 'nombre', 'fecha_nacimiento', 'dni', 'parentesco']
        widgets = {
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'parentesco': forms.Select(attrs={'class': 'form-control'}),
        }

class DomicilioForm(forms.ModelForm):
    """Formulario para solicitud de cambio de domicilio"""
    class Meta:
        model = DomicilioEmpleado
        fields = ['calle', 'numero', 'piso', 'depto', 'barrio', 'localidad', 
                 'provincia', 'codigo_postal', 'entre_calles', 'observaciones']
        widgets = {
            'calle': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'piso': forms.TextInput(attrs={'class': 'form-control'}),
            'depto': forms.TextInput(attrs={'class': 'form-control'}),
            'barrio': forms.TextInput(attrs={'class': 'form-control'}),
            'localidad': forms.TextInput(attrs={'class': 'form-control'}),
            'provincia': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_postal': forms.TextInput(attrs={'class': 'form-control'}),
            'entre_calles': forms.TextInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ObraSocialForm(forms.ModelForm):
    """Formulario para solicitud de cambio de obra social"""
    class Meta:
        model = ObraSocialEmpleado
        fields = ['nombre', 'numero_afiliado', 'plan', 'fecha_alta', 'observaciones']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_afiliado': forms.TextInput(attrs={'class': 'form-control'}),
            'plan': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_alta': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DeclaracionJuradaForm(forms.Form):
    """Formulario para la declaración jurada"""
    tipo_solicitud = forms.CharField(widget=forms.HiddenInput())
    
    # Campos comunes de la declaración jurada
    acepto_terminos = forms.BooleanField(
        required=True,
        label="Declaro bajo juramento que los datos proporcionados son veraces y completos"
    )
    
    # Campo para la firma (se llenará con JavaScript)
    firma_data = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    def clean_acepto_terminos(self):
        acepto = self.cleaned_data.get('acepto_terminos')
        if not acepto:
            raise forms.ValidationError("Debe aceptar los términos para continuar")
        return acepto

class FirmaDigitalForm(forms.Form):
    """Formulario para crear/actualizar firma digital"""
    firma_data = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    pin = forms.CharField(
        max_length=6,
        min_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'PIN de 4-6 dígitos'
        }),
        help_text="Ingresa un PIN de 4 a 6 dígitos para proteger tu firma"
    )
    confirmar_pin = forms.CharField(
        max_length=6,
        min_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirma tu PIN'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        pin = cleaned_data.get('pin')
        confirmar_pin = cleaned_data.get('confirmar_pin')
        
        if pin and confirmar_pin and pin != confirmar_pin:
            raise forms.ValidationError("Los PINs no coinciden")
        
        return cleaned_data

class SubirFotoForm(forms.ModelForm):
    """Formulario para subir foto de perfil"""
    class Meta:
        model = Empleado
        fields = ['foto_perfil']
        widgets = {
            'foto_perfil': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'form-control'
            })
        }
