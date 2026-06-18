import pytest
import zipfile
import io
import os
from pathlib import Path
from appman.utils import LocalPathDownloader
from appman.payload import InstallAppPayload

def test_local_path_downloader_invalid_path():
    """Test that a missing path raises FileNotFoundError."""
    payload = InstallAppPayload(app="test", path="invalid/path/that/does/not/exist")
    downloader = LocalPathDownloader(payload, metadata_path="invalid/path/that/does/not/exist")
    with pytest.raises(FileNotFoundError):
        downloader.get_zip_file()

def test_local_path_downloader_with_zip_file(tmp_path):
    """Test that reading an actual .zip file returns a valid BytesIO buffer."""
    # Create a dummy zip file
    zip_path = tmp_path / "test_app.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("test.txt", "hello world")
        
    payload = InstallAppPayload(app="test", path=str(zip_path))
    downloader = LocalPathDownloader(payload, metadata_path=str(zip_path))
    
    result = downloader.get_zip_file()
    assert isinstance(result, io.BytesIO)
    
    # Read the returned zip to ensure it's valid
    with zipfile.ZipFile(result, "r") as zf:
        assert "test.txt" in zf.namelist()
        assert zf.read("test.txt") == b"hello world"

def test_local_path_downloader_with_directory(tmp_path):
    """Test that passing a directory creates an in-memory zip recursively."""
    # Create a dummy directory with subdirectories and files
    app_dir = tmp_path / "my_app"
    app_dir.mkdir()
    (app_dir / "file1.txt").write_text("data 1")
    
    sub_dir = app_dir / "subdir"
    sub_dir.mkdir()
    (sub_dir / "file2.txt").write_text("data 2")
    
    payload = InstallAppPayload(app="test", path=str(app_dir))
    downloader = LocalPathDownloader(payload, metadata_path=str(app_dir))
    
    result = downloader.get_zip_file()
    assert isinstance(result, io.BytesIO)
    
    # Read the returned zip to ensure it contains relative paths
    with zipfile.ZipFile(result, "r") as zf:
        namelist = zf.namelist()
        
        # In Linux/Unix, zip paths always use forward slashes
        assert "file1.txt" in namelist
        assert "subdir/file2.txt" in namelist
        assert zf.read("subdir/file2.txt") == b"data 2"

def test_local_path_downloader_invalid_file(tmp_path):
    """Test that passing a normal file (not a zip) raises a ValueError."""
    # File exists but is not a zip file
    text_file = tmp_path / "test.txt"
    text_file.write_text("not a zip")
    
    payload = InstallAppPayload(app="test", path=str(text_file))
    downloader = LocalPathDownloader(payload, metadata_path=str(text_file))
    
    with pytest.raises(ValueError, match="is neither a valid zip file nor a directory"):
        downloader.get_zip_file()
