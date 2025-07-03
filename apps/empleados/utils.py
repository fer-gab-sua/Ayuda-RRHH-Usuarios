from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.conf import settings
from django.utils import timezone
from io import BytesIO
import os
from PIL import Image as PILImage

def generar_pdf_declaracion_domicilio(solicitud, empleado, incluir_firma=True):
    """
    Genera un PDF con la declaración jurada de cambio de domicilio
    incluir_firma: Si es False, genera preview sin firma. Si es True, incluye la firma digital.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=20,
        alignment=TA_LEFT,
        textColor=colors.darkblue
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=12,
        alignment=TA_LEFT
    )
    
    # Contenido del documento
    story = []
    
    # Encabezado
    story.append(Paragraph("DECLARACIÓN JURADA", title_style))
    story.append(Paragraph("CAMBIO DE DOMICILIO", title_style))
    story.append(Spacer(1, 20))
    
    # Información del empleado
    story.append(Paragraph("DATOS DEL EMPLEADO", subtitle_style))
    
    datos_empleado = [
        ['Nombre completo:', empleado.user.get_full_name()],
        ['Legajo:', empleado.legajo],
        ['DNI:', empleado.dni],
        ['CUIL:', empleado.cuil or 'No especificado'],
        ['Fecha de solicitud:', solicitud.fecha_solicitud.strftime('%d/%m/%Y %H:%M')],
        ['Número de solicitud:', f"DOM-{solicitud.id}"],
    ]
    
    table_empleado = Table(datos_empleado, colWidths=[2*inch, 4*inch])
    table_empleado.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table_empleado)
    story.append(Spacer(1, 20))
    
    # Domicilio actual
    story.append(Paragraph("DOMICILIO ACTUAL", subtitle_style))
    
    domicilio_actual = solicitud.datos_antiguos
    if domicilio_actual:
        datos_actual = [
            ['Calle:', domicilio_actual.get('calle', 'No especificado')],
            ['Número:', domicilio_actual.get('numero', 'No especificado')],
            ['Piso:', domicilio_actual.get('piso', 'No especificado')],
            ['Departamento:', domicilio_actual.get('depto', 'No especificado')],
            ['Barrio:', domicilio_actual.get('barrio', 'No especificado')],
            ['Localidad:', domicilio_actual.get('localidad', 'No especificado')],
            ['Provincia:', domicilio_actual.get('provincia', 'No especificado')],
            ['Código Postal:', domicilio_actual.get('codigo_postal', 'No especificado')],
        ]
    else:
        datos_actual = [['Sin domicilio registrado', '']]
    
    table_actual = Table(datos_actual, colWidths=[2*inch, 4*inch])
    table_actual.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table_actual)
    story.append(Spacer(1, 20))
    
    # Nuevo domicilio
    story.append(Paragraph("NUEVO DOMICILIO SOLICITADO", subtitle_style))
    
    domicilio_nuevo = solicitud.datos_nuevos
    datos_nuevo = [
        ['Calle:', domicilio_nuevo.get('calle', 'No especificado')],
        ['Número:', domicilio_nuevo.get('numero', 'No especificado')],
        ['Piso:', domicilio_nuevo.get('piso', 'No especificado')],
        ['Departamento:', domicilio_nuevo.get('depto', 'No especificado')],
        ['Barrio:', domicilio_nuevo.get('barrio', 'No especificado')],
        ['Localidad:', domicilio_nuevo.get('localidad', 'No especificado')],
        ['Provincia:', domicilio_nuevo.get('provincia', 'No especificado')],
        ['Código Postal:', domicilio_nuevo.get('codigo_postal', 'No especificado')],
        ['Entre calles:', domicilio_nuevo.get('entre_calles', 'No especificado')],
        ['Observaciones:', domicilio_nuevo.get('observaciones', 'No especificado')],
    ]
    
    table_nuevo = Table(datos_nuevo, colWidths=[2*inch, 4*inch])
    table_nuevo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table_nuevo)
    story.append(Spacer(1, 30))
    
    # Declaración jurada
    story.append(Paragraph("DECLARACIÓN JURADA", subtitle_style))
    
    declaracion_texto = """
    Yo, <strong>{nombre_completo}</strong>, DNI <strong>{dni}</strong>, declaro bajo juramento que:
    
    1. Los datos proporcionados en esta solicitud son veraces y completos.
    2. Comprendo que la falsedad en esta declaración puede acarrear sanciones disciplinarias.
    3. Autorizo a la empresa a verificar la información proporcionada.
    4. Me comprometo a presentar la documentación respaldatoria que me sea requerida.
    5. Solicito formalmente el cambio de domicilio según los datos consignados.
    
    Esta declaración ha sido firmada digitalmente con mi PIN personal el día {fecha}.
    """.format(
        nombre_completo=empleado.user.get_full_name(),
        dni=empleado.dni,
        fecha=solicitud.fecha_solicitud.strftime('%d de %B de %Y a las %H:%M')
    )
    
    story.append(Paragraph(declaracion_texto, normal_style))
    story.append(Spacer(1, 30))
    
    # Firma digital
    story.append(Paragraph("FIRMA DIGITAL", subtitle_style))
    
    if incluir_firma:
        # Intentar cargar la imagen de la firma
        if empleado.firma_imagen:
            try:
                firma_path = empleado.firma_imagen.path
                if os.path.exists(firma_path):
                    # Verificar que la imagen no sea demasiado grande
                    with PILImage.open(firma_path) as img:
                        width, height = img.size
                        max_width = 200
                        if width > max_width:
                            ratio = max_width / width
                            new_height = int(height * ratio)
                            firma_img = Image(firma_path, width=max_width, height=new_height)
                        else:
                            firma_img = Image(firma_path)
                        
                        story.append(firma_img)
            except Exception as e:
                story.append(Paragraph(f"[Firma digital autenticada con PIN - Error al cargar imagen: {str(e)}]", normal_style))
        else:
            story.append(Paragraph("[Firma digital autenticada con PIN]", normal_style))
        
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"Firmado digitalmente por: {empleado.user.get_full_name()}", normal_style))
        story.append(Paragraph(f"Legajo: {empleado.legajo}", normal_style))
        story.append(Paragraph(f"Fecha: {solicitud.fecha_solicitud.strftime('%d/%m/%Y %H:%M')}", normal_style))
    else:
        # Mostrar espacio para firma (solo preview)
        story.append(Spacer(1, 30))
        
        # Crear un espacio visual para la firma usando una tabla
        firma_data = [
            ['🔒 ESPACIO RESERVADO PARA FIRMA DIGITAL'],
            [''],
            ['⚠️ Este documento se firmará digitalmente tras la confirmación con PIN'],
            ['El empleado deberá ingresar su PIN para aplicar la firma']
        ]
        
        firma_table = Table(firma_data, colWidths=[6*inch], rowHeights=[0.4*inch, 0.6*inch, 0.3*inch, 0.3*inch])
        firma_table.setStyle(TableStyle([
            # Fila del título
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Espacio vacío para firma
            ('BACKGROUND', (0, 1), (-1, 1), colors.white),
            ('GRID', (0, 1), (-1, 1), 1, colors.lightgrey),
            
            # Filas de advertencia
            ('BACKGROUND', (0, 2), (-1, -1), colors.lightyellow),
            ('TEXTCOLOR', (0, 2), (-1, -1), colors.red),
            ('FONTNAME', (0, 2), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 2), (-1, -1), 10),
            ('ALIGN', (0, 2), (-1, -1), 'CENTER'),
            
            # Bordes y padding generales
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(firma_table)
        story.append(Spacer(1, 15))
        
        # Información del empleado
        info_empleado = [
            ['Empleado:', empleado.user.get_full_name()],
            ['Legajo:', empleado.legajo],
            ['Estado:', 'PENDIENTE DE FIRMA DIGITAL']
        ]
        
        info_table = Table(info_empleado, colWidths=[1.5*inch, 4.5*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 2), (1, 2), colors.lightyellow),
            ('TEXTCOLOR', (0, 2), (1, 2), colors.red),
        ]))
        
        story.append(info_table)
    
    # Pie de página
    story.append(Spacer(1, 50))
    story.append(Paragraph("Este documento fue generado automáticamente por el sistema de RRHH", 
                          ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                                       textColor=colors.grey, alignment=TA_CENTER)))
    
    # Construir el PDF
    doc.build(story)
    
    # Obtener el contenido del buffer
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content

def generar_pdf_declaracion_obra_social(solicitud, empleado, incluir_firma=True):
    """
    Genera un PDF con la declaración jurada de cambio de obra social
    incluir_firma: Si es False, genera preview sin firma. Si es True, incluye la firma digital.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=20,
        alignment=TA_LEFT,
        textColor=colors.darkblue
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=12,
        alignment=TA_LEFT
    )
    
    # Contenido del documento
    story = []
    
    # Encabezado
    story.append(Paragraph("DECLARACIÓN JURADA", title_style))
    story.append(Paragraph("CAMBIO DE OBRA SOCIAL", title_style))
    story.append(Spacer(1, 20))
    
    # Información del empleado
    story.append(Paragraph("DATOS DEL EMPLEADO", subtitle_style))
    
    datos_empleado = [
        ['Nombre completo:', empleado.user.get_full_name()],
        ['Legajo:', empleado.legajo],
        ['DNI:', empleado.dni],
        ['CUIL:', empleado.cuil or 'No especificado'],
        ['Fecha de solicitud:', solicitud.fecha_solicitud.strftime('%d/%m/%Y %H:%M')],
        ['Número de solicitud:', f"OS-{solicitud.id}"],
    ]
    
    table_empleado = Table(datos_empleado, colWidths=[2*inch, 4*inch])
    table_empleado.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table_empleado)
    story.append(Spacer(1, 20))
    
    # Obra social actual
    story.append(Paragraph("OBRA SOCIAL ACTUAL", subtitle_style))
    
    obra_social_actual = solicitud.datos_antiguos
    if obra_social_actual:
        datos_actual = [
            ['Nombre:', obra_social_actual.get('nombre', 'No especificado')],
            ['Fecha de alta:', obra_social_actual.get('fecha_alta', 'No especificado')],
            ['Observaciones:', obra_social_actual.get('observaciones', 'No especificado')],
        ]
    else:
        datos_actual = [['Sin obra social registrada', '']]
    
    table_actual = Table(datos_actual, colWidths=[2*inch, 4*inch])
    table_actual.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table_actual)
    story.append(Spacer(1, 20))
    
    # Nueva obra social
    story.append(Paragraph("NUEVA OBRA SOCIAL SOLICITADA", subtitle_style))
    
    obra_social_nueva = solicitud.datos_nuevos
    datos_nuevo = [
        ['Nombre:', obra_social_nueva.get('nombre', 'No especificado')],
        ['Fecha de alta:', obra_social_nueva.get('fecha_alta', 'No especificado')],
        ['Observaciones:', obra_social_nueva.get('observaciones', 'No especificado')],
    ]
    
    table_nuevo = Table(datos_nuevo, colWidths=[2*inch, 4*inch])
    table_nuevo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table_nuevo)
    story.append(Spacer(1, 20))
    
    # Archivo adjunto (si existe)
    story.append(Paragraph("DOCUMENTACIÓN ADJUNTA", subtitle_style))
    
    # Verificar si hay archivo adjunto
    tiene_archivo = False
    nombre_archivo = "No se adjuntó ningún archivo"
    
    if hasattr(solicitud, 'archivo_adjunto') and solicitud.archivo_adjunto:
        # Caso normal: solicitud guardada en BD o preview con archivo temporal
        tiene_archivo = True
        if hasattr(solicitud.archivo_adjunto, 'name'):
            nombre_archivo = solicitud.archivo_adjunto.name
        else:
            nombre_archivo = "Archivo adjunto"
    
    if tiene_archivo:
        datos_archivo = [
            ['Archivo adjunto:', nombre_archivo],
            ['Estado:', 'Archivo PDF adjuntado por el empleado'],
            ['Nota:', 'RRHH puede acceder al archivo adjunto para su revisión']
        ]
        color_fondo = colors.lightgreen
        mensaje_adicional = "✓ El empleado ha adjuntado documentación complementaria"
    else:
        datos_archivo = [
            ['Archivo adjunto:', 'No se adjuntó ningún archivo'],
            ['Estado:', 'Solicitud sin documentación complementaria'],
            ['Nota:', 'El empleado optó por no adjuntar documentación adicional']
        ]
        color_fondo = colors.lightgrey
        mensaje_adicional = "ℹ️ El empleado no adjuntó documentación complementaria"
    
    table_archivo = Table(datos_archivo, colWidths=[2*inch, 4*inch])
    table_archivo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), color_fondo),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table_archivo)
    story.append(Spacer(1, 10))
    story.append(Paragraph(mensaje_adicional, 
                          ParagraphStyle('ArchivoInfo', parent=styles['Normal'], fontSize=9, 
                                       textColor=colors.blue, alignment=TA_LEFT, 
                                       leftIndent=20, spaceAfter=20)))
    story.append(Spacer(1, 20))
    
    # Declaración jurada
    story.append(Paragraph("DECLARACIÓN JURADA", subtitle_style))
    
    declaracion_texto = """
    Yo, <strong>{nombre_completo}</strong>, DNI <strong>{dni}</strong>, declaro bajo juramento que:
    
    1. Los datos proporcionados en esta solicitud son veraces y completos.
    2. Comprendo que la falsedad en esta declaración puede acarrear sanciones disciplinarias.
    3. Autorizo a la empresa a verificar la información proporcionada.
    4. Me comprometo a presentar la documentación respaldatoria que me sea requerida.
    5. Solicito formalmente el cambio de obra social según los datos consignados.
    
    Esta declaración ha sido firmada digitalmente con mi PIN personal el día {fecha}.
    """.format(
        nombre_completo=empleado.user.get_full_name(),
        dni=empleado.dni,
        fecha=solicitud.fecha_solicitud.strftime('%d de %B de %Y a las %H:%M')
    )
    
    story.append(Paragraph(declaracion_texto, normal_style))
    story.append(Spacer(1, 30))
    
    # Firma digital
    story.append(Paragraph("FIRMA DIGITAL", subtitle_style))
    
    if incluir_firma:
        # Intentar cargar la imagen de la firma
        if empleado.firma_imagen:
            try:
                firma_path = empleado.firma_imagen.path
                if os.path.exists(firma_path):
                    # Verificar que la imagen no sea demasiado grande
                    with PILImage.open(firma_path) as img:
                        width, height = img.size
                        max_width = 200
                        if width > max_width:
                            ratio = max_width / width
                            new_height = int(height * ratio)
                            firma_img = Image(firma_path, width=max_width, height=new_height)
                        else:
                            firma_img = Image(firma_path)
                        
                        story.append(firma_img)
            except Exception as e:
                story.append(Paragraph(f"[Firma digital autenticada con PIN - Error al cargar imagen: {str(e)}]", normal_style))
        else:
            story.append(Paragraph("[Firma digital autenticada con PIN]", normal_style))
        
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"Firmado digitalmente por: {empleado.user.get_full_name()}", normal_style))
        story.append(Paragraph(f"Legajo: {empleado.legajo}", normal_style))
        story.append(Paragraph(f"Fecha: {solicitud.fecha_solicitud.strftime('%d/%m/%Y %H:%M')}", normal_style))
    else:
        # Mostrar espacio para firma (solo preview)
        story.append(Spacer(1, 30))
        
        # Crear un espacio visual para la firma usando una tabla
        firma_data = [
            ['🔒 ESPACIO RESERVADO PARA FIRMA DIGITAL'],
            [''],
            ['⚠️ Este documento se firmará digitalmente tras la confirmación con PIN'],
            ['El empleado deberá ingresar su PIN para aplicar la firma']
        ]
        
        firma_table = Table(firma_data, colWidths=[6*inch], rowHeights=[0.4*inch, 0.6*inch, 0.3*inch, 0.3*inch])
        firma_table.setStyle(TableStyle([
            # Fila del título
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Espacio vacío para firma
            ('BACKGROUND', (0, 1), (-1, 1), colors.white),
            ('GRID', (0, 1), (-1, 1), 1, colors.lightgrey),
            
            # Filas de advertencia
            ('BACKGROUND', (0, 2), (-1, -1), colors.lightyellow),
            ('TEXTCOLOR', (0, 2), (-1, -1), colors.red),
            ('FONTNAME', (0, 2), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 2), (-1, -1), 10),
            ('ALIGN', (0, 2), (-1, -1), 'CENTER'),
            
            # Bordes y padding generales
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(firma_table)
        story.append(Spacer(1, 15))
        
        # Información del empleado
        info_empleado = [
            ['Empleado:', empleado.user.get_full_name()],
            ['Legajo:', empleado.legajo],
            ['Estado:', 'PENDIENTE DE FIRMA DIGITAL']
        ]
        
        info_table = Table(info_empleado, colWidths=[1.5*inch, 4.5*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 2), (1, 2), colors.lightyellow),
            ('TEXTCOLOR', (0, 2), (1, 2), colors.red),
        ]))
        
        story.append(info_table)
    
    # Pie de página
    story.append(Spacer(1, 50))
    story.append(Paragraph("Este documento fue generado automáticamente por el sistema de RRHH", 
                          ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                                       textColor=colors.grey, alignment=TA_CENTER)))
    
    # Construir el PDF
    doc.build(story)
    
    # Obtener el contenido del buffer
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content
