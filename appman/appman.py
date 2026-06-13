import os
import importlib
import subprocess
import zipfile
import io
import shutil
import requests
import tempfile
from pathlib import Path
from django.conf import settings
from django.core.management import call_command
from .utils import BaseInstaller, InstallRequirements


def copy_front(payload, rollback: bool = False):
    """
    Extracts the frontend components from the installed app and copies them 
    to the central frontend workspace (e.g., for Vite/React compilation).
    
    Args:
        payload (InstallAppPayload): The manifest payload containing the app's metadata.
        rollback (bool, optional): If True, triggers the rollback mechanism to delete the copied files.
    """
    base_dir = getattr(settings, 'BASE_DIR', Path(__file__).resolve().parent.parent)
    apps_dir = Path(getattr(settings, 'APPS_DIR', base_dir / "apps"))
    
    frontend_app_fallback = base_dir / "frontend" / "apps" 
    frontend_apps_path = Path(getattr(settings, 'FRONTEND_APPS_DIR', frontend_app_fallback))
    
    app_source_frontend = apps_dir / payload.app / "frontend"
    app_dest_frontend = frontend_apps_path / payload.app

    if rollback:
        if app_dest_frontend.exists():
            shutil.rmtree(app_dest_frontend)
        return

    if not app_source_frontend.exists() or not app_source_frontend.is_dir():
        return

    if not frontend_apps_path.exists():
        frontend_apps_path.mkdir(parents=True, exist_ok=True)
        
    if app_dest_frontend.exists():
        shutil.rmtree(app_dest_frontend)

    # Copy from the app's folder (source) to the central frontend workspace (destination)
    shutil.copytree(app_source_frontend, app_dest_frontend)
    

def install_requirements(payload, installer: BaseInstaller = None, rollback: bool = False):
    if installer is None:
        installer = InstallRequirements(payload)
        
    if rollback:
        installer.run_rollback()
    else:
        installer.run_install()

def run_migrations(payload, rollback: bool = False):
    """
    Executes or reverses database migrations for the installed application.
    
    In a standard run, it generates new migration files (if models exist) and applies them.
    In a rollback run, it reverts the app's migrations back to the 'zero' state.
    
    Args:
        payload (InstallAppPayload): The manifest payload containing the app's metadata.
        rollback (bool, optional): If True, triggers the rollback to revert migrations.
    """
    if rollback:
        call_command('migrate', payload.app, 'zero')
    else:
        call_command('makemigrations', payload.app)
        call_command('migrate', payload.app)

def restart_server(payload, rollback: bool = False):
    """
    Triggers a graceful reload of the server.
    In development, Django's auto-reloader handles this automatically.
    For production, touching the wsgi.py file triggers a reload in Gunicorn/uWSGI.
    """
    base_dir = getattr(settings, 'BASE_DIR', Path(__file__).resolve().parent.parent)
    wsgi_file = base_dir / "reno" / "wsgi.py"
    
    print("Triggering server reload...")
    if wsgi_file.exists():
        os.utime(wsgi_file, None)
        print("Server reload triggered (wsgi.py touched).")
    else:
        print("Development environment detected. Auto-reloader will handle the restart.")

def generate_app(payload, rollback: bool = False):
    """
    Downloads and extracts a RenoApp module into the designated apps directory,
    or completely removes the directory if rolling back.

    Args:
        payload (InstallAppPayload): The manifest payload containing the app's metadata and remote path.
        rollback (bool, optional): If True, triggers the rollback mechanism to delete the app directory. Defaults to False.

    Raises:
        requests.exceptions.HTTPError: If the remote download request fails.
        zipfile.BadZipFile: If the downloaded content is not a valid ZIP archive.
    """
    base_dir = getattr(settings, 'BASE_DIR', Path(__file__).resolve().parent.parent)
    apps_dir = Path(getattr(settings, 'APPS_DIR', base_dir / "apps"))
    app_dir = apps_dir / payload.app
    
    if rollback:
        if app_dir.exists():
            shutil.rmtree(app_dir)
        return
        
    response = requests.get(payload.path, stream=True)
    response.raise_for_status()
    
    with tempfile.TemporaryFile() as temp_file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                temp_file.write(chunk)
                
        # Rewind the file pointer to the beginning before extraction
        temp_file.seek(0)
        
        with zipfile.ZipFile(temp_file) as z:
            z.extractall(app_dir)

def update_settings(payload, rollback: bool = False):
    pass
    

def run_post_install_tasks(payload, rollback: bool = False):
    """
    Executes custom post-installation scripts defined by the application.
    
    The application must provide a Python module in `apps/<app_name>/install_scripts/<task_name>.py`
    containing a function named `<task_name>(payload, rollback)`.
    
    Args:
        payload (InstallAppPayload): The manifest payload containing the app's metadata.
        rollback (bool, optional): If True, triggers the scripts in reverse order to undo changes.
    """
    if not payload.post_install_tasks:
        return

    # In a rollback scenario, tasks should be undone in LIFO order (reverse)
    tasks_to_run = reversed(payload.post_install_tasks) if rollback else payload.post_install_tasks

    for task in tasks_to_run:
        try:
            install_script_module = importlib.import_module(f"apps.{payload.app}.install_scripts")
            task_func = getattr(install_script_module, task)
            task_func(payload=payload, rollback=rollback)
        except (ImportError, AttributeError) as e:
            raise RuntimeError(f"Failed to load post-install task '{task}' for app '{payload.app}'. "
                               f"Ensure apps/{payload.app}/install_scripts/{task}.py defines a function named '{task}'. Error: {str(e)}")

class Appman:
    pipeline = [
        generate_app,
        update_settings,
        install_requirements,
        copy_front,
        run_migrations,
        run_post_install_tasks,
        restart_server,
    ]

    stack = [

    ]

    def __init__(self, payload: "InstallAppPayload"):
        self.payload = payload

    def add_task(self, task):
        self.pipeline.append(task)
    
    def execute(self):
        for task in self.pipeline:
            task(self.payload)
            self.stack.append(task)

    def rollback(self):
        while self.stack:
            task = self.stack.pop()
            task(self.payload, rollback=True)

    def get_payload(self):
        return self.payload