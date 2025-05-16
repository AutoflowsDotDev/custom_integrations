import logging
import sys
from importlib import import_module

def get_logger(name: str) -> logging.Logger:
    """Return a configured logger instance.

    The logger level is determined from ``src.core.config.LOG_LEVEL`` each time this
    function is called so that test suites can monkey-patch the value at runtime
    (e.g. ``patch('src.core.config.LOG_LEVEL', 'DEBUG')``).  This avoids the value
    being frozen at import time, which previously prevented the log level from
    updating in tests.
    """
    logger = logging.getLogger(name)

    # Dynamically import the config module to pick up any runtime monkey-patches
    core_config = import_module('src.core.config')
    level_name = getattr(core_config, 'LOG_LEVEL', 'INFO').upper()
    level = getattr(logging, level_name, logging.INFO)

    logger.setLevel(level)

    # Do not add multiple handlers in repeated calls
    if not logger.handlers:
        stdout_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stdout_handler.setFormatter(formatter)
        logger.addHandler(stdout_handler)

    return logger

if __name__ == '__main__':
    # Example usage
    logger = get_logger(__name__)
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.") 