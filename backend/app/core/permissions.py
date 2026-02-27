"""
Role-based permission matrix for NoPressure.
Defines what each clinical role is allowed to do in the system.
"""
from ..models.user import UserRole

# Permission constants
PERM_UPLOAD_IMAGES = "upload_images"
PERM_VIEW_OWN_PATIENTS = "view_own_patients"
PERM_VIEW_ALL_UNIT_PATIENTS = "view_all_unit_patients"
PERM_ADD_NOTES = "add_notes"
PERM_MODIFY_TREATMENT_PLANS = "modify_treatment_plans"
PERM_MANAGE_USERS = "manage_users"
PERM_VIEW_AUDIT_LOGS = "view_audit_logs"
PERM_SYSTEM_CONFIG = "system_config"
PERM_VIEW_AGGREGATE_REPORTS = "view_aggregate_reports"
PERM_VIEW_PATIENT_LEVEL_DATA = "view_patient_level_data"

# Role permission matrix
ROLE_PERMISSIONS: dict = {
    UserRole.NURSE: {
        PERM_UPLOAD_IMAGES,
        PERM_VIEW_OWN_PATIENTS,
        PERM_ADD_NOTES,
        PERM_VIEW_PATIENT_LEVEL_DATA,
    },
    UserRole.PHYSICIAN: {
        PERM_UPLOAD_IMAGES,
        PERM_VIEW_OWN_PATIENTS,
        PERM_VIEW_ALL_UNIT_PATIENTS,
        PERM_ADD_NOTES,
        PERM_MODIFY_TREATMENT_PLANS,
        PERM_VIEW_PATIENT_LEVEL_DATA,
    },
    UserRole.HEAD_NURSE: {
        PERM_UPLOAD_IMAGES,
        PERM_VIEW_OWN_PATIENTS,
        PERM_VIEW_ALL_UNIT_PATIENTS,
        PERM_ADD_NOTES,
        PERM_MODIFY_TREATMENT_PLANS,
        PERM_VIEW_PATIENT_LEVEL_DATA,
    },
    UserRole.ADMIN: {
        PERM_UPLOAD_IMAGES,
        PERM_VIEW_OWN_PATIENTS,
        PERM_VIEW_ALL_UNIT_PATIENTS,
        PERM_ADD_NOTES,
        PERM_MODIFY_TREATMENT_PLANS,
        PERM_MANAGE_USERS,
        PERM_VIEW_AUDIT_LOGS,
        PERM_SYSTEM_CONFIG,
        PERM_VIEW_AGGREGATE_REPORTS,
        PERM_VIEW_PATIENT_LEVEL_DATA,
    },
    UserRole.QUALITY_OFFICER: {
        PERM_VIEW_AGGREGATE_REPORTS,
        # Quality officer does NOT have PERM_VIEW_PATIENT_LEVEL_DATA
    },
}


def has_permission(role: str, permission: str) -> bool:
    """Check if a role has a specific permission."""
    return permission in ROLE_PERMISSIONS.get(role, set())
