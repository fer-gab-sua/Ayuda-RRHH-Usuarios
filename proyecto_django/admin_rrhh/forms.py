from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from rrhh.models import Empleado, ReciboSueldo, Documento, Notificacion
from datetime import date


class CrearEmpleadoForm(forms.Form):
    # Datos del usuario
    username = forms.CharField(max_length=150, label='Nombre de usuario')
    password = forms.CharField(widget=forms.PasswordInput, label='Contraseña')
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='Confirmar contraseña')
    first_name = forms.CharField(max_length=30, label='Nombre')
    last_name = forms.CharField(max_length=30, label='Apellido')
    email = forms.EmailField(label='Email')
    
    # Datos del empleado
    dni = forms.CharField(max_length=20, label='DNI')
    fecha_nacimiento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Fecha de nacimiento'
    )
    telefono = forms.CharField(max_length=20, label='Teléfono')
    direccion = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='Dirección')
    ciudad = forms.CharField(max_length=100, label='Ciudad')
    codigo_postal = forms.CharField(max_length=10, label='Código postal')
    telefono_emergencia = forms.CharField(max_length=20, label='Teléfono de emergencia')
    contacto_emergencia = forms.CharField(max_length=100, label='Contacto de emergencia')
    foto_perfil = forms.ImageField(required=False, label='Foto de perfil')
    
    # Datos laborales
    fecha_ingreso = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Fecha de ingreso'
    )
    puesto = forms.CharField(max_length=100, label='Puesto')
    departamento = forms.CharField(max_length=100, label='Departamento')
    salario = forms.DecimalField(max_digits=10, decimal_places=2, label='Salario')
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError('Este nombre de usuario ya existe')
        return username
    
    def clean_dni(self):
        dni = self.cleaned_data['dni']
        if Empleado.objects.filter(dni=dni).exists():
            raise ValidationError('Ya existe un empleado con este DNI')
        return dni
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError('Ya existe un usuario con este email')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise ValidationError('Las contraseñas no coinciden')
        
        return cleaned_data
    
    def save(self):
        # Crear usuario
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            email=self.cleaned_data['email']
        )
        
        # Crear empleado
        empleado = Empleado.objects.create(
            user=user,
            dni=self.cleaned_data['dni'],
            fecha_nacimiento=self.cleaned_data['fecha_nacimiento'],
            telefono=self.cleaned_data['telefono'],
            direccion=self.cleaned_data['direccion'],
            ciudad=self.cleaned_data['ciudad'],
            codigo_postal=self.cleaned_data['codigo_postal'],
            telefono_emergencia=self.cleaned_data['telefono_emergencia'],
            contacto_emergencia=self.cleaned_data['contacto_emergencia'],
            foto_perfil=self.cleaned_data['foto_perfil'],
            fecha_ingreso=self.cleaned_data['fecha_ingreso'],
            puesto=self.cleaned_data['puesto'],
            departamento=self.cleaned_data['departamento'],
            salario=self.cleaned_data['salario'],
        )
        
        return empleado


class EditarEmpleadoForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, label='Nombre')
    last_name = forms.CharField(max_length=30, label='Apellido')
    email = forms.EmailField(label='Email')
    
    class Meta:
        model = Empleado
        fields = [
            'dni', 'fecha_nacimiento', 'telefono', 'direccion', 'ciudad',
            'codigo_postal', 'telefono_emergencia', 'contacto_emergencia',
            'foto_perfil', 'puesto', 'departamento', 'salario'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'direccion': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'dni': 'DNI',
            'fecha_nacimiento': 'Fecha de nacimiento',
            'telefono': 'Teléfono',
            'direccion': 'Dirección',
            'ciudad': 'Ciudad',
            'codigo_postal': 'Código postal',
            'telefono_emergencia': 'Teléfono de emergencia',
            'contacto_emergencia': 'Contacto de emergencia',
            'foto_perfil': 'Foto de perfil',
            'puesto': 'Puesto',
            'departamento': 'Departamento',
            'salario': 'Salario',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
    
    def save(self, commit=True):
        empleado = super().save(commit=False)
        
        # Actualizar también el usuario
        user = empleado.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            empleado.save()
        
        return empleado


class SubirReciboForm(forms.ModelForm):
    class Meta:
        model = ReciboSueldo
        fields = ['empleado', 'fecha', 'periodo', 'archivo']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'empleado': 'Empleado',
            'fecha': 'Fecha del recibo',
            'periodo': 'Período (ej: Mayo 2024)',
            'archivo': 'Archivo PDF del recibo',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['empleado'].queryset = Empleado.objects.select_related('user').all()
        self.fields['empleado'].label_from_instance = lambda obj: f"{obj.user.get_full_name()} - {obj.dni}"


class DocumentoRRHHForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ['nombre', 'tipo', 'archivo', 'descripcion']
        labels = {
            'nombre': 'Nombre del documento',
            'tipo': 'Tipo de documento',
            'archivo': 'Archivo',
            'descripcion': 'Descripción',
        }
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }


class NotificacionForm(forms.Form):
    TIPO_DESTINATARIO_CHOICES = [
        ('todos', 'Todos los empleados'),
        ('departamento', 'Por departamento'),
        ('especifico', 'Empleado específico'),
    ]
    
    tipo_destinatario = forms.ChoiceField(
        choices=TIPO_DESTINATARIO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Tipo de Destinatario'
    )
    
    empleado_especifico = forms.ModelChoiceField(
        queryset=Empleado.objects.select_related('user').all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Empleado Específico',
        required=False
    )
    
    departamento = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Departamento',
        required=False
    )
    
    titulo = forms.CharField(
        max_length=200, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Título'
    )
    
    mensaje = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        label='Mensaje'
    )
    
    tipo = forms.ChoiceField(
        choices=Notificacion.TIPOS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Tipo de Notificación'
    )
    
    importante = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Marcar como importante'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Obtener departamentos únicos para el select
        departamentos = Empleado.objects.values_list('departamento', flat=True).distinct()
        self.fields['departamento'].choices = [('', 'Seleccione un departamento')] + [(dept, dept) for dept in departamentos if dept]
        
        # Configurar el queryset para empleados
        self.fields['empleado_especifico'].queryset = Empleado.objects.select_related('user').all()
        self.fields['empleado_especifico'].label_from_instance = lambda obj: f"{obj.user.get_full_name()} - {obj.puesto}"
    
    def clean(self):
        cleaned_data = super().clean()
        tipo_destinatario = cleaned_data.get('tipo_destinatario')
        empleado_especifico = cleaned_data.get('empleado_especifico')
        departamento = cleaned_data.get('departamento')
        
        if tipo_destinatario == 'especifico' and not empleado_especifico:
            raise forms.ValidationError('Debe seleccionar un empleado específico.')
        
        if tipo_destinatario == 'departamento' and not departamento:
            raise forms.ValidationError('Debe seleccionar un departamento.')
        
        return cleaned_data


class BusquedaForm(forms.Form):
    query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Buscar por nombre, DNI o puesto...',
            'class': 'form-control'
        }),
        label='Búsqueda'
    )
    departamento = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Departamento'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Obtener departamentos únicos para el select
        departamentos = Empleado.objects.values_list('departamento', flat=True).distinct()
        choices = [('', 'Todos los departamentos')] + [(dept, dept) for dept in departamentos if dept]
        self.fields['departamento'].widget.choices = choices
