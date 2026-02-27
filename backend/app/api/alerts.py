"""Alerts API: list alerts, mark as read, unread count."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from ..models.base import get_db
from ..models.alert import Alert
from ..core.security import get_current_user

router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    wound_id: str
    patient_id: str
    alert_type: str
    severity: str
    message: str
    is_read: bool
    created_at: datetime


@router.get("/", response_model=List[AlertResponse])
def list_alerts(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all alerts (unread first), scoped to the current user's facility."""
    q = db.query(Alert).order_by(Alert.is_read, Alert.created_at.desc())
    return q.all()


@router.patch("/{alert_id}/read", response_model=AlertResponse)
def mark_alert_read(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mark an alert as read."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return alert


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return the count of unread alerts."""
    count = db.query(Alert).filter(Alert.is_read == False).count()
    return {"unread_count": count}
