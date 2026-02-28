"""Tests for new services: dynamic AI engine, image storage, and PDF report generation."""
import os
import hashlib
import tempfile

import pytest
from app.services.ai_engine import AIWoundEngine, TissueSegmentation
from app.services.image_storage import ImageStorageService
from app.services.report_generator import WoundReportGenerator


# ---------------------------------------------------------------------------
# Dynamic AI Engine — image-hash-based results
# ---------------------------------------------------------------------------

class TestDynamicAIEngine:
    def setup_method(self):
        self.engine = AIWoundEngine()

    def test_different_images_produce_different_measurements(self):
        """Two distinct images should yield different 3D measurements."""
        m1 = self.engine._measure_wound_3d(b"image_a", has_calibration=True)
        m2 = self.engine._measure_wound_3d(b"image_b", has_calibration=True)
        assert (m1.length_cm, m1.width_cm, m1.depth_cm) != (
            m2.length_cm,
            m2.width_cm,
            m2.depth_cm,
        )

    def test_same_image_is_deterministic(self):
        """The same image bytes must always produce identical results."""
        m1 = self.engine._measure_wound_3d(b"stable_image", has_calibration=True)
        m2 = self.engine._measure_wound_3d(b"stable_image", has_calibration=True)
        assert m1.length_cm == m2.length_cm
        assert m1.width_cm == m2.width_cm
        assert m1.depth_cm == m2.depth_cm

    def test_measurements_within_clinical_range(self):
        """All measurements should fall within plausible clinical ranges."""
        for seed in [b"a", b"b", b"c", b"d", b"e"]:
            m = self.engine._measure_wound_3d(seed, has_calibration=True)
            assert 1.0 <= m.length_cm <= 7.0
            assert 0.5 <= m.width_cm <= 5.0
            assert 0.1 <= m.depth_cm <= 2.0
            assert m.area_cm2 > 0
            assert m.volume_cm3 > 0

    def test_calibration_affects_error(self):
        m_cal = self.engine._measure_wound_3d(b"x", has_calibration=True)
        m_nocal = self.engine._measure_wound_3d(b"x", has_calibration=False)
        assert m_cal.measurement_error_pct < m_nocal.measurement_error_pct

    def test_tissue_segmentation_varies_with_image(self):
        t1 = self.engine._segment_tissue(b"wound_photo_1")
        t2 = self.engine._segment_tissue(b"wound_photo_2")
        # At least one percentage should differ
        assert (
            t1.granulation_pct != t2.granulation_pct
            or t1.slough_pct != t2.slough_pct
        )

    def test_tissue_segmentation_sums_to_100(self):
        """Dynamic segmentation still sums to ~100%."""
        for seed in [b"x", b"y", b"z", b"test", b"abc"]:
            t = self.engine._segment_tissue(seed)
            total = (
                t.granulation_pct + t.slough_pct + t.eschar_pct + t.epithelial_pct
            )
            assert abs(total - 100.0) < 1.0, f"Tissue sum {total} != ~100 for seed {seed}"

    def test_exudate_varies_with_image(self):
        """Exudate assessment should produce valid levels and types."""
        valid_levels = {"none", "low", "moderate", "high"}
        valid_types = {"serous", "serosanguineous", "sanguineous", "purulent"}
        for seed in [b"a", b"b", b"c", b"d"]:
            level, etype = self.engine._assess_exudate(seed)
            assert level in valid_levels
            assert etype in valid_types

    def test_periwound_varies_with_image(self):
        """Periwound condition should be a non-empty string from known set."""
        results = set()
        for i in range(20):
            results.add(self.engine._assess_periwound(bytes([i])))
        # Should produce at least 2 distinct conditions across 20 inputs
        assert len(results) >= 2

    def test_full_analysis_produces_valid_result(self):
        """End-to-end analysis should complete without error."""
        result = self.engine.analyze_wound_image(
            image_data=b"full_analysis_test",
            has_calibration_marker=True,
            capture_angle=90.0,
            wound_id="test-wound-1",
        )
        assert result.measurements.length_cm > 0
        assert result.tissue.granulation_pct >= 0
        assert result.severity_score is not None
        assert result.severity_color in ("green", "orange", "red")


# ---------------------------------------------------------------------------
# Image Storage Service
# ---------------------------------------------------------------------------

class TestImageStorageService:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.service = ImageStorageService(base_dir=self.tmpdir)

    def test_store_returns_url_and_hash(self):
        result = self.service.store(b"fake_image_data", "wound-1", "scan-1")
        assert "image_url" in result
        assert "image_hash" in result
        expected_hash = hashlib.sha256(b"fake_image_data").hexdigest()
        assert result["image_hash"] == expected_hash

    def test_store_creates_file_on_disk(self):
        result = self.service.store(b"png_bytes", "wound-2", "scan-2")
        assert os.path.exists(result["image_url"])
        with open(result["image_url"], "rb") as f:
            assert f.read() == b"png_bytes"

    def test_store_creates_wound_subdirectory(self):
        self.service.store(b"data", "wound-3", "scan-3")
        assert os.path.isdir(os.path.join(self.tmpdir, "wound-3"))

    def test_different_scans_different_files(self):
        r1 = self.service.store(b"img1", "wound-4", "scan-a")
        r2 = self.service.store(b"img2", "wound-4", "scan-b")
        assert r1["image_url"] != r2["image_url"]


# ---------------------------------------------------------------------------
# PDF Report Generator
# ---------------------------------------------------------------------------

class TestWoundReportGenerator:
    def setup_method(self):
        self.gen = WoundReportGenerator()

    def test_generates_valid_pdf_bytes(self):
        from datetime import datetime
        scans = [
            {
                "created_at": datetime(2026, 1, 1),
                "scanned_by": "nurse-1",
                "area_cm2": 5.27,
                "par_from_baseline": None,
                "severity_score": 2.3,
                "stage_classification": "Stage 2",
                "tissue_granulation_pct": 55.0,
                "tissue_slough_pct": 30.0,
                "tissue_eschar_pct": 10.0,
                "treatment_recommendation": {"primary_dressing": "Foam", "interventions": ["Offloading"]},
                "clinical_notes": "Looking better",
            },
        ]
        pdf = self.gen.generate(
            patient_name="Test Patient",
            patient_mrn="MRN-123",
            wound_id="w-1",
            wound_etiology="pressure_ulcer",
            wound_location="sacrum",
            scans=scans,
            generated_by="dr-smith",
        )
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100
        # PDF files start with %PDF
        assert pdf[:5] == b"%PDF-"

    def test_empty_scans_returns_pdf(self):
        """Even with no scans, the header info should be rendered."""
        pdf = self.gen.generate(
            patient_name="Jane Doe",
            patient_mrn="MRN-456",
            wound_id="w-2",
            wound_etiology="burn",
            wound_location="left_heel",
            scans=[],
            generated_by="admin",
        )
        assert pdf[:5] == b"%PDF-"

    def test_multiple_scans_table(self):
        from datetime import datetime, timedelta
        scans = []
        for i in range(5):
            scans.append({
                "created_at": datetime(2026, 1, 1) + timedelta(days=i * 7),
                "scanned_by": f"nurse-{i}",
                "area_cm2": 10.0 - i * 1.5,
                "par_from_baseline": i * 15.0 if i > 0 else None,
                "severity_score": 3.0 - i * 0.3,
                "stage_classification": f"Stage {max(1, 3 - i // 2)}",
                "tissue_granulation_pct": 40 + i * 10,
                "tissue_slough_pct": 35 - i * 5,
                "tissue_eschar_pct": 20 - i * 4,
                "treatment_recommendation": {},
                "clinical_notes": None,
            })
        pdf = self.gen.generate(
            patient_name="Multi Scan",
            patient_mrn="MRN-789",
            wound_id="w-3",
            wound_etiology="venous_leg_ulcer",
            wound_location="right_heel",
            scans=scans,
            generated_by="system",
        )
        assert len(pdf) > 200
