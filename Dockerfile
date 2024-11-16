# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set unique working directory
WORKDIR /opt/amta

# Create a virtual environment
ENV VIRTUAL_ENV=/opt/amta/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only necessary files for dependency installation
COPY requirements.txt setup.py pyproject.toml ./

# Install dependencies in the virtual environment
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install .

# Copy project files
COPY app/ ./app/
COPY .env.example ./.env
COPY config_validator.py ./

# Make port 8081 available
EXPOSE 8081

# Define environment variable
ENV NAME amta
ENV PORT=8081

# Run the application using uvicorn on a different port
CMD ["uvicorn", "app.run_server:app", "--host", "0.0.0.0", "--port", "8081"]
