"""Admin endpoints: audit log viewer (admin only)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from ..models.base import get_db
from ..models.scan import AuditLog
from ..core.security import require_role
from ..models.user import UserRole

router = APIRouter(prefix="/admin", tags=["admin"])


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    ip_address: Optional[str]
    request_method: Optional[str]
    request_path: Optional[str]
    created_at: datetime


@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    since: Optional[datetime] = Query(None, description="Filter records after this datetime"),
    until: Optional[datetime] = Query(None, description="Filter records before this datetime"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _admin=Depends(require_role(UserRole.ADMIN)),
):
    """Searchable audit log — admin only. Filterable by user, date range, action type."""
    q = db.query(AuditLog)
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    if action:
        q = q.filter(AuditLog.action == action)
    if resource_type:
        q = q.filter(AuditLog.resource_type == resource_type)
    if since:
        q = q.filter(AuditLog.created_at >= since)
    if until:
        q = q.filter(AuditLog.created_at <= until)
    return q.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
