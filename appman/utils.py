import os
import io
import json
import shutil
import zipfile
import logging
import tempfile
import subprocess
from pathlib import Path
from django.conf import settings
from .exceptions import RequirementsException
from .payload import InstallAppPayload

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


class Fetcher:
    def __init__(self, payload, metadata_path: str = None):
        self.payload = payload
        self.metadata_path = f"{self.payload.path}"
        self.metadata_path = metadata_path


    def get_metadata(self) -> "InstallAppPayload":
        with open(self.metadata_path, "r") as f:
            metadata = json.load(f)
            return InstallAppPayload.from_dict(metadata)



class DictFetcher(Fetcher):
    def get_metadata(self) -> "InstallAppPayload":
        return InstallAppPayload.from_dict(self.payload.to_dict())


class UrlFetcher(Fetcher):
    def get_metadata(self) -> "InstallAppPayload":
        import requests

        response = requests.get(self.payload.path)
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch app metadata from {self.payload.path}")
        metadata = response.json()
        return InstallAppPayload.from_dict(metadata)    


class LocalFetcher(Fetcher):
    def get_metadata(self) -> "InstallAppPayload":
        pass



class Downloader:
    def __init__(self, payload, metadata_path: str = None):
        self.payload = payload
        self.metadata_path = metadata_path

    def get_zip_file(self) -> str:
        raise NotImplementedError

    def raise_for_status(self):
        raise NotImplementedError



class UrlDownloader(Downloader):
    def raise_for_status(self):
        pass

    def get_zip_file(self) -> str:
        import requests
        
        response = requests.get(self.payload.path, stream=True)
        response.raise_for_status()
        with tempfile.TemporaryFile() as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_file.seek(0)
            return temp_file

class MemoryDownloader(Downloader):
    def get_zip_file(self) -> str:
        return self.payload.path
    


class LocalPathDownloader(Downloader):
    def is_valid_path(self, path):
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Path {path} does not exist")
        return path

    def raise_for_status(self):
        pass

    def get_zip_file(self) -> io.BytesIO:
        path = self.is_valid_path(self.metadata_path)
        
        if path.is_file() and zipfile.is_zipfile(path):
            with open(path, "rb") as f:
                return io.BytesIO(f.read())
                
        elif path.is_dir():
            memory_zip = io.BytesIO()
            with zipfile.ZipFile(memory_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(path):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(path)
                        zipf.write(file_path, arcname)
            
            memory_zip.seek(0)
            return memory_zip
            
        else:
            raise ValueError(f"Path {path} is neither a valid zip file nor a directory.")