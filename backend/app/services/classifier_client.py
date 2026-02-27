"""
External Wound Classifier API client.
Integrates with a remote AI model for continuous severity scoring and wound staging.
Supports mock mode for development when the external API is unavailable.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional
import httpx
from ..core.config import settings

logger = logging.getLogger(__name__)


class ClassifierResult:
    """Result from the external wound classifier API."""
    def __init__(
        self,
        severity_score: float,
        stage: str,
        confidence: float,
        measurements: dict,
        wound_id: str,
        timestamp: str,
        model_version: str = "mock-1.0.0",
    ):
        self.severity_score = severity_score
        self.stage = stage
        self.confidence = confidence
        self.measurements = measurements
        self.wound_id = wound_id
        self.timestamp = timestamp
        self.model_version = model_version


def _mock_response(wound_id: str) -> ClassifierResult:
    """Generate a realistic mock classifier response for development use."""
    return ClassifierResult(
        severity_score=2.7,
        stage="Stage 2",
        confidence=0.94,
        measurements={"length": 2.3, "width": 1.5, "depth": 0.2},
        wound_id=wound_id or str(uuid.uuid4()),
        timestamp=datetime.utcnow().isoformat() + "Z",
        model_version="mock-1.0.0",
    )


class WoundClassifierClient:
    """HTTP client for the external wound classifier API."""

    def __init__(self):
        self.base_url = settings.CLASSIFIER_API_URL
        self.api_key = settings.CLASSIFIER_API_KEY
        self.timeout = settings.CLASSIFIER_TIMEOUT
        self.mock_mode = settings.CLASSIFIER_MOCK_MODE

    def get_model_version(self) -> Optional[str]:
        """Check /version endpoint for model versioning (FDA/SaMD traceability)."""
        if self.mock_mode or not self.base_url:
            return "mock-1.0.0"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
                resp = client.get(f"{self.base_url}/version", headers=headers)
                resp.raise_for_status()
                return resp.json().get("version", "unknown")
        except Exception as exc:
            logger.warning("Classifier /version endpoint unavailable: %s", exc)
            return None

    def classify(self, image_data: bytes, wound_id: str) -> Optional[ClassifierResult]:
        """
        Send wound image to external classifier API.
        Returns ClassifierResult or None if API is unavailable.
        Falls back to mock mode when CLASSIFIER_MOCK_MODE=True.
        """
        if self.mock_mode or not self.base_url:
            logger.debug("Using mock classifier response (mock_mode=%s)", self.mock_mode)
            return _mock_response(wound_id)

        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            files = {"image": ("wound.jpg", image_data, "image/jpeg")}
            data = {"wound_id": wound_id}

            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.base_url}/classify",
                    files=files,
                    data=data,
                    headers=headers,
                )
                resp.raise_for_status()
                payload = resp.json()

            model_version = self.get_model_version() or "unknown"
            return ClassifierResult(
                severity_score=float(payload["severity_score"]),
                stage=str(payload["stage"]),
                confidence=float(payload["confidence"]),
                measurements=payload.get("measurements", {}),
                wound_id=payload.get("wound_id", wound_id),
                timestamp=payload.get("timestamp", datetime.utcnow().isoformat() + "Z"),
                model_version=model_version,
            )
        except Exception as exc:
            logger.warning("Classifier API unavailable, returning None: %s", exc)
            return None


classifier_client = WoundClassifierClient()
