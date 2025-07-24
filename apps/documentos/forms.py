from django import forms
from django.core.exceptions import ValidationError
from .models import Documento, TipoDocumento, Inasistencia
from apps.empleados.models import Empleado
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
        fields = ['inasistencia', 'tipo_documento', 'titulo', 'descripcion', 'archivo', 'fecha_desde', 'fecha_hasta']
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
            'fecha_desde': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'fecha_hasta': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
        }
        labels = {
            'inasistencia': 'Inasistencia a Justificar',
            'tipo_documento': 'Tipo de Documento',
            'titulo': 'Título',
            'descripcion': 'Descripción',
            'archivo': 'Archivo',
            'fecha_desde': 'Justificar desde',
            'fecha_hasta': 'Justificar hasta',
        }
        help_texts = {
            'fecha_desde': 'Fecha desde la cual el documento justifica la inasistencia',
            'fecha_hasta': 'Fecha hasta la cual el documento justifica la inasistencia',
        }

    def __init__(self, empleado=None, inasistencia_especifica=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if empleado:
            # Mostrar solo inasistencias del empleado que pueden ser justificadas
            self.fields['inasistencia'].queryset = Inasistencia.objects.filter(
                empleado=empleado,
                estado__in=['injustificada', 'pendiente']
            ).order_by('-fecha_desde')
            
            # Si hay una inasistencia específica, pre-seleccionarla y ocultarla
            if inasistencia_especifica:
                self.fields['inasistencia'].initial = inasistencia_especifica
                self.fields['inasistencia'].widget = forms.HiddenInput()
                self.fields['inasistencia'].queryset = Inasistencia.objects.filter(id=inasistencia_especifica.id)
                
                # Pre-llenar las fechas con el rango completo de la inasistencia
                self.fields['fecha_desde'].initial = inasistencia_especifica.fecha_desde
                self.fields['fecha_hasta'].initial = inasistencia_especifica.fecha_hasta
        
        # Filtrar tipos de documento activos
        self.fields['tipo_documento'].queryset = TipoDocumento.objects.filter(activo=True)

    def clean(self):
        cleaned_data = super().clean()
        inasistencia = cleaned_data.get('inasistencia')
        fecha_desde = cleaned_data.get('fecha_desde')
        fecha_hasta = cleaned_data.get('fecha_hasta')

        if inasistencia and fecha_desde and fecha_hasta:
            # Verificar que las fechas estén dentro del rango de la inasistencia
            if fecha_desde < inasistencia.fecha_desde:
                raise ValidationError(f'La fecha "desde" no puede ser anterior al inicio de la inasistencia ({inasistencia.fecha_desde}).')
            
            if fecha_hasta > inasistencia.fecha_hasta:
                raise ValidationError(f'La fecha "hasta" no puede ser posterior al fin de la inasistencia ({inasistencia.fecha_hasta}).')
            
            if fecha_desde > fecha_hasta:
                raise ValidationError('La fecha "desde" no puede ser posterior a la fecha "hasta".')

        return cleaned_data


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


class CrearInasistenciaForm(forms.ModelForm):
    """Formulario para que RRHH cree inasistencias"""
    
    class Meta:
        model = Inasistencia
        fields = ['empleado', 'fecha_desde', 'fecha_hasta', 'tipo', 'motivo', 'observaciones_rrhh']
        widgets = {
            'empleado': forms.Select(attrs={
                'class': 'form-control empleado-select',
                'required': True,
                'data-placeholder': 'Buscar empleado por nombre o legajo...'
            }),
            'fecha_desde': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'fecha_hasta': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'motivo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del motivo de la inasistencia'
            }),
            'observaciones_rrhh': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones internas de RRHH (opcional)'
            }),
        }
        labels = {
            'empleado': 'Empleado',
            'fecha_desde': 'Fecha Desde',
            'fecha_hasta': 'Fecha Hasta',
            'tipo': 'Tipo de Inasistencia',
            'motivo': 'Motivo/Descripción',
            'observaciones_rrhh': 'Observaciones RRHH',
        }
        help_texts = {
            'empleado': 'Selecciona el empleado al que corresponde la inasistencia',
            'fecha_desde': 'Fecha de inicio de la inasistencia',
            'fecha_hasta': 'Fecha de fin de la inasistencia',
            'tipo': 'Tipo o categoría de la inasistencia',
            'motivo': 'Describe el motivo conocido de la inasistencia',
            'observaciones_rrhh': 'Notas internas para el seguimiento de RRHH',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar empleados por legajo primero, luego por apellido y nombre
        self.fields['empleado'].queryset = Empleado.objects.select_related('user').order_by(
            'legajo', 'user__last_name', 'user__first_name'
        )
        
        # Personalizar las opciones del empleado para mostrar legajo, nombre completo y departamento
        empleado_choices = []
        for emp in self.fields['empleado'].queryset:
            nombre_completo = emp.user.get_full_name()
            departamento = f" - {emp.departamento}" if emp.departamento else ""
            choice_text = f"Legajo {emp.legajo} - {nombre_completo}{departamento}"
            empleado_choices.append((emp.id, choice_text))
        
        self.fields['empleado'].choices = [('', 'Seleccionar empleado...')] + empleado_choices

    def clean(self):
        cleaned_data = super().clean()
        fecha_desde = cleaned_data.get('fecha_desde')
        fecha_hasta = cleaned_data.get('fecha_hasta')

        if fecha_desde and fecha_hasta:
            if fecha_desde > fecha_hasta:
                raise ValidationError('La fecha "desde" no puede ser posterior a la fecha "hasta".')
            
            # Verificar que no sea una fecha muy futura (más de 30 días)
            from datetime import date, timedelta
            fecha_limite = date.today() + timedelta(days=30)
            if fecha_desde > fecha_limite:
                raise ValidationError('No se pueden registrar inasistencias con más de 30 días de anticipación.')

        return cleaned_data
