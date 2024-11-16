# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /opt/amta

# Create a virtual environment
RUN python3 -m venv /opt/amta/venv
ENV PATH="/opt/amta/venv/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire project directory
COPY . .

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Install dependencies in the virtual environment
RUN pip install --no-cache-dir -r requirements.txt

# Install the package in editable mode
RUN pip install --no-cache-dir -e .

# Make port 8081 available
EXPOSE 8081

# Define environment variable
ENV NAME amta
ENV PORT=8081

# Use the virtual environment's Python to run the application
CMD ["uvicorn", "app.run_server:app", "--host", "0.0.0.0", "--port", "8081"]
