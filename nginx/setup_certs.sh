#!/bin/bash

# Setup script for copying SSL certificates from app/certs to nginx/certs
# Run this after generating certificates with app/certs/generate_ssl.py

# Get the absolute path of the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_CERTS="${PROJECT_ROOT}/app/certs"
NGINX_CERTS="${PROJECT_ROOT}/nginx/certs"

echo "Setting up SSL certificates..."
echo "Project root: ${PROJECT_ROOT}"

# Create nginx/certs directory if it doesn't exist
mkdir -p "${NGINX_CERTS}"

# Check if app certificates exist
if [ -f "${APP_CERTS}/privkey.pem" ] && [ -f "${APP_CERTS}/fullchain.pem" ]; then
    # Copy certificates from app/certs to nginx/certs
    cp "${APP_CERTS}/privkey.pem" "${NGINX_CERTS}/privkey.pem"
    cp "${APP_CERTS}/fullchain.pem" "${NGINX_CERTS}/fullchain.pem"
    
    # Set proper permissions
    chmod 600 "${NGINX_CERTS}"/*.pem
    
    echo "✅ SSL certificates copied successfully to nginx/certs/"
else
    echo "❌ SSL certificates not found in ${APP_CERTS}/"
    echo "Please run 'python ${APP_CERTS}/generate_ssl.py' first"
    exit 1
fi