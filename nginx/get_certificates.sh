#!/bin/sh

# Script to obtain Let's Encrypt certificates for your domain
# Replace example.com with your actual domain name

# Stop nginx temporarily
docker-compose stop nginx

# Get certificates using certbot standalone mode
docker run --rm \
  -v "/home/arnab/Desktop/arabic_v2/nginx/certs:/etc/letsencrypt" \
  -v "/home/arnab/Desktop/arabic_v2/nginx/certs:/var/lib/letsencrypt" \
  -p 80:80 \
  certbot/certbot certonly --standalone \
  --preferred-challenges http \
  -d example.com \
  --agree-tos \
  --email your-email@example.com \
  --non-interactive

# Copy certificates to nginx folder
cp /home/arnab/Desktop/arabic_v2/nginx/certs/live/example.com/fullchain.pem /home/arnab/Desktop/arabic_v2/nginx/certs/fullchain.pem
cp /home/arnab/Desktop/arabic_v2/nginx/certs/live/example.com/privkey.pem /home/arnab/Desktop/arabic_v2/nginx/certs/privkey.pem

# Set proper permissions
chmod 644 /home/arnab/Desktop/arabic_v2/nginx/certs/fullchain.pem
chmod 600 /home/arnab/Desktop/arabic_v2/nginx/certs/privkey.pem

# Restart nginx
docker-compose start nginx

echo "SSL certificates obtained successfully!"