# Dockerfile for ECS tasks
# Base image: Python 3.12
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    qpdf \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY lambda/ ./lambda/
COPY ecs/ ./ecs/

# Set Python path
ENV PYTHONPATH=/app

# Default command (will be overridden by ECS task definition)
CMD ["python", "-m", "app.main"]
