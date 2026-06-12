import logging
import subprocess
from pathlib import Path
from django.conf import settings
from .exceptions import RequirementsException

class BaseInstaller:
    """
    Base Strategy class for executing Appman pipeline tasks.
    """
    def __init__(self, payload):
        self.payload = payload
        base_dir = getattr(settings, 'BASE_DIR', Path(__file__).resolve().parent.parent)
        apps_dir = Path(getattr(settings, 'APPS_DIR', base_dir / "apps"))
        self.path = apps_dir / self.payload.app
        self.log = logging.getLogger("django.server")

    def run_install(self):
        """Executes the installation logic for this step."""
        raise NotImplementedError

    def run_rollback(self):
        """Executes the rollback logic to revert this step."""
        raise NotImplementedError

    def info(self, message):
        self.log.info(f"[{self.payload.app}] {message}")

    def error(self, message):
        self.log.error(f"[{self.payload.app}] {message}")

class InstallRequirements(BaseInstaller):
    def run_install(self):
        req_file = self.path / "requirements.txt"
        if not req_file.exists():
            self.info("No requirements.txt found, skipping.")
            return

        # Using uv pip for highly concurrent and fast installations
        popen = subprocess.Popen(
            ["uv", "pip", "install", "-r", str(req_file)], 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = popen.communicate()

        if popen.returncode != 0:
            self.error(f"Error installing requirements: {stderr}")
            raise RequirementsException(f"Error installing requirements: {stderr}")

        self.info("Requirements installed successfully")
    
    def run_rollback(self):
        self.info("Rolling back requirements (No-op by default)...")

class DummyInstallRequirements(BaseInstaller):
    def run_install(self):
        req_file = self.path / "requirements.txt"
        if not req_file.exists():
            self.error(f"Requirements file not found at {self.path}")
            raise RequirementsException("Requirements file not found")
            
        print(f"Installing requirements from {req_file}...")
    
    def run_rollback(self):
        print(f"Rolling back requirements from {self.path}...")