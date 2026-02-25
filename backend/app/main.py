"""
NoPressure - Wound Scanning & Skin Condition Monitoring API
HIPAA/GDPR compliant wound management platform.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models.base import Base, engine
from .api import patients, wounds, scans, analytics

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NoPressure Wound Management API",
    description=(
        "Digitally wound-scanning and skin-condition monitoring solution. "
        "HIPAA/GDPR compliant with AI-powered tissue segmentation, "
        "3D volumetric measurement, and EHR/FHIR integration."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patients.router, prefix="/api/v1")
app.include_router(wounds.router, prefix="/api/v1")
app.include_router(scans.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "NoPressure API", "version": "1.0.0"}
