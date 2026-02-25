from sqlalchemy import Column, String, Float, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin, generate_uuid


class WoundEtiology:
    DIABETIC_FOOT_ULCER = "diabetic_foot_ulcer"
    VENOUS_LEG_ULCER = "venous_leg_ulcer"
    PRESSURE_ULCER = "pressure_ulcer"
    SURGICAL_SITE = "surgical_site_infection"
    ARTERIAL_ULCER = "arterial_ulcer"
    TRAUMATIC = "traumatic"
    BURN = "burn"
    OTHER = "other"

    ALL = [
        DIABETIC_FOOT_ULCER, VENOUS_LEG_ULCER, PRESSURE_ULCER,
        SURGICAL_SITE, ARTERIAL_ULCER, TRAUMATIC, BURN, OTHER
    ]


class WoundStatus:
    ACTIVE = "active"
    HEALING = "healing"
    STALLED = "stalled"
    HEALED = "healed"
    DETERIORATING = "deteriorating"


class Wound(Base, TimestampMixin):
    __tablename__ = "wounds"

    id = Column(String, primary_key=True, default=generate_uuid)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    etiology = Column(String(50), nullable=False, default=WoundEtiology.OTHER)
    status = Column(String(20), nullable=False, default=WoundStatus.ACTIVE)

    # Body map location
    body_location = Column(String(100), nullable=True)  # e.g., "left_heel", "sacrum"
    body_side = Column(String(10), nullable=True)  # "left", "right", "midline"
    body_coordinates = Column(JSON, nullable=True)  # {x: float, y: float} on anatomical map

    is_stalled = Column(Boolean, default=False)
    stalled_alert_sent = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    patient = relationship("Patient", back_populates="wounds")
    scans = relationship("Scan", back_populates="wound", cascade="all, delete-orphan", order_by="Scan.created_at")
