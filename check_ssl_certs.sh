#!/bin/bash
# Script to verify SSL certificates

# Set certificate paths
CERT_DIR="/home/arnab/Desktop/arabic_v2/app/certs"  # Use the app/certs directory instead
PRIVKEY="${CERT_DIR}/privkey.pem"
FULLCHAIN="${CERT_DIR}/fullchain.pem"

# Check if certificate directory exists
if [ ! -d "$CERT_DIR" ]; then
    echo "Certificate directory does not exist: $CERT_DIR"
    echo "Creating directory..."
    mkdir -p "$CERT_DIR"
fi

# Check if certificate files exist
echo "Checking SSL certificates..."
if [ ! -f "$PRIVKEY" ]; then
    echo "Private key not found: $PRIVKEY"
else
    echo "Private key exists: $PRIVKEY"
    # Check if it's a valid private key
    if openssl rsa -check -noout -in "$PRIVKEY" > /dev/null 2>&1; then
        echo "Private key is valid"
    else
        echo "Private key is invalid or empty"
    fi
fi

if [ ! -f "$FULLCHAIN" ]; then
    echo "Certificate not found: $FULLCHAIN"
else
    echo "Certificate exists: $FULLCHAIN"
    # Check if it's a valid certificate
    if openssl x509 -text -noout -in "$FULLCHAIN" > /dev/null 2>&1; then
        echo "Certificate is valid"
        # Print certificate details
        echo "Certificate details:"
        openssl x509 -text -noout -in "$FULLCHAIN" | grep "Subject:" -A 2
        openssl x509 -text -noout -in "$FULLCHAIN" | grep "Not Before:" -A 2
    else
        echo "Certificate is invalid or empty"
    fi
fi

# If certificates are missing or invalid, generate self-signed certificates
if [ ! -f "$PRIVKEY" ] || [ ! -f "$FULLCHAIN" ] || ! openssl x509 -text -noout -in "$FULLCHAIN" > /dev/null 2>&1; then
    echo "Generating self-signed certificates..."
    
    # Create OpenSSL config
    cat > "${CERT_DIR}/openssl.cnf" << EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = State
L = City
O = Organization
OU = Organizational Unit
CN = localhost

[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = 127.0.0.1
IP.1 = 127.0.0.1
EOF

    # Generate private key and self-signed certificate
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$PRIVKEY" \
        -out "$FULLCHAIN" \
        -config "${CERT_DIR}/openssl.cnf"
    
    echo "Self-signed certificates generated."
    echo "NOTE: For production use, replace these with proper certificates."
    echo "Certificate details:"
    openssl x509 -text -noout -in "$FULLCHAIN" | grep "Subject:" -A 2
    openssl x509 -text -noout -in "$FULLCHAIN" | grep "Not Before:" -A 2
fi

echo "SSL certificate verification complete."
