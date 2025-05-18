import os
import subprocess
from pathlib import Path

def generate_self_signed_certificate():
    """Generate a self-signed SSL certificate if none exists"""
    
    # Create directory for certificates
    certs_dir = Path(__file__).parent.absolute()
    certs_dir.mkdir(exist_ok=True, parents=True)
    
    # Define certificate files
    key_file = certs_dir / "privkey.pem"
    cert_file = certs_dir / "fullchain.pem"
    
    # Check if certificates already exist
    if key_file.exists() and cert_file.exists():
        print("SSL certificates already exist")
        return
    
    print("Generating self-signed SSL certificate...")
    
    # Generate self-signed certificate with OpenSSL
    cmd = [
        "openssl", "req", "-x509", 
        "-newkey", "rsa:4096", 
        "-keyout", str(key_file),
        "-out", str(cert_file),
        "-days", "365",
        "-nodes",
        "-subj", "/CN=localhost"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Generated SSL certificate at {cert_file}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to generate SSL certificate: {e}")
        
if __name__ == "__main__":
    generate_self_signed_certificate()