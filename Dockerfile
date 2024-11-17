# Use an official Python runtime as a parent image
FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory to the project root
WORKDIR /atlomy_chat

# Install system dependencies and venv creation tools
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    python3-venv \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment in the project directory
RUN python3 -m venv /atlomy_chat/venv

# Explicitly set PATH to use venv
ENV PATH="/atlomy_chat/venv/bin:$PATH"

# Verify venv creation and activation
RUN python3 -m venv --help && \
    ls -la /atlomy_chat && \
    ls -la /atlomy_chat/venv && \
    which python && \
    python --version

# Upgrade pip in the virtual environment
RUN pip install --upgrade pip setuptools wheel

# Copy project files
COPY . .

# Create logs directory
RUN mkdir -p /atlomy_chat/logs && chmod 777 /atlomy_chat/logs

# Diagnostic step: list contents and verify package structure
RUN ls -R app && python -c "import sys; print(sys.path)"

# Install dependencies in the virtual environment
RUN pip install --no-cache-dir -r requirements.txt

# Install the package with verbose output and fallback
RUN pip install --no-cache-dir -v -e . \
    || (python setup.py egg_info && pip install --no-cache-dir -v .)

# Verify package can be imported with detailed error handling
RUN python -c "import app; print('App package imported successfully')" \
    || (echo "Package import failed" && ls -la && python setup.py develop)

# Make port 8081 available
EXPOSE 8081

# Set environment variables for the application
ENV DEPLOYMENT_MODE=production
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8081

# Logging configuration
ENV PYTHONUNBUFFERED=1
ENV LOGGING_CONFIG=/atlomy_chat/logging_config.json

# Use the virtual environment's Python to run the application
CMD ["python", "-m", "app.run_server"]
