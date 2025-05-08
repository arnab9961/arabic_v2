FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    pkg-config \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Make directory for LLaMA model if it doesn't exist
RUN mkdir -p /app/models

# Make directory for Quran text data if it doesn't exist
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8100

# Expose port
EXPOSE 8100

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "10.0.10.182", "--port", "8100"]