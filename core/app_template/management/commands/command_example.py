import os
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Descripción básica del comando'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Comando ejecutado exitosamente'))
        self.stdout.write(self.style.SUCCESS( f'Ruta actual: {os.getcwd()}'))
