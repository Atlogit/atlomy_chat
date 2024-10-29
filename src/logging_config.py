import logging
import os
import json
from logging.handlers import RotatingFileHandler
from datetime import datetime

def json_formatter(record):
    """
    Custom JSON formatter for log records.
    """
    log_data = {
        'timestamp': datetime.utcfromtimestamp(record.created).isoformat(),
        'level': record.levelname,
        'message': record.getMessage(),
        'module': record.module,
        'function': record.funcName,
        'line': record.lineno,
    }
    return json.dumps(log_data)

class EnvConfig:
    """
    Configuration class that reads from environment variables.
    """
    def __init__(self):
        self.LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
        self.LOG_FORMAT = os.environ.get('LOG_FORMAT', 'standard')
        self.CONSOLE_OUTPUT = os.environ.get('CONSOLE_OUTPUT', 'true').lower() == 'true'
        self.FILE_OUTPUT = os.environ.get('FILE_OUTPUT', 'true').lower() == 'true'
        self.LOG_FILE = os.environ.get('LOG_FILE', 'atlomy_chat.log')
        self.JSON_LOGGING = os.environ.get('JSON_LOGGING', 'false').lower() == 'true'
        # New configuration options for log rotation with stricter defaults
        self.MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 5242880))  # 5MB default
        self.BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))

def setup_logging(config=None, **kwargs):
    """
    Set up logging configuration for the application.
    
    Args:
    config (dict, optional): Configuration dictionary. If not provided, environment variables will be used.
    kwargs: Additional keyword arguments to override configuration.

    Returns:
    logging.Logger: Configured logger object
    """
    if config is None:
        config = EnvConfig()
        
    # Override configuration with keyword arguments
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    # Print the configuration to verify
    print("Using environment variables for configuration", config.__dict__)

    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_path = os.path.join(log_dir, config.LOG_FILE)
    
    # Create a logger
    logger = logging.getLogger('atlomy_chat')
    logger.setLevel(config.LOG_LEVEL.upper())
    print(f"Logger level set to: {logger.level} ({logging.getLevelName(logger.level)})")

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create handlers
    handlers = []
    if config.CONSOLE_OUTPUT:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(config.LOG_LEVEL.upper())
        print(f"Console handler level set to: {console_handler.level} ({logging.getLevelName(console_handler.level)})")
        handlers.append(console_handler)
    if config.FILE_OUTPUT:
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=config.MAX_BYTES,
            backupCount=config.BACKUP_COUNT
        )
        file_handler.setLevel(logging.DEBUG)  # File handler set to DEBUG to capture all logs
        handlers.append(file_handler)
    
    # Create formatters and add it to handlers
    if config.LOG_FORMAT == 'json':
        formatter = logging.Formatter(json_formatter)
    else:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s')
    
    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

# Global logger instance
logger = None

def initialize_logger(log_level=None):
    global logger
    if logger is None:
        print("Initializing logger...")
        if log_level is not None:
            print(f"Setting log level to: {log_level}")
            logger = setup_logging(LOG_LEVEL=log_level)
            print("Logger initialized")
        else:
            print("Logger already initialized")
            logger = setup_logging()
            print("Logger already initialized")
                    
def change_log_level(level):
    """
    Dynamically change the log level at runtime.
    
    Args:
    level (str): The new log level (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    logger.setLevel(logging.getLevelName(level.upper()))
    logger.info(f"Log level changed to {level.upper()}")

def get_logger():
    """
    Get the configured logger instance.
    
    Returns:
    logging.Logger: The configured logger object
    """
    return logger
