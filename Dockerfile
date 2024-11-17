FROM python:3.11-slim-bullseye

# Set environment variables using modern format
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory to the project root
WORKDIR /atlomy_chat

# Install system dependencies with retry and specific mirror
RUN set -ex; \
    apt-get update || \
    (sleep 5 && apt-get update) || \
    (sleep 10 && apt-get update) || \
    (echo "Failed to update package lists" && exit 1); \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    python3-venv \
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
RUN pip install --upgrade pip

# Copy project files
COPY . .

# Install dependencies in the virtual environment
RUN pip install --no-cache-dir -r requirements.txt

# Install the package with fallback strategies
RUN pip install --no-cache-dir . || \
    pip install --no-cache-dir -e . || \
    pip install --no-cache-dir -e ./app || \
    pip install --no-cache-dir --no-deps .

# Verify package can be imported
RUN python -c "import app; print('App package imported successfully')" || \
    (echo "Import failed. Debugging information:" && \
     python -c "import sys; print('Python path:', sys.path)" && \
     ls -la && \
     exit 1)

# Make port 8081 available
EXPOSE 8081

# Set environment variables for the application
ENV DEPLOYMENT_MODE=production
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8081

# Use the virtual environment's Python to run the application
CMD ["python", "-m", "app.run_server"]
