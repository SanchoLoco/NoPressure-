"""Authentication endpoints: register, login, refresh, me, change password."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from ..models.base import get_db, generate_uuid
from ..models.user import User, UserRole
from ..core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    get_current_user,
    require_role,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Request / Response schemas ──────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    full_name: Optional[str] = None
    role: str = UserRole.NURSE
    facility_id: Optional[str] = None
    license_number: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    username: str
    full_name: Optional[str]
    role: str
    facility_id: Optional[str]
    is_active: bool


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    req: RegisterRequest,
    db: Session = Depends(get_db),
    _admin=Depends(require_role(UserRole.ADMIN)),
):
    """Admin-only: create a new user account."""
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        id=generate_uuid(),
        email=req.email,
        username=req.username,
        hashed_password=get_password_hash(req.password),
        full_name=req.full_name,
        role=req.role,
        facility_id=req.facility_id,
        license_number=req.license_number,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and receive JWT access + refresh tokens."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    access_token = create_access_token({"sub": user.id, "role": user.role})
    refresh_token = create_refresh_token({"sub": user.id})

    # Persist refresh token and last login timestamp
    user.refresh_token = refresh_token
    user.last_login = datetime.utcnow()
    db.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(req: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new access token."""
    payload = decode_access_token(req.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.refresh_token != req.refresh_token or not user.is_active:
        raise HTTPException(status_code=401, detail="Refresh token revoked or invalid")

    new_access = create_access_token({"sub": user.id, "role": user.role})
    new_refresh = create_refresh_token({"sub": user.id})
    user.refresh_token = new_refresh
    db.commit()

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    req: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Change the current user's password."""
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = get_password_hash(req.new_password)
    db.commit()
