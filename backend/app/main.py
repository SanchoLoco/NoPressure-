"""
NoPressure - Wound Scanning & Skin Condition Monitoring API
HIPAA/GDPR compliant wound management platform.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models.base import Base, engine
from .models import alert  # Ensure Alert tables are registered
from .api import patients, wounds, scans, analytics, auth, alerts, admin
from .core.audit_middleware import AuditMiddleware
from .seed_demo import seed_demo_data

# Create all database tables
# NOTE: In production, use Alembic migrations instead of create_all()
Base.metadata.create_all(bind=engine)

# Seed demo users and sample data (idempotent)
seed_demo_data()

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
    allow_origins=["*"],  # TODO: Restrict to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuditMiddleware)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(patients.router, prefix="/api/v1")
app.include_router(wounds.router, prefix="/api/v1")
app.include_router(scans.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "NoPressure API", "version": "1.0.0"}
