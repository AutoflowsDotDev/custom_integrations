import logging
import sys
from src.core.config import LOG_LEVEL

def get_logger(name: str) -> logging.Logger:
    """Configures and returns a logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    # Create handlers
    stdout_handler = logging.StreamHandler(sys.stdout)
    # You could also add a FileHandler here if you want to log to a file
    # file_handler = logging.FileHandler('app.log')

    # Create formatters and add it to handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stdout_handler.setFormatter(formatter)
    # file_handler.setFormatter(formatter)

    # Add handlers to the logger
    # Avoid adding handlers multiple times if the logger is already configured
    if not logger.handlers:
        logger.addHandler(stdout_handler)
        # logger.addHandler(file_handler)

    return logger

if __name__ == '__main__':
    # Example usage
    logger = get_logger(__name__)
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.") 