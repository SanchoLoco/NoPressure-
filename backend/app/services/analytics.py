"""
Healing Trend Analytics - PAR calculation, stalled wound detection, and reporting.
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class HealingTrend:
    wound_id: str
    baseline_area_cm2: float
    current_area_cm2: float
    par_percentage: float
    days_elapsed: int
    is_stalled: bool
    trend_direction: str  # "improving", "stable", "deteriorating"
    projected_healing_days: Optional[int]


@dataclass
class FacilityWoundBurden:
    facility_id: str
    total_wounds: int
    active_wounds: int
    stalled_wounds: int
    healed_this_month: int
    average_healing_days: float
    wound_by_etiology: Dict[str, int]
    dressing_usage_summary: Dict[str, int]


class AnalyticsService:
    """
    Wound healing analytics engine.
    Calculates PAR, detects stalled wounds, and generates facility-level reports.
    """

    STALLED_PAR_THRESHOLD = 20.0  # <20% area reduction
    STALLED_DAYS = 28             # over 4 weeks

    def calculate_healing_trend(
        self,
        wound_id: str,
        scan_history: List[Dict],
    ) -> HealingTrend:
        """
        Calculate healing trend from scan history.
        Triggers stalled wound alert if PAR < 20% in 4 weeks.
        """
        if not scan_history:
            raise ValueError("No scan history available")

        baseline = scan_history[0]
        current = scan_history[-1]

        baseline_area = baseline.get("area_cm2", 0)
        current_area = current.get("area_cm2", 0)

        baseline_date = baseline.get("created_at", datetime.utcnow())
        current_date = current.get("created_at", datetime.utcnow())

        days_elapsed = (current_date - baseline_date).days if isinstance(baseline_date, datetime) else 0

        par = self._calculate_par(baseline_area, current_area)
        is_stalled = (
            days_elapsed >= self.STALLED_DAYS and par < self.STALLED_PAR_THRESHOLD
        )

        trend_direction = self._get_trend_direction(scan_history)
        projected_days = self._project_healing_days(scan_history, current_area)

        return HealingTrend(
            wound_id=wound_id,
            baseline_area_cm2=baseline_area,
            current_area_cm2=current_area,
            par_percentage=par,
            days_elapsed=days_elapsed,
            is_stalled=is_stalled,
            trend_direction=trend_direction,
            projected_healing_days=projected_days,
        )

    def _calculate_par(self, baseline_area: float, current_area: float) -> float:
        if baseline_area <= 0:
            return 0.0
        return round(((baseline_area - current_area) / baseline_area) * 100, 1)

    def _get_trend_direction(self, scan_history: List[Dict]) -> str:
        if len(scan_history) < 2:
            return "stable"
        recent_areas = [s.get("area_cm2", 0) for s in scan_history[-3:]]
        if len(recent_areas) < 2:
            return "stable"
        if recent_areas[-1] < recent_areas[0] * 0.95:
            return "improving"
        if recent_areas[-1] > recent_areas[0] * 1.05:
            return "deteriorating"
        return "stable"

    def _project_healing_days(
        self, scan_history: List[Dict], current_area: float
    ) -> Optional[int]:
        """Project days to full healing based on current healing rate."""
        if len(scan_history) < 2 or current_area <= 0:
            return None

        # Simple linear projection from last two scans
        areas = [s.get("area_cm2", 0) for s in scan_history[-2:]]
        dates = [s.get("created_at", datetime.utcnow()) for s in scan_history[-2:]]

        if not all(isinstance(d, datetime) for d in dates):
            return None

        days = (dates[-1] - dates[-2]).days
        if days <= 0:
            return None

        area_change_per_day = (areas[0] - areas[-1]) / days
        if area_change_per_day <= 0:
            return None  # Not healing

        return int(current_area / area_change_per_day)


analytics_service = AnalyticsService()
