"""
Demo data seeder for NoPressure.

Creates a demo admin user and a demo physician user with known credentials,
plus a sample patient and wound record so the happy-flow walkthrough works
immediately after a fresh start.

Credentials (printed to stdout on first run):
  Admin    : admin@nopressure.demo  / Admin1234!
  Physician: demo@nopressure.demo   / Demo1234!

This seeder is idempotent — it is safe to call on every startup.
"""
from datetime import date

from .models.base import SessionLocal, Base, engine, generate_uuid
from .models.user import User, UserRole
from .models.patient import Patient
from .models.wound import Wound, WoundEtiology, AnatomicalLocation
from .core.security import get_password_hash

DEMO_FACILITY_ID = "demo-facility-1"

DEMO_ADMIN_EMAIL = "admin@nopressure.demo"
DEMO_ADMIN_USERNAME = "admin_demo"
DEMO_ADMIN_PASSWORD = "Admin1234!"

DEMO_PHYSICIAN_EMAIL = "demo@nopressure.demo"
DEMO_PHYSICIAN_USERNAME = "demo_physician"
DEMO_PHYSICIAN_PASSWORD = "Demo1234!"

DEMO_PATIENT_MRN = "DEMO-MRN-001"


def seed_demo_data() -> None:
    """Create demo users, patient, and wound if they do not already exist."""
    # Ensure tables exist (no-op when already created by main.py)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        _seed_users(db)
        patient = _seed_patient(db)
        _seed_wound(db, patient.id)
    finally:
        db.close()


# ── helpers ──────────────────────────────────────────────────────────────────

def _seed_users(db) -> None:
    # Admin user
    if not db.query(User).filter(User.email == DEMO_ADMIN_EMAIL).first():
        admin = User(
            id=generate_uuid(),
            email=DEMO_ADMIN_EMAIL,
            username=DEMO_ADMIN_USERNAME,
            hashed_password=get_password_hash(DEMO_ADMIN_PASSWORD),
            full_name="Demo Admin",
            role=UserRole.ADMIN,
            facility_id=DEMO_FACILITY_ID,
        )
        db.add(admin)
        db.commit()
        print(f"[seed] Created demo admin  : {DEMO_ADMIN_EMAIL} / {DEMO_ADMIN_PASSWORD}")

    # Physician / presenter user
    if not db.query(User).filter(User.email == DEMO_PHYSICIAN_EMAIL).first():
        physician = User(
            id=generate_uuid(),
            email=DEMO_PHYSICIAN_EMAIL,
            username=DEMO_PHYSICIAN_USERNAME,
            hashed_password=get_password_hash(DEMO_PHYSICIAN_PASSWORD),
            full_name="Demo Physician",
            role=UserRole.PHYSICIAN,
            facility_id=DEMO_FACILITY_ID,
            license_number="DEMO-LIC-001",
        )
        db.add(physician)
        db.commit()
        print(f"[seed] Created demo user   : {DEMO_PHYSICIAN_EMAIL} / {DEMO_PHYSICIAN_PASSWORD}")


def _seed_patient(db) -> Patient:
    patient = db.query(Patient).filter(Patient.mrn == DEMO_PATIENT_MRN).first()
    if not patient:
        patient = Patient(
            id=generate_uuid(),
            mrn=DEMO_PATIENT_MRN,
            first_name="John",
            last_name="Demo",
            date_of_birth=date(1960, 6, 15),
            gender="male",
            facility_id=DEMO_FACILITY_ID,
            notes="Pre-seeded demo patient for presentation purposes.",
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
        print(f"[seed] Created demo patient: {patient.first_name} {patient.last_name} (MRN: {patient.mrn})")
    return patient


def _seed_wound(db, patient_id: str) -> None:
    existing = db.query(Wound).filter(Wound.patient_id == patient_id).first()
    if not existing:
        wound = Wound(
            id=generate_uuid(),
            patient_id=patient_id,
            etiology=WoundEtiology.DIABETIC_FOOT_ULCER,
            body_location=AnatomicalLocation.LEFT_HEEL,
            body_side="left",
            notes="Pre-seeded demo wound — diabetic foot ulcer, left heel.",
        )
        db.add(wound)
        db.commit()
        print(f"[seed] Created demo wound  : {wound.etiology} @ {wound.body_location} (id: {wound.id})")
