from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from ..models.base import get_db
from ..models.scan import Scan, AuditLog
from ..models.wound import Wound, WoundStatus
from ..models.base import generate_uuid
from ..services.ai_engine import ai_engine
from ..services.treatment_engine import treatment_engine
from ..services.analytics import analytics_service
from ..core.config import settings

router = APIRouter(prefix="/scans", tags=["scans"])


class ScanResponse(BaseModel):
    id: str
    wound_id: str
    scanned_by: str
    length_cm: Optional[float]
    width_cm: Optional[float]
    depth_cm: Optional[float]
    area_cm2: Optional[float]
    tissue_granulation_pct: Optional[float]
    tissue_slough_pct: Optional[float]
    tissue_eschar_pct: Optional[float]
    exudate_level: Optional[str]
    treatment_recommendation: Optional[dict]
    dressing_recommendation: Optional[str]
    par_from_baseline: Optional[float]
    sub_epidermal_risk: bool
    clinical_notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/{wound_id}/scan", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    wound_id: str,
    scanned_by: str = Form(...),
    capture_angle: float = Form(90.0),
    has_calibration_marker: bool = Form(True),
    clinical_notes: Optional[str] = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Create a new wound scan with AI analysis.
    Image is never stored to device gallery (zero-footprint).
    """
    wound = db.query(Wound).filter(Wound.id == wound_id).first()
    if not wound:
        raise HTTPException(status_code=404, detail="Wound not found")

    # Read image data
    image_data = await image.read()

    # Run AI analysis
    try:
        analysis = ai_engine.analyze_wound_image(
            image_data=image_data,
            has_calibration_marker=has_calibration_marker,
            capture_angle=capture_angle,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Get previous scans for PAR calculation
    previous_scans = db.query(Scan).filter(Scan.wound_id == wound_id).order_by(Scan.created_at).all()
    par = None
    if previous_scans:
        baseline = previous_scans[0]
        if baseline.area_cm2:
            par = ai_engine.calculate_par(baseline.area_cm2, analysis.measurements.area_cm2)

    # Get treatment recommendation
    rec = treatment_engine.recommend(
        granulation_pct=analysis.tissue.granulation_pct,
        slough_pct=analysis.tissue.slough_pct,
        eschar_pct=analysis.tissue.eschar_pct,
        exudate_level=analysis.exudate_level,
        etiology=wound.etiology,
        is_stalled=wound.is_stalled,
        sub_epidermal_risk=analysis.sub_epidermal.risk_level,
    )

    # Create scan record
    scan = Scan(
        id=generate_uuid(),
        wound_id=wound_id,
        scanned_by=scanned_by,
        length_cm=analysis.measurements.length_cm,
        width_cm=analysis.measurements.width_cm,
        depth_cm=analysis.measurements.depth_cm,
        area_cm2=analysis.measurements.area_cm2,
        volume_cm3=analysis.measurements.volume_cm3,
        measurement_error_pct=analysis.measurements.measurement_error_pct,
        tissue_granulation_pct=analysis.tissue.granulation_pct,
        tissue_slough_pct=analysis.tissue.slough_pct,
        tissue_eschar_pct=analysis.tissue.eschar_pct,
        tissue_epithelial_pct=analysis.tissue.epithelial_pct,
        exudate_level=analysis.exudate_level,
        exudate_type=analysis.exudate_type,
        periwound_condition=analysis.periwound_condition,
        sub_epidermal_risk=analysis.sub_epidermal.risk_level != "none",
        temperature_delta=analysis.sub_epidermal.temperature_delta_celsius,
        calibration_marker_detected=analysis.calibration_marker_detected,
        capture_angle_degrees=analysis.capture_angle_degrees,
        par_from_baseline=par,
        clinical_notes=clinical_notes,
        treatment_recommendation={
            "primary_dressing": rec.primary_dressing,
            "interventions": rec.interventions,
            "rationale": rec.rationale,
            "urgency": rec.urgency,
        },
        dressing_recommendation=rec.primary_dressing,
    )
    db.add(scan)

    # Check if wound is stalled (after 4 weeks with <20% PAR)
    if par is not None and previous_scans:
        from ..models.scan import Scan as ScanModel
        baseline_scan = previous_scans[0]
        days = (datetime.utcnow() - baseline_scan.created_at).days
        if ai_engine.is_wound_stalled(par, days):
            wound.is_stalled = True
            wound.status = WoundStatus.STALLED

    # Audit log (HIPAA compliance)
    audit = AuditLog(
        id=generate_uuid(),
        scan_id=scan.id,
        user_id=scanned_by,
        action="create",
        resource_type="scan",
        resource_id=scan.id,
    )
    db.add(audit)

    db.commit()
    db.refresh(scan)
    return scan


@router.get("/{scan_id}", response_model=ScanResponse)
def get_scan(scan_id: str, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.get("/wound/{wound_id}", response_model=List[ScanResponse])
def get_wound_scans(wound_id: str, db: Session = Depends(get_db)):
    """Get all scans for a wound - supports time-lapse comparison."""
    return db.query(Scan).filter(Scan.wound_id == wound_id).order_by(Scan.created_at).all()
