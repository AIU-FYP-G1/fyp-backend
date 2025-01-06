import pytest
import shutil
import os
from django.conf import settings

@pytest.fixture(autouse=True)
def cleanup_media():
    """Cleanup all test media files after each test"""
    yield
    try:
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
    except Exception as e:
        print(f"Error cleaning up media files: {e}")

@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Cleanup any other test files"""
    yield
    try:
        paths_to_cleanup = [
            'test_echo.txt',
            'test_image.jpg',
        ]
        for path in paths_to_cleanup:
            try:
                os.remove(path)
            except OSError:
                pass
    except Exception as e:
        print(f"Error cleaning up test files: {e}")