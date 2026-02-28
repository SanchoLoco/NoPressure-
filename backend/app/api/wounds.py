from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from ..models.base import get_db
from ..models.wound import Wound, WoundEtiology, WoundStatus, AnatomicalLocation
from ..models.scan import Scan
from ..models.base import generate_uuid
from ..core.security import get_current_user
from ..core.permissions import PERM_VIEW_PATIENT_LEVEL_DATA, has_permission

router = APIRouter(prefix="/wounds", tags=["wounds"])


class WoundCreate(BaseModel):
    patient_id: str
    etiology: str = WoundEtiology.OTHER
    body_location: Optional[str] = None
    body_side: Optional[str] = None
    body_coordinates: Optional[Dict] = None
    notes: Optional[str] = None


class WoundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    etiology: str
    status: str
    body_location: Optional[str]
    body_side: Optional[str]
    body_coordinates: Optional[Dict]
    is_stalled: bool


class WoundSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    etiology: str
    status: str
    body_location: Optional[str]
    is_stalled: bool
    latest_severity_score: Optional[float]
    latest_stage: Optional[str]
    last_assessment_date: Optional[datetime]


def _require_patient_access(current_user):
    if not has_permission(current_user.role, PERM_VIEW_PATIENT_LEVEL_DATA):
        raise HTTPException(status_code=403, detail="Insufficient permissions to access wound data")


@router.post("/", response_model=WoundResponse, status_code=status.HTTP_201_CREATED)
def create_wound(
    wound_in: WoundCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _require_patient_access(current_user)
    if wound_in.etiology not in WoundEtiology.ALL:
        raise HTTPException(status_code=400, detail=f"Invalid etiology. Choose from: {WoundEtiology.ALL}")
    if wound_in.body_location and wound_in.body_location not in AnatomicalLocation.ALL:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid anatomical location. Choose from: {AnatomicalLocation.ALL}",
        )
    wound = Wound(id=generate_uuid(), **wound_in.dict())
    db.add(wound)
    db.commit()
    db.refresh(wound)
    return wound


@router.get("/patient/{patient_id}/summary", response_model=List[WoundSummaryResponse])
def get_patient_wounds_summary(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Returns wound list enriched with latest scan data (severity, stage, last assessment date)."""
    _require_patient_access(current_user)
    wounds = db.query(Wound).filter(Wound.patient_id == patient_id).all()
    summaries = []
    for wound in wounds:
        latest_scan = (
            db.query(Scan)
            .filter(Scan.wound_id == wound.id)
            .order_by(Scan.created_at.desc())
            .first()
        )
        summaries.append(
            WoundSummaryResponse(
                id=wound.id,
                patient_id=wound.patient_id,
                etiology=wound.etiology,
                status=wound.status,
                body_location=wound.body_location,
                is_stalled=wound.is_stalled,
                latest_severity_score=latest_scan.severity_score if latest_scan else None,
                latest_stage=latest_scan.stage_classification if latest_scan else None,
                last_assessment_date=latest_scan.created_at if latest_scan else None,
            )
        )
    return summaries


@router.get("/{wound_id}", response_model=WoundResponse)
def get_wound(
    wound_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _require_patient_access(current_user)
    wound = db.query(Wound).filter(Wound.id == wound_id).first()
    if not wound:
        raise HTTPException(status_code=404, detail="Wound not found")
    return wound


@router.get("/patient/{patient_id}", response_model=List[WoundResponse])
def get_patient_wounds(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _require_patient_access(current_user)
    return db.query(Wound).filter(Wound.patient_id == patient_id).all()


@router.patch("/{wound_id}/location")
def update_wound_location(
    wound_id: str,
    body_location: str,
    body_side: Optional[str] = None,
    x_coord: Optional[float] = None,
    y_coord: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update wound location on body map."""
    _require_patient_access(current_user)
    wound = db.query(Wound).filter(Wound.id == wound_id).first()
    if not wound:
        raise HTTPException(status_code=404, detail="Wound not found")
    if body_location not in AnatomicalLocation.ALL:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid anatomical location. Choose from: {AnatomicalLocation.ALL}",
        )
    wound.body_location = body_location
    wound.body_side = body_side
    if x_coord is not None and y_coord is not None:
        wound.body_coordinates = {"x": x_coord, "y": y_coord}
    db.commit()
    return {"status": "updated"}
