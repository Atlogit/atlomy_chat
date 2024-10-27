"""
Logging configuration for the migration process.

Sets up logging to both file and console with different levels and formats.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

def setup_migration_logging(log_dir: Path = None, level: str = "INFO") -> None:
    """
    Configure logging for the migration process.
    
    Args:
        log_dir: Directory to store log files. If None, uses toolkit/migration/logs.
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    if log_dir is None:
        log_dir = Path(__file__).parent / "logs"
    
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "migration.log"
    
    # Convert string level to logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Create and configure file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Create and configure console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Create specific loggers
    loggers = {
        'migration': logging.getLogger('migration'),
        'citation': logging.getLogger('citation'),
        'database': logging.getLogger('database')
    }
    
    for logger in loggers.values():
        logger.setLevel(numeric_level)
        
    # Log migration start
    migration_logger = loggers['migration']
    migration_logger.info("Migration logging configured")
    migration_logger.info(f"Log file: {log_file}")
    migration_logger.info(f"Console log level: {level}")

def get_migration_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific migration component.
    
    Args:
        name: Name of the logger (e.g., 'citation', 'database')
        
    Returns:
        Logger instance for the specified component
    """
    return logging.getLogger(f'migration.{name}')
