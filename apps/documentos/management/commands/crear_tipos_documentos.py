from django.core.management.base import BaseCommand
from apps.documentos.models import TipoDocumento


class Command(BaseCommand):
    help = 'Crea tipos de documentos por defecto en el sistema'

    def handle(self, *args, **options):
        tipos_documentos = [
            {
                'nombre': 'Certificado Médico',
                'descripcion': 'Certificados médicos por enfermedad o incapacidad temporal'
            },
            {
                'nombre': 'Certificado de Estudio',
                'descripcion': 'Certificados de instituciones educativas para justificar ausencias por exámenes o trámites académicos'
            },
            {
                'nombre': 'Certificado de Defunción',
                'descripcion': 'Certificados de defunción de familiares directos'
            },
            {
                'nombre': 'Constancia de Matrimonio',
                'descripcion': 'Constancias o actas de matrimonio'
            },
            {
                'nombre': 'Certificado de Nacimiento',
                'descripcion': 'Certificados de nacimiento de hijos'
            },
            {
                'nombre': 'Certificado de Adopción',
                'descripcion': 'Documentos relacionados con procesos de adopción'
            },
            {
                'nombre': 'Constancia Judicial',
                'descripcion': 'Citaciones, comparendas u otras constancias judiciales'
            },
            {
                'nombre': 'Certificado de Donación de Sangre',
                'descripcion': 'Certificados de donación de sangre'
            },
            {
                'nombre': 'Constancia de Mudanza',
                'descripcion': 'Documentos que acrediten mudanza o cambio de domicilio'
            },
            {
                'nombre': 'Certificado de Emergencia Familiar',
                'descripcion': 'Documentos que acrediten emergencias familiares'
            },
            {
                'nombre': 'Otros',
                'descripcion': 'Otros tipos de documentos no contemplados en las categorías anteriores'
            }
        ]

        creados = 0
        for tipo_data in tipos_documentos:
            tipo, created = TipoDocumento.objects.get_or_create(
                nombre=tipo_data['nombre'],
                defaults={'descripcion': tipo_data['descripcion']}
            )
            if created:
                creados += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Tipo de documento creado: {tipo.nombre}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'- Tipo de documento ya existe: {tipo.nombre}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n¡Proceso completado! Se crearon {creados} nuevos tipos de documentos.'
            )
        )
