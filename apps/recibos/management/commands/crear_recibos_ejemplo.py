from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.base import ContentFile
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import random

from apps.empleados.models import Empleado
from apps.recibos.models import ReciboSueldo


class Command(BaseCommand):
    help = 'Crear recibos de sueldo de ejemplo para todos los empleados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--meses',
            type=int,
            default=3,
            help='Número de meses hacia atrás para crear recibos'
        )

    def handle(self, *args, **options):
        meses = options['meses']
        
        # Filtrar solo empleados con datos válidos
        empleados = Empleado.objects.exclude(
            legajo__isnull=True
        ).exclude(
            legajo=''
        ).exclude(
            user__first_name__isnull=True
        ).exclude(
            user__first_name=''
        ).exclude(
            user__last_name__isnull=True
        ).exclude(
            user__last_name=''
        )
        
        total_empleados = Empleado.objects.count()
        empleados_validos = empleados.count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Total empleados en sistema: {total_empleados}\n'
                f'Empleados válidos para recibos: {empleados_validos}'
            )
        )
        
        if not empleados.exists():
            self.stdout.write(
                self.style.ERROR('No hay empleados válidos en el sistema. Verificar datos de empleados.')
            )
            return
        
        # Meses para crear recibos
        periodos = [
            ('enero', 1), ('febrero', 2), ('marzo', 3), ('abril', 4),
            ('mayo', 5), ('junio', 6), ('julio', 7), ('agosto', 8),
            ('septiembre', 9), ('octubre', 10), ('noviembre', 11), ('diciembre', 12)
        ]
        
        mes_actual = datetime.now().month
        anio_actual = datetime.now().year
        
        recibos_creados = 0
        
        for empleado in empleados:
            # Verificación adicional de datos válidos
            if not empleado.legajo or not empleado.legajo.strip():
                self.stdout.write(
                    self.style.WARNING(f'Saltando empleado sin legajo: {empleado.user.get_full_name()}')
                )
                continue
            
            if not empleado.user.first_name or not empleado.user.last_name:
                self.stdout.write(
                    self.style.WARNING(f'Saltando empleado sin nombre completo: {empleado.legajo}')
                )
                continue
            
            self.stdout.write(f'Creando recibos para {empleado.user.get_full_name()} (Legajo: {empleado.legajo})...')
            
            for i in range(meses):
                # Calcular mes y año
                mes_idx = (mes_actual - 1 - i) % 12
                anio = anio_actual if mes_actual - i > 0 else anio_actual - 1
                periodo_nombre, periodo_num = periodos[mes_idx]
                
                # Verificar si ya existe el recibo
                if ReciboSueldo.objects.filter(
                    empleado=empleado,
                    periodo=periodo_nombre,
                    anio=anio
                ).exists():
                    continue
                
                # Generar datos del recibo
                sueldo_bruto = random.randint(150000, 500000)
                descuentos = int(sueldo_bruto * random.uniform(0.15, 0.25))
                sueldo_neto = sueldo_bruto - descuentos
                
                # Fecha de emisión (primer día del mes siguiente)
                if periodo_num == 12:
                    fecha_emision = datetime(anio + 1, 1, 1)
                else:
                    fecha_emision = datetime(anio, periodo_num + 1, 1)
                
                # Fecha de vencimiento (15 días después de emisión)
                fecha_vencimiento = fecha_emision + timedelta(days=15)
                
                # Generar PDF del recibo
                pdf_content = self.generar_pdf_recibo(
                    empleado, periodo_nombre, anio, sueldo_bruto, descuentos, sueldo_neto
                )
                
                # Crear el recibo
                recibo = ReciboSueldo.objects.create(
                    empleado=empleado,
                    periodo=periodo_nombre,
                    anio=anio,
                    fecha_emision=fecha_emision,
                    fecha_vencimiento=fecha_vencimiento,
                    sueldo_bruto=sueldo_bruto,
                    descuentos=descuentos,
                    sueldo_neto=sueldo_neto,
                    estado='pendiente'
                )
                
                # Guardar PDF
                pdf_filename = f"recibo_{periodo_nombre}_{anio}_{empleado.legajo}.pdf"
                recibo.archivo_pdf.save(pdf_filename, ContentFile(pdf_content), save=True)
                
                recibos_creados += 1
                
                # Si es el mes más reciente, algunos recibos ya vencieron
                if i == 0 and random.choice([True, False]):
                    recibo.fecha_vencimiento = timezone.now() - timedelta(days=1)
                    recibo.estado = 'vencido'
                    recibo.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Se crearon {recibos_creados} recibos de sueldo.')
        )

    def generar_pdf_recibo(self, empleado, periodo, anio, bruto, descuentos, neto):
        """Generar PDF del recibo de sueldo"""
        buffer = BytesIO()
        
        # Crear documento PDF
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles = getSampleStyleSheet()
        story = []
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        story.append(Paragraph("RECIBO DE SUELDO", title_style))
        story.append(Spacer(1, 20))
        
        # Información de la empresa
        empresa_info = [
            ['EMPRESA DEMO S.A.', ''],
            ['CUIT: 20-12345678-9', ''],
            ['Dirección: Av. Corrientes 1234, CABA', ''],
        ]
        
        empresa_table = Table(empresa_info, colWidths=[4*inch, 2*inch])
        empresa_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(empresa_table)
        story.append(Spacer(1, 20))
        
        # Información del empleado
        emp_info = [
            ['Empleado:', f"{empleado.user.get_full_name()}"],
            ['Legajo:', empleado.legajo],
            ['DNI:', empleado.dni],
            ['CUIL:', empleado.cuil],
            ['Puesto:', empleado.puesto or 'No especificado'],
            ['Período:', f"{periodo.title()} {anio}"],
        ]
        
        emp_table = Table(emp_info, colWidths=[2*inch, 4*inch])
        emp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(emp_table)
        story.append(Spacer(1, 30))
        
        # Liquidación
        liquidacion_data = [
            ['CONCEPTO', 'HABERES', 'DESCUENTOS'],
            ['Sueldo Básico', f"${bruto:,.2f}", ''],
            ['Aportes Jubilatorios', '', f"${int(bruto * 0.11):,.2f}"],
            ['Obra Social', '', f"${int(bruto * 0.03):,.2f}"],
            ['Otros Descuentos', '', f"${descuentos - int(bruto * 0.14):,.2f}"],
            ['', '', ''],
            ['TOTALES', f"${bruto:,.2f}", f"${descuentos:,.2f}"],
            ['', '', ''],
            ['NETO A COBRAR', f"${neto:,.2f}", ''],
        ]
        
        liquidacion_table = Table(liquidacion_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        liquidacion_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -3), colors.beige),
            ('BACKGROUND', (0, -2), (-1, -1), colors.lightgreen),
            ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ]))
        story.append(liquidacion_table)
        story.append(Spacer(1, 30))
        
        # Pie de página
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        story.append(Paragraph("Este recibo requiere firma digital del empleado para su validez legal.", footer_style))
        
        # Construir PDF
        doc.build(story)
        
        # Obtener contenido del buffer
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
