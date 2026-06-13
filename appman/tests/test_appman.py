import pytest
import zipfile
import io
import requests
from unittest.mock import patch, MagicMock, call
from pathlib import Path
from django.conf import settings

from appman.appman import Appman, generate_app, install_requirements, run_post_install_tasks
from appman.payload import InstallAppPayload
from appman.utils import DummyInstallRequirements
from appman.exceptions import RequirementsException

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
    
    generate_app(payload)
    
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
    
    generate_app(payload)
    app_dir = fake_apps_dir / "test_app"
    assert app_dir.exists()
    generate_app(payload, rollback=True)
    
    
def test_install_requirements_success(fake_apps_dir):
    """
    Tests that install_requirements uses the injected installer correctly
    when requirements.txt is present.
    """
    payload = InstallAppPayload(
        app="test_app",
        dependencies=[],
        tasks=[],
        path="http://fake-registry.com"
    )
    
    app_dir = fake_apps_dir / "test_app"
    app_dir.mkdir()
    (app_dir / "requirements.txt").write_text("requests==2.31.0")
    
    dummy_installer = DummyInstallRequirements(payload)
    
    install_requirements(payload, installer=dummy_installer)

def test_install_requirements_missing_file(fake_apps_dir):
    """
    Tests that install_requirements raises RequirementsException 
    if requirements.txt is missing when using the dummy installer.
    """
    payload = InstallAppPayload(
        app="test_app",
        dependencies=[],
        tasks=[],
        path="http://fake-registry.com"
    )
    
    app_dir = fake_apps_dir / "test_app"
    app_dir.mkdir()
    
    dummy_installer = DummyInstallRequirements(payload)
    
    with pytest.raises(RequirementsException, match="Requirements file not found"):
        install_requirements(payload, installer=dummy_installer)

def test_run_post_install_tasks_success():
    """
    Tests that post-install tasks are executed in the defined order.
    """
    payload = InstallAppPayload(
        app="test_app",
        path="",
        post_install_tasks=["task_a", "task_b"]
    )
    
    
    with patch("appman.appman.importlib.import_module") as mock_import:
        # Create a mock module that has attributes "task_a" and "task_b"
        mock_module = MagicMock()
        mock_func_a = MagicMock()
        mock_func_b = MagicMock()
        
        setattr(mock_module, "task_a", mock_func_a)
        setattr(mock_module, "task_b", mock_func_b)
        mock_import.return_value = mock_module
        
        run_post_install_tasks(payload, rollback=False)
        
        assert mock_import.call_count == 2
        mock_import.assert_called_with("apps.test_app.install_scripts")
        
        mock_func_a.assert_called_once_with(payload=payload, rollback=False)
        mock_func_b.assert_called_once_with(payload=payload, rollback=False)

def test_run_post_install_tasks_rollback_order():
    """
    Tests that post-install tasks are executed in reverse (LIFO) order during a rollback.
    """
    payload = InstallAppPayload(
        app="test_app",
        path="",
        post_install_tasks=["task_a", "task_b"]
    )
    
    with patch("appman.appman.importlib.import_module") as mock_import:
        mock_module = MagicMock()
        manager = MagicMock()
        
        setattr(mock_module, "task_a", manager.task_a)
        setattr(mock_module, "task_b", manager.task_b)
        mock_import.return_value = mock_module
        
        run_post_install_tasks(payload, rollback=True)
        
        expected_calls = [
            call.task_b(payload=payload, rollback=True),
            call.task_a(payload=payload, rollback=True)
        ]
        assert manager.mock_calls == expected_calls

def test_run_post_install_tasks_missing_script():
    """
    Tests that a clear RuntimeError is raised if the script or function is missing.
    """
    payload = InstallAppPayload(
        app="test_app",
        path="",
        post_install_tasks=["missing_task"]
    )
    
    with patch("appman.appman.importlib.import_module", side_effect=ImportError("No module named 'apps.test_app.install_scripts'")):
        with pytest.raises(RuntimeError, match="Failed to load post-install task 'missing_task' for app 'test_app'"):
            run_post_install_tasks(payload)
