# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install the project
RUN pip install .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Copy .env file (if exists)
COPY .env.example /app/.env

# Define environment variable
ENV NAME amta

# Run the application using uvicorn
CMD ["uvicorn", "app.run_server:app", "--host", "0.0.0.0", "--port", "8000"]
