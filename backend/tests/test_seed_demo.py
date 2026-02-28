"""Tests for the demo data seeder."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import all models so SQLAlchemy mapper relationships resolve correctly
from app.models.base import Base
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.wound import Wound
import app.models.scan  # noqa: F401 — ensures Scan mapper is registered
import app.models.alert  # noqa: F401 — ensures Alert mapper is registered
from app.seed_demo import (
    seed_demo_data,
    DEMO_ADMIN_EMAIL,
    DEMO_PHYSICIAN_EMAIL,
    DEMO_PATIENT_MRN,
    DEMO_FACILITY_ID,
)


@pytest.fixture()
def in_memory_db(monkeypatch):
    """Provide an isolated in-memory SQLite database for each test."""
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    # Patch the module-level engine/SessionLocal used inside seed_demo
    import app.seed_demo as sd
    import app.models.base as mb

    monkeypatch.setattr(sd, "engine", test_engine)
    monkeypatch.setattr(sd, "SessionLocal", TestSession)
    monkeypatch.setattr(mb, "engine", test_engine)
    monkeypatch.setattr(mb, "SessionLocal", TestSession)

    db = TestSession()
    yield db
    db.close()


class TestSeedDemoData:
    def test_creates_admin_user(self, in_memory_db):
        seed_demo_data()
        admin = in_memory_db.query(User).filter(User.email == DEMO_ADMIN_EMAIL).first()
        assert admin is not None
        assert admin.role == UserRole.ADMIN
        assert admin.facility_id == DEMO_FACILITY_ID

    def test_creates_physician_user(self, in_memory_db):
        seed_demo_data()
        physician = in_memory_db.query(User).filter(User.email == DEMO_PHYSICIAN_EMAIL).first()
        assert physician is not None
        assert physician.role == UserRole.PHYSICIAN

    def test_creates_demo_patient(self, in_memory_db):
        seed_demo_data()
        patient = in_memory_db.query(Patient).filter(Patient.mrn == DEMO_PATIENT_MRN).first()
        assert patient is not None
        assert patient.first_name == "John"
        assert patient.last_name == "Demo"
        assert patient.facility_id == DEMO_FACILITY_ID

    def test_creates_demo_wound(self, in_memory_db):
        seed_demo_data()
        patient = in_memory_db.query(Patient).filter(Patient.mrn == DEMO_PATIENT_MRN).first()
        wound = in_memory_db.query(Wound).filter(Wound.patient_id == patient.id).first()
        assert wound is not None
        assert wound.etiology == "diabetic_foot_ulcer"
        assert wound.body_location == "left_heel"

    def test_idempotent_on_second_call(self, in_memory_db):
        """Calling seed_demo_data twice must not create duplicate records."""
        seed_demo_data()
        seed_demo_data()
        admin_count = in_memory_db.query(User).filter(User.email == DEMO_ADMIN_EMAIL).count()
        physician_count = in_memory_db.query(User).filter(User.email == DEMO_PHYSICIAN_EMAIL).count()
        patient_count = in_memory_db.query(Patient).filter(Patient.mrn == DEMO_PATIENT_MRN).count()
        assert admin_count == 1
        assert physician_count == 1
        assert patient_count == 1

    def test_demo_passwords_are_hashed(self, in_memory_db):
        """Passwords must be stored as bcrypt hashes, not plain text."""
        seed_demo_data()
        from app.core.security import verify_password
        from app.seed_demo import DEMO_ADMIN_PASSWORD, DEMO_PHYSICIAN_PASSWORD

        admin = in_memory_db.query(User).filter(User.email == DEMO_ADMIN_EMAIL).first()
        physician = in_memory_db.query(User).filter(User.email == DEMO_PHYSICIAN_EMAIL).first()

        assert verify_password(DEMO_ADMIN_PASSWORD, admin.hashed_password)
        assert verify_password(DEMO_PHYSICIAN_PASSWORD, physician.hashed_password)
