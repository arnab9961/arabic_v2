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
    
    ssl_enabled = os.path.exists(ssl_keyfile) and os.path.exists(ssl_certfile)
    
    if ssl_enabled:
        # Run with SSL
        uvicorn.run(
            "app.main:app", 
            host="0.0.0.0", 
            port=8100, 
            reload=True,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile
        )
    else:
        # Run without SSL
        print("SSL certificates not found, running without HTTPS")
        uvicorn.run("app.main:app", host="0.0.0.0", port=8100, reload=True)