"""Tests for the logger module."""
import logging
from unittest.mock import patch, MagicMock

from src.utils.logger import get_logger


def test_get_logger_returns_logger_instance():
    """Test that get_logger returns a logger instance."""
    # Arrange
    logger_name = "test_logger"
    
    # Act
    logger = get_logger(logger_name)
    
    # Assert
    assert isinstance(logger, logging.Logger)
    assert logger.name == logger_name


def test_get_logger_configures_level():
    """Test that get_logger sets the correct log level."""
    # Arrange
    logger_name = "test_logger_level"
    
    # Patch the LOG_LEVEL in the config module
    with patch('src.core.config.LOG_LEVEL', 'DEBUG'):
        
        # Act
        logger = get_logger(logger_name)
        
        # Assert
        # Should be set to DEBUG from our patched value
        assert logger.level == logging.DEBUG


def test_get_logger_adds_handler_once():
    """Test that get_logger adds handlers only once."""
    # Arrange
    logger_name = "test_logger_handlers"
    
    # Act
    logger1 = get_logger(logger_name)
    handler_count = len(logger1.handlers)
    logger2 = get_logger(logger_name)
    
    # Assert
    assert len(logger2.handlers) == handler_count
    

@patch('logging.StreamHandler')
def test_get_logger_formatter_config(mock_handler):
    """Test that get_logger configures formatter correctly."""
    # Arrange
    mock_handler_instance = MagicMock()
    mock_handler.return_value = mock_handler_instance
    logger_name = "test_logger_formatter"
    
    # Act
    logger = get_logger(logger_name)
    
    # Assert
    mock_handler_instance.setFormatter.assert_called_once()
    # Formatter is set with the expected format string
    formatter = mock_handler_instance.setFormatter.call_args[0][0]
    assert '%(asctime)s - %(name)s - %(levelname)s - %(message)s' in formatter._fmt 