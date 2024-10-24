import uvicorn
import sys
from pathlib import Path
import os

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.logging_config import initialize_logger, get_logger

if __name__ == "__main__":
    # Initialize the logger with the LOG_LEVEL from environment variable
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    initialize_logger(log_level)
    logger = get_logger()
    
    logger.debug("Starting the server with debug logging enabled")
    
    uvicorn.run("app.api:app", host="0.0.0.0", port=8000, reload=True, log_level=log_level.lower())
