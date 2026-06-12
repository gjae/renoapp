import pytest
import zipfile
import io
import requests
from unittest.mock import patch, MagicMock
from pathlib import Path
from django.conf import settings

from appman.appman import Appman, generate_app
from appman.payload import InstallAppPayload

@pytest.fixture
def fake_zip_bytes():
    """
    Creates an in-memory ZIP file representing an app structure.
    Returns the raw bytes of the zip.
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("__init__.py", "")
        z.writestr("__app__.json", '{"name": "test_app"}')
        z.writestr("views.py", "def index(request):\n    pass\n")
    return zip_buffer.getvalue()

@pytest.fixture
def fake_apps_dir(tmp_path, settings):
    """
    Redirects Django's APPS_DIR to a temporary pytest directory.
    Returns the path to the temporary apps directory.
    """
    apps_dir = tmp_path / "apps"
    apps_dir.mkdir()
    settings.APPS_DIR = apps_dir
    return apps_dir

@pytest.fixture
def mock_requests_get(fake_zip_bytes):
    """
    Mocks requests.get to return a successful response containing fake_zip_bytes via iter_content.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Simulate the generator behavior of iter_content yielding chunks
    mock_response.iter_content.return_value = [fake_zip_bytes]
    mock_response.raise_for_status.return_value = None

    with patch('appman.appman.requests.get', return_value=mock_response) as mock_get:
        yield mock_get

def test_generate_app_success(fake_apps_dir, mock_requests_get):
    """
    Tests that generate_app correctly downloads (mocks) and extracts 
    the zip file into the designated APPS_DIR.
    """
    payload = InstallAppPayload(
        app="test_app",
        dependencies=[],
        tasks=[],
        path="http://fake-registry.com/test_app/download"
    )
    
    # Execute the phase directly
    generate_app(payload)
    
    # Verify extraction
    app_dir = fake_apps_dir / "test_app"
    assert app_dir.exists(), "The app directory was not created."
    assert (app_dir / "__init__.py").exists()
    assert (app_dir / "__app__.json").exists()
    assert (app_dir / "views.py").read_text() == "def index(request):\n    pass\n"

def test_generate_app_rollback(fake_apps_dir, mock_requests_get):
    """
    Tests that generate_app with rollback=True correctly deletes the extracted app directory.
    """
    payload = InstallAppPayload(
        app="test_app",
        dependencies=[],
        tasks=[],
        path="http://fake-registry.com/test_app/download"
    )
    
    # First install it
    generate_app(payload)
    app_dir = fake_apps_dir / "test_app"
    assert app_dir.exists()
    
    # Then trigger rollback
    generate_app(payload, rollback=True)
    
    # Verify deletion
    assert not app_dir.exists(), "The app directory was not deleted during rollback."
