from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import date
from ..models.base import get_db
from ..models.patient import Patient
from ..models.base import generate_uuid

router = APIRouter(prefix="/patients", tags=["patients"])


class PatientCreate(BaseModel):
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    facility_id: Optional[str] = None
    notes: Optional[str] = None


class PatientResponse(BaseModel):
    id: str
    mrn: str
    first_name: str
    last_name: str
    facility_id: Optional[str]

    class Config:
        from_attributes = True


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(patient_in: PatientCreate, db: Session = Depends(get_db)):
    existing = db.query(Patient).filter(Patient.mrn == patient_in.mrn).first()
    if existing:
        raise HTTPException(status_code=400, detail="Patient MRN already exists")
    patient = Patient(id=generate_uuid(), **patient_in.dict())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.get("/", response_model=List[PatientResponse])
def list_patients(
    facility_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(Patient).filter(Patient.is_active == True)
    if facility_id:
        q = q.filter(Patient.facility_id == facility_id)
    return q.offset(skip).limit(limit).all()
