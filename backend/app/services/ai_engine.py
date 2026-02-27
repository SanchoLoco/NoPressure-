"""
Core AI Engine for wound scanning and tissue segmentation.
Implements tissue classification, wound measurement, and sub-epidermal analysis.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List
import math


@dataclass
class WoundMeasurements:
    """3D volumetric measurements from photogrammetry/LiDAR."""
    length_cm: float
    width_cm: float
    depth_cm: float
    area_cm2: float
    volume_cm3: float
    measurement_error_pct: float  # Target: <5%
    calibration_confirmed: bool


@dataclass
class TissueSegmentation:
    """AI-driven tissue type classification within wound bed."""
    granulation_pct: float    # Red - healthy granulation tissue
    slough_pct: float         # Yellow - fibrinous slough needing debridement
    eschar_pct: float         # Black - necrotic/dead tissue
    epithelial_pct: float     # Pink - re-epithelialization
    hypergranulation_pct: float = 0.0

    def __post_init__(self):
        total = (self.granulation_pct + self.slough_pct + self.eschar_pct +
                 self.epithelial_pct + self.hypergranulation_pct)
        if abs(total - 100.0) > 1.0:
            raise ValueError(f"Tissue percentages must sum to ~100%, got {total}")


@dataclass
class SubEpidermalAnalysis:
    """Early-stage pressure ulcer detection (Stage 1) before skin breaks."""
    persistent_redness_detected: bool
    temperature_delta_celsius: float
    risk_level: str  # "none", "low", "moderate", "high"
    recommendation: str


@dataclass
class ScanAnalysisResult:
    measurements: WoundMeasurements
    tissue: TissueSegmentation
    sub_epidermal: SubEpidermalAnalysis
    capture_angle_degrees: float
    calibration_marker_detected: bool
    exudate_level: str
    exudate_type: str
    periwound_condition: str
    # Classifier results (populated if external classifier is available)
    severity_score: Optional[float] = None
    stage_classification: Optional[str] = None
    ai_confidence: Optional[float] = None
    model_version: Optional[str] = None


class AIWoundEngine:
    """
    Core AI engine for wound analysis.

    In production this integrates with:
    - Computer vision models for tissue segmentation (e.g., U-Net, DeepLab)
    - Photogrammetry/LiDAR for 3D measurements
    - Thermal sensor APIs for temperature analysis
    - Auto-calibration via fiducial markers
    - External wound classifier API for continuous severity scoring
    """

    MEASUREMENT_ERROR_TARGET = 5.0  # <5% margin of error

    def analyze_wound_image(
        self,
        image_data: bytes,
        has_calibration_marker: bool = True,
        thermal_data: Optional[bytes] = None,
        capture_angle: float = 90.0,
        wound_id: Optional[str] = None,
    ) -> ScanAnalysisResult:
        """
        Analyze wound image and return comprehensive scan results.

        Args:
            image_data: Raw image bytes from camera
            has_calibration_marker: Whether physical scale marker is present
            thermal_data: Optional thermal sensor data for sub-epidermal analysis
            capture_angle: Camera angle in degrees (target: 90°)
            wound_id: Optional wound ID for classifier API call

        Returns:
            ScanAnalysisResult with all measurements and AI classifications
        """
        # Validate capture quality
        self._validate_capture_angle(capture_angle)

        # Run 3D measurement pipeline
        measurements = self._measure_wound_3d(image_data, has_calibration_marker)

        # Run tissue segmentation
        tissue = self._segment_tissue(image_data)

        # Sub-epidermal analysis
        sub_epidermal = self._analyze_sub_epidermal(image_data, thermal_data)

        # Assess exudate and periwound
        exudate_level, exudate_type = self._assess_exudate(image_data)
        periwound = self._assess_periwound(image_data)

        # Call external classifier API for severity score and staging
        severity_score = None
        stage_classification = None
        ai_confidence = None
        model_version = None
        try:
            from .classifier_client import classifier_client
            classifier_result = classifier_client.classify(
                image_data=image_data,
                wound_id=wound_id or "",
            )
            if classifier_result is not None:
                severity_score = classifier_result.severity_score
                stage_classification = classifier_result.stage
                ai_confidence = classifier_result.confidence
                model_version = classifier_result.model_version
        except Exception:
            pass  # Classifier is optional; proceed without it

        return ScanAnalysisResult(
            measurements=measurements,
            tissue=tissue,
            sub_epidermal=sub_epidermal,
            capture_angle_degrees=capture_angle,
            calibration_marker_detected=has_calibration_marker,
            exudate_level=exudate_level,
            exudate_type=exudate_type,
            periwound_condition=periwound,
            severity_score=severity_score,
            stage_classification=stage_classification,
            ai_confidence=ai_confidence,
            model_version=model_version,
        )

    def _validate_capture_angle(self, angle: float) -> None:
        """Enforce 90-degree capture angle for accurate measurements."""
        if abs(angle - 90.0) > 15.0:
            raise ValueError(
                f"Camera angle {angle}° is too far from 90°. "
                "Please align camera perpendicular to wound surface."
            )

    def _measure_wound_3d(
        self, image_data: bytes, has_calibration: bool
    ) -> WoundMeasurements:
        """
        3D volumetric measurement using photogrammetry or LiDAR.
        Auto-calibrates using detected physical markers.
        """
        # Production: integrate with photogrammetry SDK or LiDAR depth API
        # The calibration marker ensures accuracy regardless of camera distance
        error_pct = 2.5 if has_calibration else 8.0

        # Stub measurements - replace with real CV pipeline
        length = 3.2
        width = 2.1
        depth = 0.4
        area = math.pi * (length / 2) * (width / 2)  # Ellipse approximation
        volume = area * depth * (2 / 3)  # Ellipsoid approximation

        return WoundMeasurements(
            length_cm=length,
            width_cm=width,
            depth_cm=depth,
            area_cm2=round(area, 2),
            volume_cm3=round(volume, 2),
            measurement_error_pct=error_pct,
            calibration_confirmed=has_calibration,
        )

    def _segment_tissue(self, image_data: bytes) -> TissueSegmentation:
        """
        AI-driven tissue classification within wound bed.
        Production: Use U-Net or DeepLabV3 trained on wound images.
        """
        # Stub - replace with trained CNN inference
        return TissueSegmentation(
            granulation_pct=60.0,
            slough_pct=25.0,
            eschar_pct=10.0,
            epithelial_pct=5.0,
        )

    def _analyze_sub_epidermal(
        self, image_data: bytes, thermal_data: Optional[bytes]
    ) -> SubEpidermalAnalysis:
        """
        Detect early-stage pressure ulcers (Stage 1) before skin breaks.
        Uses persistent redness detection and thermal variance analysis.
        """
        has_redness = False
        temp_delta = 0.0

        if thermal_data:
            # Production: parse thermal camera data to detect hotspots
            temp_delta = 1.2  # Stub: 1.2°C difference from surrounding skin

        if temp_delta > 1.5 or has_redness:
            risk = "moderate" if temp_delta > 1.5 else "low"
            recommendation = (
                "Reposition patient every 2 hours; apply pressure-relieving mattress"
            )
        else:
            risk = "none"
            recommendation = "No immediate intervention required; continue monitoring"

        return SubEpidermalAnalysis(
            persistent_redness_detected=has_redness,
            temperature_delta_celsius=temp_delta,
            risk_level=risk,
            recommendation=recommendation,
        )

    def _assess_exudate(self, image_data: bytes):
        """Classify exudate level and type from image analysis."""
        # Production: Color analysis + CNN classification
        return "moderate", "serous"

    def _assess_periwound(self, image_data: bytes) -> str:
        """Assess periwound skin condition."""
        return "Mild maceration present; intact surrounding skin"

    def calculate_par(self, baseline_area: float, current_area: float) -> float:
        """
        Calculate Percentage Area Reduction (PAR).
        PAR = ((baseline - current) / baseline) * 100
        """
        if baseline_area <= 0:
            return 0.0
        return round(((baseline_area - current_area) / baseline_area) * 100, 1)

    def is_wound_stalled(
        self, par: float, days_elapsed: int, threshold_pct: float = 20.0, threshold_days: int = 28
    ) -> bool:
        """
        Determine if wound healing has stalled.
        Alert if wound doesn't shrink by threshold_pct in threshold_days days.
        """
        return days_elapsed >= threshold_days and par < threshold_pct


ai_engine = AIWoundEngine()
