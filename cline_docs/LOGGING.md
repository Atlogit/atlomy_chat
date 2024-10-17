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

Log files are automatically rotated daily and kept for 7 days. They are stored in the `logs` directory.

## JSON Logging

When JSON logging is enabled, log entries are formatted as JSON objects, making them easier to parse and analyze with log management tools.

## Best Practices

1. Use appropriate log levels for different types of messages.
2. Include relevant context in log messages to aid in debugging and monitoring.
3. Avoid logging sensitive information.
4. Use structured logging (e.g., JSON format) when integrating with log analysis tools.

## Troubleshooting

If you're not seeing logs:
1. Check that the LOG_LEVEL is set appropriately.
2. Ensure CONSOLE_OUTPUT and/or FILE_OUTPUT are set to 'true'.
3. Verify that the logs directory exists and is writable.

For any issues or questions about the logging system, please contact the development team.
