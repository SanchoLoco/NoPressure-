from sqlalchemy import Column, String, Boolean, Text
from .base import Base, TimestampMixin, generate_uuid


class UserRole:
    NURSE = "nurse"
    PHYSICIAN = "physician"
    HEAD_NURSE = "head_nurse"
    ADMIN = "admin"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=True)
    role = Column(String(20), nullable=False, default=UserRole.NURSE)
    facility_id = Column(String(50), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    license_number = Column(String(100), nullable=True)
