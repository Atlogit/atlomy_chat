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
        self.MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 5242880))  # 5MB default
        self.BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))

def setup_logging(config=None, **kwargs):
    """
    Set up logging configuration for the application.
    """
    if config is None:
        config = EnvConfig()
        
    # Override configuration with keyword arguments
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_path = os.path.join(log_dir, config.LOG_FILE)
    
    # Configure root logger to prevent duplicate logging
    root_logger = logging.getLogger()
    root_logger.handlers = []  # Remove any existing handlers
    
    # Create handlers
    handlers = []
    if config.CONSOLE_OUTPUT:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(config.LOG_LEVEL.upper())
        handlers.append(console_handler)
    if config.FILE_OUTPUT:
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=config.MAX_BYTES,
            backupCount=config.BACKUP_COUNT
        )
        file_handler.setLevel(logging.DEBUG)
        handlers.append(file_handler)
    
    # Create formatter
    if config.LOG_FORMAT == 'json':
        formatter = logging.Formatter(json_formatter)
    else:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s')
    
    # Configure root logger
    root_logger.setLevel(config.LOG_LEVEL.upper())
    for handler in handlers:
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    
    # Configure FastAPI logger
    fastapi_logger = logging.getLogger("fastapi")
    fastapi_logger.handlers = []  # Remove any existing handlers
    fastapi_logger.propagate = True  # Let it propagate to root logger
    
    # Configure uvicorn logger
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers = []  # Remove any existing handlers
    uvicorn_logger.propagate = True  # Let it propagate to root logger
    
    # Configure our app logger
    app_logger = logging.getLogger('atlomy_chat')
    app_logger.handlers = []  # Remove any existing handlers
    app_logger.propagate = True  # Let it propagate to root logger
    
    return app_logger

# Global logger instance
logger = None

def initialize_logger(log_level=None):
    """Initialize the global logger instance."""
    global logger
    if logger is None:
        if log_level is not None:
            logger = setup_logging(LOG_LEVEL=log_level)
        else:
            logger = setup_logging()
                    
def change_log_level(level):
    """
    Dynamically change the log level at runtime.
    """
    if logger:
        logger.setLevel(logging.getLevelName(level.upper()))
        # Also update root logger to maintain consistency
        logging.getLogger().setLevel(logging.getLevelName(level.upper()))
        logger.info(f"Log level changed to {level.upper()}")

def get_logger():
    """
    Get the configured logger instance.
    """
    return logger
