# Use an official Python runtime as a parent image
FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV VIRTUAL_ENV=/amta/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONPATH="/amta:$PYTHONPATH"

# Set working directory to the project root
WORKDIR /amta

# Install system dependencies and venv creation tools
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    python3-venv \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment in the project directory
RUN python3 -m venv $VIRTUAL_ENV

# Explicitly set PATH to use venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Verify venv creation and activation
RUN python3 -m venv --help && \
    ls -la /amta && \
    ls -la $VIRTUAL_ENV && \
    which python && \
    python --version

# Upgrade pip in the virtual environment
RUN pip install --upgrade pip setuptools wheel

# Copy project files
COPY . .

# Create logs directory
RUN mkdir -p /amta/logs && chmod 777 /amta/logs

# Diagnostic step: list contents and verify package structure
RUN ls -R app && python -c "import sys; print('\n'.join(sys.path))"

# Install dependencies in the virtual environment
RUN pip install --no-cache-dir -r requirements.txt

# Verbose package installation with comprehensive diagnostics
RUN pip install --no-cache-dir -v -e . || \
    (echo "=== Package Installation Diagnostics ===" && \
     echo "Virtual Environment: $VIRTUAL_ENV" && \
     echo "Current Directory: $(pwd)" && \
     echo "=== Directory Contents ===" && \
     ls -la && \
     echo "=== Python Path ===" && \
     python -c "import sys; print('\n'.join(sys.path))" && \
     echo "=== Installed Packages ===" && \
     pip list && \
     echo "=== PYTHONPATH ===" && \
     python -c "import os; print(os.environ.get('PYTHONPATH', 'Not set'))" && \
     false)

# Additional diagnostic steps for package discovery
RUN python -c "import sys; print('Current working directory:', sys.path[0])" && \
    python -c "import os; print('Current working directory:', os.getcwd())"

# Verify package can be imported
RUN python -c "import app; print('App package imported successfully')"

# Verify specific module can be imported with full path
RUN PYTHONPATH=/amta python -c "from app import run_server; print('run_server module imported successfully')"

# Make port 8081 available
EXPOSE 8081

# Set environment variables for the application
ENV DEPLOYMENT_MODE=production
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8081

# Use the virtual environment's Python to run the application
CMD ["python", "-m", "app.run_server"]
