import pytest
from app.services.ai_engine import AIWoundEngine, TissueSegmentation, WoundMeasurements


class TestAIWoundEngine:
    def setup_method(self):
        self.engine = AIWoundEngine()

    def test_calculate_par_normal(self):
        """PAR should correctly calculate percentage area reduction."""
        par = self.engine.calculate_par(baseline_area=10.0, current_area=8.0)
        assert par == 20.0

    def test_calculate_par_full_healing(self):
        """PAR of 100% means wound fully healed."""
        par = self.engine.calculate_par(baseline_area=10.0, current_area=0.0)
        assert par == 100.0

    def test_calculate_par_zero_baseline(self):
        """PAR with zero baseline should return 0 (avoid division by zero)."""
        par = self.engine.calculate_par(baseline_area=0.0, current_area=5.0)
        assert par == 0.0

    def test_stalled_wound_detection(self):
        """Wound with <20% PAR after 28+ days should be flagged as stalled."""
        assert self.engine.is_wound_stalled(par=15.0, days_elapsed=30) is True

    def test_not_stalled_wound(self):
        """Wound with >20% PAR should not be stalled."""
        assert self.engine.is_wound_stalled(par=25.0, days_elapsed=30) is False

    def test_not_stalled_too_early(self):
        """Wound not yet at 28 days should not be flagged as stalled."""
        assert self.engine.is_wound_stalled(par=5.0, days_elapsed=10) is False

    def test_validate_capture_angle_valid(self):
        """90-degree angle should not raise."""
        self.engine._validate_capture_angle(90.0)  # Should not raise
        self.engine._validate_capture_angle(80.0)  # Within 15 degrees, ok

    def test_validate_capture_angle_invalid(self):
        """Angles too far from 90° should raise ValueError."""
        with pytest.raises(ValueError, match="Camera angle"):
            self.engine._validate_capture_angle(45.0)

    def test_tissue_segmentation_sums_to_100(self):
        """Tissue percentages must sum to approximately 100%."""
        tissue = TissueSegmentation(
            granulation_pct=60.0,
            slough_pct=25.0,
            eschar_pct=10.0,
            epithelial_pct=5.0,
        )
        total = (tissue.granulation_pct + tissue.slough_pct +
                 tissue.eschar_pct + tissue.epithelial_pct)
        assert abs(total - 100.0) < 1.0

    def test_tissue_segmentation_invalid_sum(self):
        """TissueSegmentation should raise if percentages don't sum to ~100%."""
        with pytest.raises(ValueError):
            TissueSegmentation(
                granulation_pct=10.0,
                slough_pct=10.0,
                eschar_pct=10.0,
                epithelial_pct=10.0,
            )


class TestTreatmentEngine:
    def setup_method(self):
        from app.services.treatment_engine import TreatmentEngine
        self.engine = TreatmentEngine()

    def test_high_exudate_recommends_alginate(self):
        """High exudate with slough should recommend alginate dressing."""
        rec = self.engine.recommend(
            granulation_pct=30.0,
            slough_pct=60.0,
            eschar_pct=10.0,
            exudate_level="high",
            etiology="venous_leg_ulcer",
        )
        assert "Alginate" in rec.primary_dressing

    def test_eschar_recommends_debridement(self):
        """High eschar percentage should trigger debridement recommendation."""
        rec = self.engine.recommend(
            granulation_pct=20.0,
            slough_pct=10.0,
            eschar_pct=70.0,
            exudate_level="low",
            etiology="pressure_ulcer",
        )
        assert any("debridement" in i.lower() for i in rec.interventions)

    def test_diabetic_foot_ulcer_requires_offloading(self):
        """Diabetic foot ulcer should always include offloading recommendation."""
        rec = self.engine.recommend(
            granulation_pct=70.0,
            slough_pct=20.0,
            eschar_pct=10.0,
            exudate_level="moderate",
            etiology="diabetic_foot_ulcer",
        )
        assert any("Offloading" in i for i in rec.interventions)
        assert rec.referral_needed is True

    def test_stalled_wound_escalates_urgency(self):
        """Stalled wound should have urgent priority and escalation plan."""
        rec = self.engine.recommend(
            granulation_pct=50.0,
            slough_pct=30.0,
            eschar_pct=20.0,
            exudate_level="moderate",
            etiology="venous_leg_ulcer",
            is_stalled=True,
        )
        assert rec.urgency == "urgent"


class TestAnalyticsService:
    def setup_method(self):
        from app.services.analytics import AnalyticsService
        self.service = AnalyticsService()

    def test_healing_trend_improving(self):
        from datetime import datetime, timedelta
        scans = [
            {"area_cm2": 10.0, "created_at": datetime.utcnow() - timedelta(days=30)},
            {"area_cm2": 7.0, "created_at": datetime.utcnow() - timedelta(days=15)},
            {"area_cm2": 5.0, "created_at": datetime.utcnow()},
        ]
        trend = self.service.calculate_healing_trend("wound-1", scans)
        assert trend.par_percentage == 50.0
        assert trend.is_stalled is False
        assert trend.trend_direction == "improving"

    def test_stalled_wound_detection(self):
        from datetime import datetime, timedelta
        scans = [
            {"area_cm2": 10.0, "created_at": datetime.utcnow() - timedelta(days=35)},
            {"area_cm2": 9.5, "created_at": datetime.utcnow()},
        ]
        trend = self.service.calculate_healing_trend("wound-2", scans)
        assert trend.is_stalled is True
        assert trend.par_percentage < 20.0

    def test_empty_scan_history_raises(self):
        with pytest.raises(ValueError, match="No scan history"):
            self.service.calculate_healing_trend("wound-3", [])
