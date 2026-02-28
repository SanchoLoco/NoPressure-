from typing import Optional
from sqlalchemy import Column, String, Float, Text, Boolean, ForeignKey, JSON, Integer, DateTime
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin, generate_uuid


class TissueType:
    GRANULATION = "granulation"    # Red - healthy healing
    SLOUGH = "slough"              # Yellow - fibrinous, needs debridement
    ESCHAR = "eschar"              # Black/necrotic - dead tissue
    EPITHELIAL = "epithelial"      # Pink - new skin
    HYPERGRANULATION = "hypergranulation"


class Scan(Base, TimestampMixin):
    __tablename__ = "scans"

    id = Column(String, primary_key=True, default=generate_uuid)
    wound_id = Column(String, ForeignKey("wounds.id"), nullable=False, index=True)
    scanned_by = Column(String(100), nullable=False)  # User ID

    # 3D Measurements (photogrammetry/LiDAR)
    length_cm = Column(Float, nullable=True)
    width_cm = Column(Float, nullable=True)
    depth_cm = Column(Float, nullable=True)
    area_cm2 = Column(Float, nullable=True)
    volume_cm3 = Column(Float, nullable=True)
    measurement_error_pct = Column(Float, nullable=True)  # Must be <5%

    # AI tissue segmentation results (percentages 0-100)
    tissue_granulation_pct = Column(Float, nullable=True)
    tissue_slough_pct = Column(Float, nullable=True)
    tissue_eschar_pct = Column(Float, nullable=True)
    tissue_epithelial_pct = Column(Float, nullable=True)

    # Exudate assessment
    exudate_level = Column(String(20), nullable=True)  # none, low, moderate, high
    exudate_type = Column(String(50), nullable=True)   # serous, serosanguineous, purulent

    # Periwound condition
    periwound_condition = Column(String(200), nullable=True)

    # Image storage (zero-footprint - stored in secure cloud)
    image_url = Column(String(500), nullable=True)  # Encrypted cloud URL
    image_hash = Column(String(64), nullable=True)  # SHA-256 for integrity

    # Sub-epidermal analysis
    sub_epidermal_risk = Column(Boolean, default=False)
    temperature_delta = Column(Float, nullable=True)  # Thermal sensor data

    # Treatment recommendation
    treatment_recommendation = Column(JSON, nullable=True)
    dressing_recommendation = Column(String(200), nullable=True)

    # Clinical notes (voice-to-text)
    clinical_notes = Column(Text, nullable=True)

    # Calibration
    calibration_marker_detected = Column(Boolean, default=False)
    capture_angle_degrees = Column(Float, nullable=True)  # Should be ~90

    # Healing progress
    par_from_baseline = Column(Float, nullable=True)  # Percentage Area Reduction from first scan

    # External classifier results (FDA/SaMD traceability)
    severity_score = Column(Float, nullable=True)       # Continuous score e.g. 2.7
    stage_classification = Column(String(20), nullable=True)  # "Stage 1" through "Stage 4"
    ai_confidence = Column(Float, nullable=True)        # 0.0-1.0
    model_version = Column(String(50), nullable=True)   # Version of the classifier model

    # Clinician confirmation / override
    clinician_confirmed = Column(Boolean, default=False)
    confirmed_by = Column(String(100), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    override_reason = Column(Text, nullable=True)
    override_severity_score = Column(Float, nullable=True)
    override_stage = Column(String(20), nullable=True)

    wound = relationship("Wound", back_populates="scans")
    audit_logs = relationship("AuditLog", back_populates="scan", cascade="all, delete-orphan")

    @property
    def npiap_stage(self) -> Optional[int]:
        if hasattr(self, "_npiap_stage"):
            return getattr(self, "_npiap_stage")
        if self.stage_classification and self.stage_classification.lower().startswith("stage"):
            try:
                return int(self.stage_classification.split()[-1])
            except Exception:
                return None
        return None

    @npiap_stage.setter
    def npiap_stage(self, value):
        self._npiap_stage = value

    @property
    def sub_severity_score(self) -> Optional[float]:
        return getattr(self, "_sub_severity_score", self.severity_score)

    @sub_severity_score.setter
    def sub_severity_score(self, value):
        self._sub_severity_score = value

    @property
    def severity_color(self) -> Optional[str]:
        if hasattr(self, "_severity_color"):
            return getattr(self, "_severity_color")
        return self._map_color(self.sub_severity_score)

    @severity_color.setter
    def severity_color(self, value):
        self._severity_color = value

    @staticmethod
    def _map_color(score: Optional[float]) -> Optional[str]:
        if score is None:
            return None
        if score >= 3.0:
            return "red"
        if score >= 2.0:
            return "orange"
        if score >= 1.0:
            return "green"
        return None


class AuditLog(Base, TimestampMixin):
    """HIPAA-compliant audit trail for all scan actions."""
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    scan_id = Column(String, ForeignKey("scans.id"), nullable=True, index=True)
    user_id = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)  # create, view, update, delete
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String, nullable=False)
    ip_address = Column(String(45), nullable=True)
    request_method = Column(String(10), nullable=True)
    request_path = Column(String(500), nullable=True)
    user_agent = Column(String(500), nullable=True)
    changes = Column(JSON, nullable=True)

    scan = relationship("Scan", back_populates="audit_logs")
