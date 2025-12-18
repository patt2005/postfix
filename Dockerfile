# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# Disable NNPACK to avoid warnings on Cloud Run (unsupported hardware)
ENV USE_NNPACK=0
ENV PYTORCH_DISABLE_NNPACK=1
# Force CPU device on Cloud Run (no GPU available)
ENV FORCE_CPU=1
# Set model cache directory to a writable location
ENV XDG_CACHE_HOME=/app/.cache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create cache directory for models
RUN mkdir -p /app/.cache && chmod 777 /app/.cache

# Create temp directory for video processing
RUN mkdir -p /app/temp && chmod 777 /app/temp

# Expose the port the app runs on
EXPOSE 8080

# Run the application with gunicorn for production
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app