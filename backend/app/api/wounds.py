from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from pydantic import BaseModel
from ..models.base import get_db
from ..models.wound import Wound, WoundEtiology, WoundStatus
from ..models.base import generate_uuid

router = APIRouter(prefix="/wounds", tags=["wounds"])


class WoundCreate(BaseModel):
    patient_id: str
    etiology: str = WoundEtiology.OTHER
    body_location: Optional[str] = None
    body_side: Optional[str] = None
    body_coordinates: Optional[Dict] = None
    notes: Optional[str] = None


class WoundResponse(BaseModel):
    id: str
    patient_id: str
    etiology: str
    status: str
    body_location: Optional[str]
    body_side: Optional[str]
    body_coordinates: Optional[Dict]
    is_stalled: bool

    class Config:
        from_attributes = True


@router.post("/", response_model=WoundResponse, status_code=status.HTTP_201_CREATED)
def create_wound(wound_in: WoundCreate, db: Session = Depends(get_db)):
    if wound_in.etiology not in WoundEtiology.ALL:
        raise HTTPException(status_code=400, detail=f"Invalid etiology. Choose from: {WoundEtiology.ALL}")
    wound = Wound(id=generate_uuid(), **wound_in.dict())
    db.add(wound)
    db.commit()
    db.refresh(wound)
    return wound


@router.get("/{wound_id}", response_model=WoundResponse)
def get_wound(wound_id: str, db: Session = Depends(get_db)):
    wound = db.query(Wound).filter(Wound.id == wound_id).first()
    if not wound:
        raise HTTPException(status_code=404, detail="Wound not found")
    return wound


@router.get("/patient/{patient_id}", response_model=List[WoundResponse])
def get_patient_wounds(patient_id: str, db: Session = Depends(get_db)):
    return db.query(Wound).filter(Wound.patient_id == patient_id).all()


@router.patch("/{wound_id}/location")
def update_wound_location(
    wound_id: str,
    body_location: str,
    body_side: Optional[str] = None,
    x_coord: Optional[float] = None,
    y_coord: Optional[float] = None,
    db: Session = Depends(get_db),
):
    """Update wound location on body map."""
    wound = db.query(Wound).filter(Wound.id == wound_id).first()
    if not wound:
        raise HTTPException(status_code=404, detail="Wound not found")
    wound.body_location = body_location
    wound.body_side = body_side
    if x_coord is not None and y_coord is not None:
        wound.body_coordinates = {"x": x_coord, "y": y_coord}
    db.commit()
    return {"status": "updated"}
