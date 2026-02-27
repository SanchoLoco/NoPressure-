from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import date
from ..models.base import get_db
from ..models.patient import Patient
from ..models.base import generate_uuid
from ..core.security import get_current_user
from ..core.permissions import PERM_VIEW_PATIENT_LEVEL_DATA, has_permission

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
    model_config = ConfigDict(from_attributes=True)

    id: str
    mrn: str
    first_name: str
    last_name: str
    facility_id: Optional[str]


def _require_patient_access(current_user):
    if not has_permission(current_user.role, PERM_VIEW_PATIENT_LEVEL_DATA):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Insufficient permissions to access patient data")


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(
    patient_in: PatientCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _require_patient_access(current_user)
    existing = db.query(Patient).filter(Patient.mrn == patient_in.mrn).first()
    if existing:
        raise HTTPException(status_code=400, detail="Patient MRN already exists")
    patient = Patient(id=generate_uuid(), **patient_in.dict())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/search", response_model=List[PatientResponse])
def search_patients(
    q: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Search patients by name or MRN."""
    _require_patient_access(current_user)
    term = f"%{q}%"
    results = (
        db.query(Patient)
        .filter(Patient.is_active == True)
        .filter(
            Patient.mrn.ilike(term)
            | Patient.first_name.ilike(term)
            | Patient.last_name.ilike(term)
        )
        .limit(50)
        .all()
    )
    return results


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _require_patient_access(current_user)
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
    current_user=Depends(get_current_user),
):
    _require_patient_access(current_user)
    q = db.query(Patient).filter(Patient.is_active == True)
    if facility_id:
        q = q.filter(Patient.facility_id == facility_id)
    return q.offset(skip).limit(limit).all()
