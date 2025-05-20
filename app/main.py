import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from app.api.routes import router as api_router
from app.core.config import get_settings

app = FastAPI(
    title="Quranic Pronunciation Assessment",
    description="A system to assess pronunciation accuracy in Quranic recitation",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API routes
app.include_router(api_router)

if __name__ == "__main__":
    settings = get_settings()
    
    # Check if SSL certificates exist
    ssl_keyfile = os.environ.get("SSL_KEYFILE", "/app/certs/privkey.pem")
    ssl_certfile = os.environ.get("SSL_CERTFILE", "/app/certs/fullchain.pem")
    
    # Check if SSL certificates exist and have proper content
    ssl_enabled = False
    try:
        if os.path.exists(ssl_keyfile) and os.path.exists(ssl_certfile):
            # Verify certificate files are not empty
            if os.path.getsize(ssl_keyfile) > 0 and os.path.getsize(ssl_certfile) > 0:
                ssl_enabled = True
            else:
                print("SSL certificates exist but are empty")
        else:
            print(f"SSL certificates not found: {ssl_keyfile} or {ssl_certfile}")
    except Exception as e:
        print(f"Error checking SSL certificates: {str(e)}")
    
    # Configure the port based on environment variable or default
    port = int(os.environ.get("PORT", 8100))
    ssl_port = int(os.environ.get("SSL_PORT", 8443))
    
    if ssl_enabled:
        # Run with SSL
        print(f"Running with HTTPS on port {ssl_port}")
        uvicorn.run(
            "app.main:app", 
            host="0.0.0.0", 
            port=ssl_port, 
            reload=True,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile
        )
    else:
        # Run without SSL
        print("SSL certificates not found or invalid, running without HTTPS")
        print("Warning: Microphone access requires HTTPS in modern browsers")
        uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)