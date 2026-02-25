from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from ..models.base import get_db
from ..models.wound import Wound
from ..models.scan import Scan
from ..services.analytics import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


class HealingTrendResponse(BaseModel):
    wound_id: str
    baseline_area_cm2: float
    current_area_cm2: float
    par_percentage: float
    days_elapsed: int
    is_stalled: bool
    trend_direction: str
    projected_healing_days: Optional[int]


class FacilityDashboardResponse(BaseModel):
    facility_id: str
    total_wounds: int
    active_wounds: int
    stalled_wounds: int
    wound_by_etiology: dict


@router.get("/wound/{wound_id}/trend", response_model=HealingTrendResponse)
def get_healing_trend(wound_id: str, db: Session = Depends(get_db)):
    """
    Calculate healing trend for a wound.
    Triggers stalled wound alert if PAR < 20% over 4 weeks.
    """
    scans = (
        db.query(Scan)
        .filter(Scan.wound_id == wound_id)
        .order_by(Scan.created_at)
        .all()
    )
    if not scans:
        raise HTTPException(status_code=404, detail="No scans found for this wound")

    scan_dicts = [
        {"area_cm2": s.area_cm2, "created_at": s.created_at}
        for s in scans
    ]

    trend = analytics_service.calculate_healing_trend(wound_id, scan_dicts)

    return HealingTrendResponse(
        wound_id=trend.wound_id,
        baseline_area_cm2=trend.baseline_area_cm2,
        current_area_cm2=trend.current_area_cm2,
        par_percentage=trend.par_percentage,
        days_elapsed=trend.days_elapsed,
        is_stalled=trend.is_stalled,
        trend_direction=trend.trend_direction,
        projected_healing_days=trend.projected_healing_days,
    )


@router.get("/facility/{facility_id}/dashboard", response_model=FacilityDashboardResponse)
def get_facility_dashboard(facility_id: str, db: Session = Depends(get_db)):
    """
    Centralized command center for head nurses/physicians.
    Shows entire facility wound burden at a glance.
    """
    from ..models.patient import Patient
    from ..models.wound import WoundStatus

    patients = db.query(Patient).filter(Patient.facility_id == facility_id).all()
    patient_ids = [p.id for p in patients]

    all_wounds = db.query(Wound).filter(Wound.patient_id.in_(patient_ids)).all()
    active_wounds = [w for w in all_wounds if w.status == WoundStatus.ACTIVE]
    stalled_wounds = [w for w in all_wounds if w.is_stalled]

    etiology_counts = {}
    for wound in all_wounds:
        etiology_counts[wound.etiology] = etiology_counts.get(wound.etiology, 0) + 1

    return FacilityDashboardResponse(
        facility_id=facility_id,
        total_wounds=len(all_wounds),
        active_wounds=len(active_wounds),
        stalled_wounds=len(stalled_wounds),
        wound_by_etiology=etiology_counts,
    )
