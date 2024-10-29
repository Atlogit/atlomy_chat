# Logging System Documentation

This document provides an overview of the logging system implemented in the Ancient Medical Texts Analysis App.

## Overview

The logging system is centralized and configurable, allowing for flexible log management across the application. It supports both console and file output, with options for different log formats and levels.

## Configuration

The logging system can be configured using environment variables or by passing a configuration object to the `setup_logging` function.

### Environment Variables

- `LOG_LEVEL`: Sets the logging level (default: 'INFO')
- `LOG_FORMAT`: Sets the log format, either 'standard' or 'json' (default: 'standard')
- `CONSOLE_OUTPUT`: Enables/disables console output (default: 'true')
- `FILE_OUTPUT`: Enables/disables file output (default: 'true')
- `LOG_FILE`: Sets the name of the log file (default: 'atlomy_chat.log')
- `JSON_LOGGING`: Enables/disables JSON formatting for logs (default: 'false')
- `LOG_MAX_BYTES`: Maximum size of each log file in bytes (default: 5242880 [5MB])
- `LOG_BACKUP_COUNT`: Number of backup files to keep (default: 5)

### Log Levels

Available log levels, in order of increasing severity:

1. DEBUG
2. INFO
3. WARNING
4. ERROR
5. CRITICAL

## Usage

### Basic Usage

To use the logger in your code:

```python
from logging_config import logger

logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
logger.critical("This is a critical message")
```

### Changing Log Level at Runtime

You can change the log level dynamically using the `change_log_level` function:

```python
from logging_config import change_log_level

change_log_level('DEBUG')
```

### Getting Logger Instance

If you need to get the logger instance in a different module:

```python
from logging_config import get_logger

logger = get_logger()
```

## Log File Management

Log files are automatically rotated based on size:
- Each log file has a maximum size of 5MB (configurable via LOG_MAX_BYTES)
- When a log file reaches its size limit, it is renamed with a suffix (e.g., .1, .2, etc.)
- Up to 5 backup files are kept (configurable via LOG_BACKUP_COUNT)
- Older log files are automatically deleted when the backup count is exceeded

For example, with default settings:
- Current log: atlomy_chat.log (active file, up to 5MB)
- Backups: atlomy_chat.log.1, atlomy_chat.log.2, etc. (up to atlomy_chat.log.5)
- Total maximum disk usage: ~25MB (5 files × 5MB)

## JSON Logging

When JSON logging is enabled, log entries are formatted as JSON objects, making them easier to parse and analyze with log management tools.

## Best Practices

1. Use appropriate log levels for different types of messages:
   - DEBUG: Detailed information for debugging
   - INFO: General operational events
   - WARNING: Unexpected but handled situations
   - ERROR: Errors that affect functionality
   - CRITICAL: Severe errors that prevent operation
2. Include relevant context in log messages to aid in debugging and monitoring
3. Avoid logging sensitive information
4. Use structured logging (e.g., JSON format) when integrating with log analysis tools
5. Monitor log file sizes and rotation to ensure proper disk space management

## Log Management Tips

1. Regular Monitoring:
   - Check log file sizes periodically
   - Monitor disk space usage in the logs directory
   - Review log rotation to ensure it's working as expected

2. Log Cleanup:
   - The system automatically manages log files through rotation
   - Old log files are automatically deleted when they exceed the backup count
   - Manual cleanup is typically not needed unless there are special circumstances

3. Troubleshooting Large Log Files:
   - If logs grow too large too quickly, consider:
     - Adjusting the log level to reduce verbosity
     - Reviewing code for excessive logging
     - Decreasing the LOG_MAX_BYTES value
     - Increasing log rotation frequency

## Troubleshooting

If you're not seeing logs:
1. Check that the LOG_LEVEL is set appropriately
2. Ensure CONSOLE_OUTPUT and/or FILE_OUTPUT are set to 'true'
3. Verify that the logs directory exists and is writable
4. Check if log rotation is working by examining the log files in the logs directory

For any issues or questions about the logging system, please contact the development team.
