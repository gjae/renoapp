import pytest
import zipfile
import io
import os
from pathlib import Path
from appman.utils import LocalPathDownloader
from appman.payload import InstallAppPayload

def test_local_path_downloader_invalid_path():
    """Test that a missing path raises FileNotFoundError."""
    payload = InstallAppPayload(app="test_app", path="/invalid/path")
    downloader = LocalPathDownloader(payload, metadata_path="__app__.json")
    with pytest.raises(FileNotFoundError):
        downloader.get_zip_file()

def test_local_path_downloader_with_directory(tmp_path):
    """Test that passing a directory creates an in-memory zip recursively."""
    # Base directory
    base_dir = tmp_path / "apps"
    base_dir.mkdir()
    
    # App directory
    app_dir = base_dir / "test_app"
    app_dir.mkdir()
    
    # Metadata file
    (app_dir / "__app__.json").write_text('{"name": "test_app"}')
    
    # Random files
    (app_dir / "file1.txt").write_text("data 1")
    
    sub_dir = app_dir / "subdir"
    sub_dir.mkdir()
    (sub_dir / "file2.txt").write_text("data 2")
    
    payload = InstallAppPayload(app="test_app", path=str(base_dir))
    downloader = LocalPathDownloader(payload, metadata_path="__app__.json")
    
    result = downloader.get_zip_file()
    assert isinstance(result, io.BytesIO)
    
    # Read the returned zip to ensure it contains relative paths
    with zipfile.ZipFile(result, "r") as zf:
        namelist = zf.namelist()
        
        assert "__app__.json" in namelist
        assert "file1.txt" in namelist
        assert "subdir/file2.txt" in namelist
        assert zf.read("subdir/file2.txt") == b"data 2"
