"""Tests for the config module."""
import os
import pytest
from unittest.mock import patch

from src.core.config import get_env_variable, ConfigError, validate_config


def test_get_env_variable_success():
    """Test retrieving an environment variable."""
    # Arrange
    test_var = "TEST_ENV_VAR"
    test_value = "test_value"
    os.environ[test_var] = test_value
    
    # Act
    result = get_env_variable(test_var)
    
    # Assert
    assert result == test_value
    
    # Cleanup
    del os.environ[test_var]


def test_get_env_variable_with_default():
    """Test retrieving a non-existent environment variable with a default value."""
    # Arrange
    test_var = "NON_EXISTENT_VAR"
    default_value = "default_value"
    
    # Act
    result = get_env_variable(test_var, default_value)
    
    # Assert
    assert result == default_value


def test_get_env_variable_missing_no_default():
    """Test retrieving a non-existent environment variable without a default value."""
    # Arrange
    test_var = "NON_EXISTENT_VAR"
    
    # Act & Assert
    with pytest.raises(ConfigError) as excinfo:
        get_env_variable(test_var)
    
    assert str(excinfo.value) == f"Environment variable '{test_var}' not found and no default value provided."


def test_validate_config_success():
    """Test successful configuration validation."""
    # This should succeed with the mock_env_variables fixture (autouse=True)
    validate_config()
    # No assertion needed - if no exception is raised, the test passes


@patch.dict(os.environ, {"SLACK_BOT_TOKEN": ""}, clear=False)
def test_validate_config_missing_required():
    """Test configuration validation with a missing required variable."""
    # Patch the SLACK_BOT_TOKEN environment variable to be empty
    # and also update the global SLACK_BOT_TOKEN in the config module
    # Otherwise, it will already have the default value from the config initialization
    with patch('src.core.config.SLACK_BOT_TOKEN', ''):
        with pytest.raises(ConfigError) as excinfo:
            validate_config()
        
        assert "Missing required configuration: SLACK_BOT_TOKEN" in str(excinfo.value) 