import zipfile
import io
import shutil
import requests
import tempfile
from pathlib import Path
from django.conf import settings

def copy_front(payload, rollback: bool = False):
    pass

def install_requirements(payload, rollback: bool = False):
    pass

def run_migrations(payload, rollback: bool = False):
    pass

def restart_server(payload, rollback: bool = False):
    pass

def check_reno_dependencies(payload, rollback: bool = False):
    pass

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
    pass

class Appman:
    pipeline = [
        check_reno_dependencies,
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