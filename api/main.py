from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import magic
from api.core.dependencies import get_parser

app = FastAPI(
    title="ComplyOS Validation API",
    description="The backend engine for NLP parsing, XSLT compilation, and XML validation.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("[ComplyOS] Booting up backend server instantly (Models will lazy-load on first API call)...")

import os
from fastapi.staticfiles import StaticFiles

# Include the endpoints
app.include_router(magic.router, prefix="/api/validate", tags=["Validation Engine"])

@app.get("/health")
def health_check():
    return {"status": "online", "message": "ComplyOS Engine is actively listening."}

# Mount React static files if built (Production deployment)
if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
else:
    @app.get("/")
    def root_fallback():
        return {"status": "online", "message": "ComplyOS API is running (Frontend static assets not built)."}
