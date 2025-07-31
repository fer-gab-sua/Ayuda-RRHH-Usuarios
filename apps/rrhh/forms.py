from django import forms
from django.contrib.auth.models import User
from apps.empleados.models import Empleado, DomicilioEmpleado
from django.core.exceptions import ValidationError
from .models import CargaMasivaRecibos
import datetime

class SubirRecibosForm(forms.Form):
    archivo = forms.FileField(label="Archivo de Recibos de Sueldo (PDF o TXT)", required=True)

class DomicilioEmpleadoForm(forms.ModelForm):
    class Meta:
        model = DomicilioEmpleado
        fields = [
            'calle', 'numero', 'piso', 'depto', 'barrio', 
            'localidad', 'provincia', 'codigo_postal', 
            'entre_calles', 'observaciones'
        ]
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'calle': 'Calle',
            'numero': 'Número',
            'piso': 'Piso',
            'depto': 'Departamento',
            'barrio': 'Barrio',
            'localidad': 'Localidad',
            'provincia': 'Provincia',
            'codigo_postal': 'Código Postal',
            'entre_calles': 'Entre calles',
            'observaciones': 'Observaciones'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar clases CSS de Bootstrap a todos los campos
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.widgets.Input):
                field.widget.attrs['class'] = 'form-control'
            elif isinstance(field.widget, forms.widgets.Select):
                field.widget.attrs['class'] = 'form-select'
            elif isinstance(field.widget, forms.widgets.Textarea):
                field.widget.attrs['class'] = 'form-control'

class CrearEmpleadoForm(forms.ModelForm):
    # Campos del User
    username = forms.CharField(
        max_length=150,
        label="Nombre de usuario",
        help_text="Nombre de usuario para acceder al sistema"
    )
    email = forms.EmailField(
        label="Correo electrónico",
        required=True
    )
    first_name = forms.CharField(
        max_length=150,
        label="Nombre",
        required=True
    )
    last_name = forms.CharField(
        max_length=150,
        label="Apellido",
        required=True
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput,
        label="Contraseña",
        help_text="Mínimo 8 caracteres"
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirmar contraseña"
    )
    
    class Meta:
        model = Empleado
        fields = [
            'legajo', 'numero_legajo', 'dni', 'cuil', 'fecha_nacimiento', 
            'telefono', 'puesto', 'departamento', 'supervisor', 
            'tipo_contrato', 'salario', 'fecha_contrato',
            'contacto_emergencia', 'telefono_emergencia', 'relacion_emergencia',
            'es_rrhh'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'fecha_contrato': forms.DateInput(attrs={'type': 'date'}),
            'salario': forms.NumberInput(attrs={'step': '0.01'}),
            'es_rrhh': forms.CheckboxInput()
        }
        labels = {
            'legajo': 'Legajo',
            'numero_legajo': 'Número de legajo',
            'dni': 'DNI',
            'cuil': 'CUIL',
            'fecha_nacimiento': 'Fecha de nacimiento',
            'telefono': 'Teléfono',
            'puesto': 'Puesto',
            'departamento': 'Departamento',
            'supervisor': 'Supervisor',
            'tipo_contrato': 'Tipo de contrato',
            'salario': 'Salario',
            'fecha_contrato': 'Fecha de contrato',
            'contacto_emergencia': 'Contacto de emergencia',
            'telefono_emergencia': 'Teléfono de emergencia',
            'relacion_emergencia': 'Relación de emergencia',
            'es_rrhh': '¿Es personal de RRHH?'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar clases CSS de Bootstrap a todos los campos
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.widgets.Input):
                field.widget.attrs['class'] = 'form-control'
            elif isinstance(field.widget, forms.widgets.Select):
                field.widget.attrs['class'] = 'form-select'
            elif isinstance(field.widget, forms.widgets.Textarea):
                field.widget.attrs['class'] = 'form-control'
            elif isinstance(field.widget, forms.widgets.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
                
        # Configurar campos específicos
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ingrese el nombre de usuario'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'ejemplo@empresa.com'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Contraseña segura'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Repita la contraseña'
        })

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Las contraseñas no coinciden")
        return password2

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Este nombre de usuario ya existe")
        return username

    def clean_legajo(self):
        legajo = self.cleaned_data.get('legajo')
        if Empleado.objects.filter(legajo=legajo).exists():
            raise ValidationError("Este legajo ya existe")
        return legajo

    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if Empleado.objects.filter(dni=dni).exists():
            raise ValidationError("Este DNI ya está registrado")
        return dni

class EditarEmpleadoForm(forms.ModelForm):
    # Campos del User
    username = forms.CharField(
        max_length=150,
        label="Nombre de usuario",
        help_text="Nombre de usuario para acceder al sistema"
    )
    email = forms.EmailField(
        label="Correo electrónico",
        required=True
    )
    first_name = forms.CharField(
        max_length=150,
        label="Nombre",
        required=True
    )
    last_name = forms.CharField(
        max_length=150,
        label="Apellido",
        required=True
    )
    
    class Meta:
        model = Empleado
        fields = [
            'legajo', 'numero_legajo', 'dni', 'cuil', 'fecha_nacimiento', 
            'telefono', 'puesto', 'departamento', 'supervisor', 
            'tipo_contrato', 'salario', 'fecha_contrato',
            'contacto_emergencia', 'telefono_emergencia', 'relacion_emergencia',
            'es_rrhh'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'fecha_contrato': forms.DateInput(attrs={'type': 'date'}),
            'salario': forms.NumberInput(attrs={'step': '0.01'}),
            'es_rrhh': forms.CheckboxInput()
        }
        labels = {
            'legajo': 'Legajo',
            'numero_legajo': 'Número de legajo',
            'dni': 'DNI',
            'cuil': 'CUIL',
            'fecha_nacimiento': 'Fecha de nacimiento',
            'telefono': 'Teléfono',
            'puesto': 'Puesto',
            'departamento': 'Departamento',
            'supervisor': 'Supervisor',
            'tipo_contrato': 'Tipo de contrato',
            'salario': 'Salario',
            'fecha_contrato': 'Fecha de contrato',
            'contacto_emergencia': 'Contacto de emergencia',
            'telefono_emergencia': 'Teléfono de emergencia',
            'relacion_emergencia': 'Relación de emergencia',
            'es_rrhh': '¿Es personal de RRHH?'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar clases CSS de Bootstrap a todos los campos
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.widgets.Input):
                field.widget.attrs['class'] = 'form-control'
            elif isinstance(field.widget, forms.widgets.Select):
                field.widget.attrs['class'] = 'form-select'
            elif isinstance(field.widget, forms.widgets.Textarea):
                field.widget.attrs['class'] = 'form-control'
            elif isinstance(field.widget, forms.widgets.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
                
        # Configurar campos específicos
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ingrese el nombre de usuario'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'ejemplo@empresa.com'
        })
        
        # Cargar datos del usuario asociado
        if self.instance and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(id=self.instance.user.id).exists():
            raise ValidationError("Este nombre de usuario ya existe")
        return username

    def clean_legajo(self):
        legajo = self.cleaned_data.get('legajo')
        if Empleado.objects.filter(legajo=legajo).exclude(id=self.instance.id).exists():
            raise ValidationError("Este legajo ya existe")
        return legajo

    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if Empleado.objects.filter(dni=dni).exclude(id=self.instance.id).exists():
            raise ValidationError("Este DNI ya está registrado")
        return dni

class CargaMasivaRecibosForm(forms.ModelForm):
    """Formulario para cargar recibos masivamente"""
    
    class Meta:
        model = CargaMasivaRecibos
        fields = ['tipo_recibo', 'periodo', 'anio', 'archivo_pdf', 'dias_vencimiento']
        widgets = {
            'tipo_recibo': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'periodo': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'anio': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2020,
                'max': 2030,
                'value': datetime.datetime.now().year,
                'required': True
            }),
            'archivo_pdf': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf',
                'required': True
            }),
            'dias_vencimiento': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 365,
                'value': 30,
                'required': True
            })
        }
        labels = {
            'tipo_recibo': 'Tipo de Recibo',
            'periodo': 'Período',
            'anio': 'Año',
            'archivo_pdf': 'Archivo PDF con Recibos',
            'dias_vencimiento': 'Días para Vencimiento'
        }
        help_texts = {
            'tipo_recibo': 'Selecciona si es sueldo regular, SAC 1 o SAC 2',
            'archivo_pdf': 'Selecciona el archivo PDF que contiene todos los recibos del período',
            'dias_vencimiento': 'Número de días desde la carga hasta el vencimiento de la firma'
        }
    
    def clean_archivo_pdf(self):
        archivo = self.cleaned_data.get('archivo_pdf')
        if archivo:
            if not archivo.name.lower().endswith('.pdf'):
                raise ValidationError('El archivo debe ser un PDF.')
            
            # Verificar tamaño del archivo (máximo 50MB)
            if archivo.size > 50 * 1024 * 1024:
                raise ValidationError('El archivo no puede ser mayor a 50MB.')
        
        return archivo
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Crear una instancia temporal para validar con el modelo
        if cleaned_data:
            temp_instance = CargaMasivaRecibos(**cleaned_data)
            try:
                temp_instance.clean()
            except ValidationError as e:
                raise ValidationError(e.message)
        
        return cleaned_data
