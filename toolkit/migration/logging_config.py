"""
Logging configuration for the migration process.

Sets up comprehensive logging with file and console handlers,
ensuring detailed logs are captured and preserved.
"""

import logging
import sys
import os
from pathlib import Path
from datetime import datetime
import os

def setup_migration_logging(
    log_dir: Path = None, 
    level: str = "DEBUG", 
    max_log_size_bytes: int = 100 * 1024 * 1024  # 100 MB
) -> Path:
    """
    Configure comprehensive logging for migration processes.
    
    Args:
        log_dir: Directory to store log files
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_log_size_bytes: Maximum size of log file before rotation
    
    Returns:
        Path to the current log file
    """
    # Reduce verbosity for external libraries
    external_loggers = [
        'sqlalchemy', 'alembic', 'asyncio', 'urllib3', 
        'botocore', 'boto3', 's3transfer'
    ]
    for logger_name in external_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    # Default log directory in project's logs folder with migration subfolder
    if log_dir is None:
        log_dir = Path(__file__).parent.parent.parent / "logs" / "migration_runs"
    
    # Ensure log directory exists with proper permissions
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate unique log filename with detailed timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_file = log_dir / f"migration_{timestamp}.log"
    
    # Convert string level to logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Create file handler without rotation to preserve all logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(file_formatter)
    
    # Create and configure console handler with reduced verbosity
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)  # Only show warnings and errors on console
    console_handler.setFormatter(console_formatter)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[file_handler, console_handler],
        force=True  # Ensure existing loggers are reconfigured
    )
    
    # Reduce verbosity for external libraries
    external_loggers = [
        'sqlalchemy', 'alembic', 'asyncio', 'urllib3', 
        'botocore', 'boto3', 's3transfer'
    ]
    for logger_name in external_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    # Ensure all loggers propagate
    root_logger = logging.getLogger()
    root_logger.propagate = True
    
    # Log configuration details
    migration_logger = logging.getLogger('migration.core')
    migration_logger.info("Migration logging configured")
    migration_logger.info(f"Log file: {log_file}")
    migration_logger.info(f"Log level: {level}")
    migration_logger.info(f"Log directory: {log_dir}")

    return log_file

def get_migration_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific migration component.
    
    Args:
        name: Name of the logger
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(f'migration.{name}')
    logger.propagate = True
    return logger
