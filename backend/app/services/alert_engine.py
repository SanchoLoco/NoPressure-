"""
Rule-based alert engine for early warning of wound deterioration.
Triggered after each new scan is created.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from ..models.alert import Alert, AlertType, AlertSeverity
from ..models.scan import Scan
from ..models.wound import Wound
from ..models.base import generate_uuid

logger = logging.getLogger(__name__)

# Configurable thresholds
SEVERITY_SPIKE_THRESHOLD = 0.5   # Increase >0.5 within 24 h triggers alert
STALLED_PAR_THRESHOLD = 20.0     # PAR < 20% after 28 days = stalled
STALLED_DAYS = 28
STAGE_4_PREDICTED_SCORE = 3.5    # Projected score >= this → Stage 4 risk


def _linear_trend(x: List[float], y: List[float]) -> Optional[float]:
    """Return slope of the best-fit line, or None if not enough data."""
    n = len(x)
    if n < 2:
        return None
    try:
        import numpy as np
        coeffs = np.polyfit(x, y, 1)
        return float(coeffs[0])
    except Exception:
        return None


def _project_severity(scans: List[Scan], days_ahead: int = 14) -> Optional[float]:
    """Linear regression projection of severity score N days ahead."""
    scored = [(s.created_at.timestamp(), s.severity_score) for s in scans if s.severity_score is not None]
    if len(scored) < 2:
        return None
    x = [t for t, _ in scored]
    y = [v for _, v in scored]
    try:
        import numpy as np
        coeffs = np.polyfit(x, y, 1)
        future_t = x[-1] + days_ahead * 86400
        return float(coeffs[0] * future_t + coeffs[1])
    except Exception:
        return None


def evaluate_alerts(wound_id: str, db: Session) -> List[Alert]:
    """
    Evaluate all rules for a wound and persist any new alerts.
    Returns the list of newly created Alert objects.
    """
    wound = db.query(Wound).filter(Wound.id == wound_id).first()
    if not wound:
        return []

    scans: List[Scan] = (
        db.query(Scan)
        .filter(Scan.wound_id == wound_id)
        .order_by(Scan.created_at)
        .all()
    )
    if not scans:
        return []

    new_alerts: List[Alert] = []

    # ── Rule 1: Severity spike (>0.5 increase within 24 h) ─────────────────
    recent_scored = [s for s in scans if s.severity_score is not None]
    if len(recent_scored) >= 2:
        last = recent_scored[-1]
        prev_24h = [
            s for s in recent_scored[:-1]
            if (last.created_at - s.created_at) <= timedelta(hours=24)
        ]
        if prev_24h:
            delta = last.severity_score - prev_24h[-1].severity_score
            if delta > SEVERITY_SPIKE_THRESHOLD:
                alert = Alert(
                    id=generate_uuid(),
                    wound_id=wound_id,
                    patient_id=wound.patient_id,
                    alert_type=AlertType.SEVERITY_SPIKE,
                    severity=AlertSeverity.HIGH,
                    message=(
                        f"Severity score increased by {delta:.2f} in the last 24 hours "
                        f"(from {prev_24h[-1].severity_score:.1f} to {last.severity_score:.1f})."
                    ),
                )
                db.add(alert)
                new_alerts.append(alert)
                logger.info("Severity spike alert created for wound %s", wound_id)

    # ── Rule 2: Stalled wound (PAR < 20% after 28 days) ────────────────────
    if scans[0].area_cm2 and scans[-1].area_cm2:
        baseline_area = scans[0].area_cm2
        current_area = scans[-1].area_cm2
        days_elapsed = (scans[-1].created_at - scans[0].created_at).days
        if baseline_area > 0:
            par = ((baseline_area - current_area) / baseline_area) * 100
            if days_elapsed >= STALLED_DAYS and par < STALLED_PAR_THRESHOLD:
                alert = Alert(
                    id=generate_uuid(),
                    wound_id=wound_id,
                    patient_id=wound.patient_id,
                    alert_type=AlertType.STALLED_WOUND,
                    severity=AlertSeverity.MEDIUM,
                    message=(
                        f"Wound has not improved by 20%% in {days_elapsed} days "
                        f"(current PAR: {par:.1f}%%). Consider treatment plan review."
                    ),
                )
                db.add(alert)
                new_alerts.append(alert)
                logger.info("Stalled wound alert created for wound %s", wound_id)

    # ── Rule 3: Predicted Stage 4 (linear regression) ──────────────────────
    projected = _project_severity(scans, days_ahead=14)
    if projected is not None and projected >= STAGE_4_PREDICTED_SCORE:
        alert = Alert(
            id=generate_uuid(),
            wound_id=wound_id,
            patient_id=wound.patient_id,
            alert_type=AlertType.STAGE_4_PREDICTED,
            severity=AlertSeverity.CRITICAL,
            message=(
                f"Projected severity score in 14 days: {projected:.1f}. "
                "Stage 4 progression risk detected. Immediate clinical review recommended."
            ),
        )
        db.add(alert)
        new_alerts.append(alert)
        logger.warning("Stage 4 prediction alert created for wound %s", wound_id)

    if new_alerts:
        db.commit()

    return new_alerts
