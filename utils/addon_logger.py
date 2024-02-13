import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name, log_file, level=logging.ERROR, max_size=1048576, backups=5):
    """Sets up a rotating file logger.

    Args:
        name (str): Name of the logger.
        log_file (str): Path to the log file.
        level (int, optional): Logging level. Defaults to logging.ERROR.
        max_size (int, optional): Max size of log file in bytes. Defaults to 1048576 (1MB).
        backups (int, optional): Number of backup files to keep. Defaults to 5.
    
    Returns:
        logging.Logger: Configured logger.
    """
    # Create a logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create a rotating file handler
    handler = RotatingFileHandler(log_file, maxBytes=max_size, backupCount=backups)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

    # Add the levels to the logger
    logger.setLevel(level)
    logger.setLevel(logging.INFO)

    return logger

# Determine path to addon directory
addon_directory = os.path.dirname(os.path.dirname(__file__))
print(addon_directory)
error_dir =f'{addon_directory}{os.sep}error_logs'
# Set up the logger (adjust the file path as needed)
log_file_path = os.path.join(error_dir, 'error_log.txt')
if not os.path.exists(error_dir):
    os.mkdir(error_dir)
addon_logger = setup_logger('addon_logger', log_file_path)


def unregister():
    
    addon_logger.handlers.clear()
    for handler in addon_logger.handlers:
        handler.close()
        addon_logger.handlers.remove(handler)