#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import subprocess
import atexit

def start_frontend_dev_server():
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')
    
    if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'true':
        if os.path.exists(frontend_dir) and os.path.exists(os.path.join(frontend_dir, 'package.json')):
            print("\n[RenoApp] Iniciando el servidor de desarrollo del Frontend (npm run dev)...")
            
            # Run npm proicess as subprocess
            npm_process = subprocess.Popen(
                ['npm', 'run', 'start'],
                cwd=frontend_dir,
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
            
            # Graceful shutdown (Ctrl+C), kill frontend process
            def kill_npm_process():
                npm_process.terminate()
                npm_process.wait()
                
            atexit.register(kill_npm_process)
        else:
            print(f"\n[RenoApp] Advertencia: Se detectó 'runserver', pero no se encontró un entorno Node en '{frontend_dir}' (falta package.json). Omitiendo inicio del frontend.")

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reno.settings')
    
    start_frontend_dev_server()
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
