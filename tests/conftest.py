import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def mock_env_vars():
    """Fixture to provide mock environment variables"""
    return {
        'ACR_NAME': 'test_acr_registry',
        'AZURE_CLIENT_ID': 'test_client_id',
        'AZURE_CLIENT_SECRET': 'test_client_secret',
        'AZURE_TENANT_ID': 'test_tenant_id'
    }


@pytest.fixture(autouse=True)
def clean_env():
    """Automatically clean environment variables after each test"""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)