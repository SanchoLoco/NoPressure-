"""
HIPAA-compliant audit logging middleware.
Auto-logs all requests to PHI endpoints (patients, wounds, scans).
"""
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from ..models.scan import AuditLog
from ..models.base import SessionLocal, generate_uuid
from ..core.security import decode_access_token

logger = logging.getLogger(__name__)

# Endpoints that touch PHI - requests to these paths are logged
PHI_PATH_PREFIXES = (
    "/api/v1/patients",
    "/api/v1/wounds",
    "/api/v1/scans",
)


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware that auto-logs access to PHI endpoints."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        path = request.url.path
        if not any(path.startswith(prefix) for prefix in PHI_PATH_PREFIXES):
            return response

        # Only log mutating operations or reads of specific resources
        if request.method not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
            return response

        user_id = "anonymous"
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            payload = decode_access_token(auth_header[7:])
            if payload:
                user_id = payload.get("sub", "anonymous")

        # Derive resource type and ID from path
        parts = [p for p in path.split("/") if p]
        resource_type = "unknown"
        resource_id = "unknown"
        if len(parts) >= 3:
            resource_type = parts[2]  # e.g., "patients"
        if len(parts) >= 4:
            resource_id = parts[3]

        action_map = {
            "GET": "view",
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete",
        }
        action = action_map.get(request.method, request.method.lower())

        ip_address = request.client.host if request.client else None

        try:
            db = SessionLocal()
            log_entry = AuditLog(
                id=generate_uuid(),
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                request_method=request.method,
                request_path=path,
                scan_id=None,
            )
            db.add(log_entry)
            db.commit()
        except Exception as exc:
            logger.warning(
                "Audit log write failed for %s %s (user=%s): %s",
                request.method, path, user_id, exc,
            )
        finally:
            db.close()

        return response
