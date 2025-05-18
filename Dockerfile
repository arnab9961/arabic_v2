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
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Make directory for certificates
RUN mkdir -p /app/certs

# Make directory for LLaMA model if it doesn't exist
RUN mkdir -p /app/models

# Make directory for Quran text data if it doesn't exist
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8100
ENV SSL_PORT=8443

# Generate self-signed certificate if needed
RUN if [ ! -f "/app/certs/fullchain.pem" ]; then \
        openssl req -x509 -newkey rsa:4096 \
        -keyout /app/certs/privkey.pem \
        -out /app/certs/fullchain.pem \
        -days 365 -nodes -subj "/CN=localhost"; \
    fi

# Expose ports
EXPOSE 8100
EXPOSE 8443

# Run the application with SSL if certificates exist
CMD if [ -f "/app/certs/privkey.pem" ] && [ -f "/app/certs/fullchain.pem" ]; then \
        uvicorn app.main:app --host 0.0.0.0 --port 8443 --ssl-keyfile /app/certs/privkey.pem --ssl-certfile /app/certs/fullchain.pem; \
    else \
        uvicorn app.main:app --host 0.0.0.0 --port 8100; \
    fi