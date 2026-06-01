import os
import django
import sys

# Add project root directory to python path if not present
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Setup Django ORM context before importing any models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SWMM.settings")
django.setup()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers after django.setup() is done
from fast_api.routers import cmms

app = FastAPI(
    title="SWMM CMMS Integration APIs",
    description="FastAPI endpoints for external applications to interface with the CMMS module.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for developer access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api namespace
app.include_router(cmms.router, prefix="/api")

@app.get("/", tags=["Root"])
async def root():
    return {
        "title": "SWMM External Integration APIs",
        "description": "FastAPI server running alongside Django",
        "docs_url": "/docs",
        "status": "online"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fast_api.main:app", host="0.0.0.0", port=8001, reload=True)
