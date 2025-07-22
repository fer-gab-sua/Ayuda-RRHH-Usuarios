from django import forms
from django.core.exceptions import ValidationError
from .models import Documento, TipoDocumento, Inasistencia
import os


class DocumentoForm(forms.ModelForm):
    """Formulario para subir documentos"""
    
    class Meta:
        model = Documento
        fields = ['tipo_documento', 'titulo', 'descripcion', 'archivo', 'fecha_desde', 'fecha_hasta']
        widgets = {
            'tipo_documento': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título descriptivo del documento',
                'required': True
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción opcional del documento (motivo, detalles, etc.)'
            }),
            'archivo': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx',
                'required': True
            }),
            'fecha_desde': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'Fecha desde (opcional)'
            }),
            'fecha_hasta': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'Fecha hasta (opcional)'
            }),
        }
        labels = {
            'tipo_documento': 'Tipo de Documento',
            'titulo': 'Título',
            'descripcion': 'Descripción',
            'archivo': 'Archivo',
            'fecha_desde': 'Válido desde',
            'fecha_hasta': 'Válido hasta',
        }
        help_texts = {
            'tipo_documento': 'Selecciona el tipo de documento que estás subiendo',
            'titulo': 'Ingresa un título descriptivo para identificar fácilmente el documento',
            'descripcion': 'Proporciona detalles adicionales si es necesario',
            'archivo': 'Archivos permitidos: PDF, imágenes (JPG, PNG), documentos de Word',
            'fecha_desde': 'Fecha desde la cual es válido el documento (opcional)',
            'fecha_hasta': 'Fecha hasta la cual es válido el documento (opcional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo tipos de documentos activos
        self.fields['tipo_documento'].queryset = TipoDocumento.objects.filter(activo=True)

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            # Verificar tamaño del archivo (máximo 10MB)
            if archivo.size > 10 * 1024 * 1024:
                raise ValidationError('El archivo no puede ser mayor a 10MB.')
            
            # Verificar extensión del archivo
            ext = os.path.splitext(archivo.name)[1].lower()
            extensiones_permitidas = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
            if ext not in extensiones_permitidas:
                raise ValidationError(f'Extensión no permitida. Extensiones válidas: {", ".join(extensiones_permitidas)}')
        
        return archivo

    def clean(self):
        cleaned_data = super().clean()
        fecha_desde = cleaned_data.get('fecha_desde')
        fecha_hasta = cleaned_data.get('fecha_hasta')

        if fecha_desde and fecha_hasta:
            if fecha_desde > fecha_hasta:
                raise ValidationError('La fecha "desde" no puede ser posterior a la fecha "hasta".')

        return cleaned_data


class JustificarInasistenciaForm(forms.ModelForm):
    """Formulario para justificar una inasistencia con un documento"""
    
    inasistencia = forms.ModelChoiceField(
        queryset=Inasistencia.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Inasistencia a Justificar',
        help_text='Selecciona la inasistencia que deseas justificar con este documento'
    )
    
    class Meta:
        model = Documento
        fields = ['inasistencia', 'tipo_documento', 'titulo', 'descripcion', 'archivo']
        widgets = {
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del documento justificativo'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del documento'
            }),
            'archivo': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'
            }),
        }

    def __init__(self, empleado=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empleado:
            # Mostrar solo inasistencias del empleado que pueden ser justificadas
            self.fields['inasistencia'].queryset = Inasistencia.objects.filter(
                empleado=empleado,
                estado='pendiente'
            ).order_by('-fecha_desde')
        
        # Filtrar tipos de documento activos
        self.fields['tipo_documento'].queryset = TipoDocumento.objects.filter(activo=True)


class FiltroDocumentosForm(forms.Form):
    """Formulario para filtrar documentos"""
    
    ESTADO_CHOICES = [
        ('', 'Todos los estados'),
        ('pendiente', 'Pendientes'),
        ('aprobado', 'Aprobados'),
        ('rechazado', 'Rechazados'),
        ('requiere_aclaracion', 'Requieren Aclaración'),
    ]
    
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    tipo_documento = forms.ModelChoiceField(
        queryset=TipoDocumento.objects.filter(activo=True),
        required=False,
        empty_label="Todos los tipos",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
