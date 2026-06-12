import os
from django.conf import settings
from django.core.management.commands.startapp import Command as StartAppCommand
from django.core.management.base import CommandError

class Command(StartAppCommand):
    help = "Crea una app de Django extendida con carpetas personalizadas."
    
        
    def handle(self, **options):
        # 1. Ejecutar el comportamiento original de Django (crea la app)
        options.update({
            'directory': settings.BASE_DIR / 'apps' / options.get('name'),
            "template": str(settings.BASE_DIR / 'core' / 'app_template')
        })
        options['extensions'].extend(['json-tpl', 'json'])
        
        super().handle(**options)
        
        # 2. Obtener los argumentos que el usuario escribió
        app_name = options.get('name')
        target = options.get('directory')
        
        print(f"App '{app_name}' creada. Ahora extendiendo con funcionalidades personalizadas {target}...")
        # Determinar la ruta física donde se creó la app
        if target is None:
            app_dir = os.path.join(os.getcwd(), app_name)
        else:
            app_dir = os.path.abspath(target)

        # 3. Inyectar tu comportamiento personalizado
        try:
            # Ejemplo: Crear una carpeta extra llamada 'services'
            services_dir = os.path.join(app_dir, 'services')
            os.makedirs(services_dir, exist_ok=True)
            
            # Crear un archivo __init__.py dentro de ella
            with open(os.path.join(services_dir, '__init__.py'), 'w') as f:
                f.write("# Capa de servicios de la aplicación\n")
                
            # Mensaje de éxito en la consola
            self.stdout.write(
                self.style.SUCCESS(f"¡Éxito! App '{app_name}' creada y extendida con la carpeta /services.")
            )
            
        except Exception as e:
            raise CommandError(f"No se pudo extender la app: {e}")
