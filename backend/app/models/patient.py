from sqlalchemy import Column, String, Date, Text, Boolean
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin, generate_uuid


class Patient(Base, TimestampMixin):
    __tablename__ = "patients"

    id = Column(String, primary_key=True, default=generate_uuid)
    # PHI fields - encrypted at rest in production
    mrn = Column(String(50), unique=True, nullable=False, index=True)  # Medical Record Number
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    facility_id = Column(String(50), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    wounds = relationship("Wound", back_populates="patient", cascade="all, delete-orphan")
