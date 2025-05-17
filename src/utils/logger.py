import logging
import logging.handlers
import sys
import os
from importlib import import_module
import time
from typing import Optional, Union
import uuid

# Create the logs directory if it doesn't exist
os.makedirs("src/logs", exist_ok=True)

# Global variable to store the current run number
_current_run_number = None

def get_run_number() -> int:
    """Return the current run number, initializing if needed."""
    global _current_run_number
    if _current_run_number is None:
        # Read the last run number from a file, or start at 1
        try:
            with open("src/logs/run_number.txt", "r") as f:
                _current_run_number = int(f.read().strip())
        except (FileNotFoundError, ValueError):
            _current_run_number = 0
        
        # Increment for the current run
        _current_run_number += 1
        
        # Save the new run number
        with open("src/logs/run_number.txt", "w") as f:
            f.write(str(_current_run_number))
    
    return _current_run_number

class ContextAdapter(logging.LoggerAdapter):
    """Logger adapter that adds contextual information to log records."""
    
    def __init__(self, logger, extra=None):
        """Initialize the adapter with default extra dict if none provided."""
        if extra is None:
            extra = {"run_id": get_run_number(), "step": None, "request_id": str(uuid.uuid4())}
        super().__init__(logger, extra)
    
    def process(self, msg, kwargs):
        """Process the log record, adding contextual information."""
        run_id = self.extra.get("run_id", get_run_number())
        step = self.extra.get("step", "")
        step_str = f"step:{step}-" if step else ""
        
        # Format message with run and step information
        new_msg = f"run: {run_id}, {step_str}{msg}"
        return new_msg, kwargs
    
    def set_step(self, step: str) -> None:
        """Set the current workflow step."""
        self.extra["step"] = step
        
    def set_request_id(self, request_id: str) -> None:
        """Set the request ID for request tracking."""
        self.extra["request_id"] = request_id
    
    # Forward logger attributes for compatibility with tests
    @property
    def level(self):
        """Return the logger's level for test compatibility."""
        return self.logger.level
    
    @property
    def handlers(self):
        """Return the logger's handlers for test compatibility."""
        return self.logger.handlers
    
    @property
    def name(self):
        """Return the logger's name for test compatibility."""
        return self.logger.name

def get_logger(name: str) -> Union[logging.Logger, ContextAdapter]:
    """Return a configured logger instance with context adapter.
    
    The logger includes both console and file handlers with proper formatting
    for structured logging and monitoring. Log files are rotated to manage size.
    
    Args:
        name: The logger name, typically __name__
        
    Returns:
        ContextAdapter: A logger adapter that adds contextual information
    """
    logger = logging.getLogger(name)

    # Dynamically import the config module to pick up any runtime monkey-patches
    core_config = import_module('src.core.config')
    level_name = getattr(core_config, 'LOG_LEVEL', 'INFO').upper()
    level = getattr(logging, level_name, logging.INFO)

    logger.setLevel(level)

    # Do not add multiple handlers in repeated calls
    if not logger.handlers:
        # Standard formatter with timestamp, level, name, and message
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Create a structured formatter for file output
        structured_formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s', 
                                     datefmt='%b %d, %Y %H:%M:%S')
        
        # Console handler (stdout)
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)  # Use standard formatter for console
        logger.addHandler(stdout_handler)
        
        # File handler for all logs
        file_handler = logging.handlers.RotatingFileHandler(
            filename="src/logs/app.log",
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(structured_formatter)  # Use structured formatter for files
        logger.addHandler(file_handler)
        
        # File handler for debug logs only
        debug_handler = logging.handlers.RotatingFileHandler(
            filename="src/logs/app_debug.log",
            maxBytes=10485760,  # 10MB
            backupCount=2
        )
        debug_handler.setFormatter(structured_formatter)
        debug_handler.setLevel(logging.DEBUG)
        logger.addHandler(debug_handler)
        
        # File handler for errors only
        error_handler = logging.handlers.RotatingFileHandler(
            filename="src/logs/app_error.log",
            maxBytes=10485760,  # 10MB
            backupCount=3
        )
        error_handler.setFormatter(structured_formatter)
        error_handler.setLevel(logging.ERROR)
        logger.addHandler(error_handler)

    # Return the logger wrapped in a context adapter
    return ContextAdapter(logger)

if __name__ == '__main__':
    # Example usage
    logger = get_logger(__name__)
    logger.set_step("testing_logger")
    
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")
    
    # Example of changing step
    logger.set_step("second_step")
    logger.info("This is a message from the second step.") 