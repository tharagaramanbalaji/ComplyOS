from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import magic
from api.core.dependencies import get_parser

app = FastAPI(
    title="ComplyOS Validation API",
    description="The backend engine for NLP parsing, XSLT compilation, and XML validation.",
    version="1.0.0"
)

# CRITICAL: This allows our React Frontend (Phase 5) to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all ports for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("🚀 Booting up ComplyOS Backend...")
    # Pre-load the AI models so the very first API request doesn't lag the frontend
    get_parser()

# Include the endpoints
app.include_router(magic.router, prefix="/api/validate", tags=["Validation Engine"])

@app.get("/")
def health_check():
    return {"status": "online", "message": "ComplyOS Engine is actively listening."}
