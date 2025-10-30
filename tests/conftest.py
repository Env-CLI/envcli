"""
Test configuration and fixtures for EnvCLI.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import Mock, patch

from envcli.config import CONFIG_DIR
from envcli.env_manager import EnvManager


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment with isolated config."""
    # Create temporary directory for tests
    test_config_dir = Path(tempfile.mkdtemp(prefix="envcli_test_"))

    # Override config directory for tests
    with patch('envcli.config.CONFIG_DIR', test_config_dir):
        with patch('envcli.config.PROFILES_DIR', test_config_dir / "profiles"):
            with patch('envcli.config.CONFIG_FILE', test_config_dir / "config.yaml"):
                yield test_config_dir

    # Clean up after tests
    shutil.rmtree(test_config_dir, ignore_errors=True)


@pytest.fixture
def temp_config_dir():
    """Provide a temporary config directory for individual tests."""
    temp_dir = Path(tempfile.mkdtemp(prefix="envcli_test_"))
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_env_vars():
    """Sample environment variables for testing."""
    return {
        "API_KEY": "test-api-key-12345",
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/testdb",
        "DEBUG": "true",
        "PORT": "8080",
        "SECRET_TOKEN": "super-secret-token-abcdef"
    }


@pytest.fixture
def env_manager(sample_env_vars):
    """Create an EnvManager instance for testing."""
    manager = EnvManager("test_profile")
    manager.save_env(sample_env_vars)
    return manager


@pytest.fixture
def mock_aws_ssm():
    """Mock AWS SSM client."""
    with patch('boto3.client') as mock_client:
        mock_ssm = Mock()
        mock_client.return_value = mock_ssm

        # Mock parameter operations
        mock_ssm.get_parameters_by_path.return_value = {
            'Parameters': [
                {'Name': '/test/KEY1', 'Value': 'value1'},
                {'Name': '/test/KEY2', 'Value': 'value2'}
            ]
        }
        mock_ssm.put_parameter.return_value = {}
        mock_ssm.delete_parameters.return_value = {'DeletedParameters': []}

        yield mock_ssm


@pytest.fixture
def mock_github_api():
    """Mock GitHub API responses."""
    import responses

    with responses.RequestsMock() as rsps:
        # Mock public key endpoint
        rsps.add(
            responses.GET,
            "https://api.github.com/repos/test/repo/actions/secrets/public-key",
            json={"key_id": "test_key_id", "key": "test_public_key"},
            status=200
        )

        # Mock secret creation
        rsps.add(
            responses.PUT,
            "https://api.github.com/repos/test/repo/actions/secrets/TEST_SECRET",
            json={},
            status=201
        )

        yield rsps


@pytest.fixture
def mock_kubernetes():
    """Mock Kubernetes client."""
    with patch('kubernetes.client.CoreV1Api') as mock_api_class:
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        # Mock secret operations
        mock_secret = Mock()
        mock_secret.data = {"KEY1": "dmFsdWUx", "KEY2": "dmFsdWUy"}  # base64 encoded
        mock_api.read_namespaced_secret.return_value = mock_secret
        mock_api.create_namespaced_secret.return_value = mock_secret
        mock_api.replace_namespaced_secret.return_value = mock_secret
        mock_api.list_namespaced_secret.return_value = Mock(items=[Mock(metadata=Mock(name="test-secret"))])

        # Mock configmap operations
        mock_configmap = Mock()
        mock_configmap.data = {"KEY1": "value1", "KEY2": "value2"}
        mock_api.read_namespaced_config_map.return_value = mock_configmap
        mock_api.create_namespaced_config_map.return_value = mock_configmap
        mock_api.replace_namespaced_config_map.return_value = mock_configmap

        yield mock_api


@pytest.fixture
def mock_vault():
    """Mock HashiCorp Vault client."""
    with patch('hvac.Client') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.is_authenticated.return_value = True

        # Mock KV operations
        mock_client.secrets.kv.v2.create_or_update_secret_version.return_value = {}
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            'data': {'data': {"KEY1": "value1", "KEY2": "value2"}}
        }

        yield mock_client


@pytest.fixture
def mock_ai_model():
    """Mock AI model for testing."""
    with patch('transformers.pipeline') as mock_pipeline:
        mock_classifier = Mock()
        mock_classifier.return_value = [
            {"label": "POSITIVE", "score": 0.9},
            {"label": "NEGATIVE", "score": 0.1}
        ]
        mock_pipeline.return_value = mock_classifier
        yield mock_classifier


@pytest.fixture
def test_profile_data():
    """Test profile data for various test scenarios."""
    return {
        "dev": {
            "API_KEY": "dev-api-key",
            "DATABASE_URL": "postgresql://dev:dev@localhost:5432/devdb",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG"
        },
        "staging": {
            "API_KEY": "staging-api-key",
            "DATABASE_URL": "postgresql://staging:staging@staging-db:5432/stagingdb",
            "DEBUG": "false",
            "LOG_LEVEL": "INFO"
        },
        "prod": {
            "API_KEY": "prod-api-key-secure",
            "DATABASE_URL": "postgresql://prod_user:prod_pass@prod-db:5432/proddb",
            "DEBUG": "false",
            "LOG_LEVEL": "ERROR",
            "REDIS_URL": "redis://prod-redis:6379",
            "SECRET_TOKEN": "prod-secret-token-12345"
        }
    }


@pytest.fixture
def cli_runner():
    """CLI runner for integration tests."""
    from typer.testing import CliRunner
    return CliRunner()


# Test data constants
TEST_PROFILES = ["dev", "staging", "prod"]
TEST_ENV_VARS = {
    "API_KEY": "test-api-key",
    "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
    "REDIS_URL": "redis://localhost:6379",
    "SECRET_KEY": "super-secret-key"
}
TEST_POLICIES = {
    "required_keys": [{"pattern": "API_.*", "description": "API keys required"}],
    "prohibited_patterns": [{"pattern": "password", "description": "No plain passwords"}],
    "naming_conventions": [{"convention": "uppercase", "description": "Use uppercase"}]
}
TEST_USERS = [
    {"username": "admin", "role": "admin"},
    {"username": "dev1", "role": "member"},
    {"username": "readonly", "role": "guest"}
]
