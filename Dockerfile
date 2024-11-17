# Use an official Python runtime as a parent image
FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /opt/amta

# Install system dependencies and venv creation tools
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3 -m venv /opt/amta/venv

# Explicitly set PATH to use venv
ENV PATH="/opt/amta/venv/bin:$PATH"

# Verify venv creation and activation
RUN python3 -m venv --help && \
    ls -la /opt/amta && \
    ls -la /opt/amta/venv && \
    which python && \
    python --version

# Upgrade pip in the virtual environment
RUN pip install --upgrade pip

# Copy project files
COPY . .

# Install dependencies in the virtual environment
RUN pip install --no-cache-dir -r requirements.txt

# Install the package in editable mode
RUN pip install --no-cache-dir -e .

# Verify package can be imported
RUN python -c "import app; print('App package imported successfully')"

# Make port 8081 available
EXPOSE 8081

# Set environment variables for the application
ENV DEPLOYMENT_MODE=production
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8081

# Use the virtual environment's Python to run the application
CMD ["python", "-m", "app.run_server"]
