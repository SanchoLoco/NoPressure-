"""
Treatment Recommendation Engine.
Logic-based system that suggests dressings and interventions based on scan results.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TreatmentRecommendation:
    primary_dressing: str
    secondary_dressing: Optional[str]
    interventions: List[str]
    rationale: str
    urgency: str  # "routine", "urgent", "emergency"
    referral_needed: bool
    referral_reason: Optional[str]


class TreatmentEngine:
    """
    Evidence-based treatment recommendation system.
    Suggests dressings and interventions based on tissue composition,
    exudate level, wound etiology, and healing trajectory.
    """

    def recommend(
        self,
        granulation_pct: float,
        slough_pct: float,
        eschar_pct: float,
        exudate_level: str,
        etiology: str,
        is_stalled: bool = False,
        sub_epidermal_risk: str = "none",
    ) -> TreatmentRecommendation:
        """
        Generate treatment recommendation based on wound assessment.
        """
        interventions = []
        referral_needed = False
        referral_reason = None
        urgency = "routine"

        # Determine primary dressing based on dominant tissue and exudate
        if eschar_pct > 30:
            primary_dressing = "Hydrocolloid or Enzymatic Debridement Agent"
            interventions.append("Mechanical or autolytic debridement required")
            interventions.append("Vascular assessment recommended before sharp debridement")
            urgency = "urgent"
        elif slough_pct > 50:
            if exudate_level in ("high", "moderate"):
                primary_dressing = "Alginate Dressing"
                interventions.append("Debridement of fibrinous tissue required")
            else:
                primary_dressing = "Hydrogel Dressing"
                interventions.append("Autolytic debridement - maintain moist wound environment")
        elif granulation_pct > 70 and exudate_level == "low":
            primary_dressing = "Non-adherent Silicone Foam Dressing"
            interventions.append("Protect granulation tissue - avoid trauma on removal")
        elif granulation_pct > 70 and exudate_level in ("moderate", "high"):
            primary_dressing = "Foam Dressing with Superabsorbent Layer"
            interventions.append("High exudate detected; recommend Alginate dressing")
        else:
            primary_dressing = "Foam Dressing"

        # Etiology-specific interventions
        if etiology == "diabetic_foot_ulcer":
            interventions.append("Offloading: Total Contact Cast or therapeutic footwear")
            interventions.append("Blood glucose optimisation: target HbA1c <7%")
            referral_needed = True
            referral_reason = "Diabetic foot multidisciplinary team referral"
        elif etiology == "venous_leg_ulcer":
            interventions.append("Compression therapy: 40mmHg four-layer bandaging")
            interventions.append("Leg elevation when resting")
        elif etiology == "pressure_ulcer":
            interventions.append("Reposition every 2 hours")
            interventions.append("Pressure-redistributing mattress")
            interventions.append("Nutritional assessment (protein, vitamin C, zinc)")

        # Stalled wound intervention
        if is_stalled:
            interventions.append("Wound not progressing - consider biopsy to rule out malignancy")
            interventions.append("Review treatment plan and consider advanced therapy (NPWT or biologics)")
            urgency = "urgent"

        # Sub-epidermal risk
        if sub_epidermal_risk in ("moderate", "high"):
            interventions.append("Stage 1 pressure injury detected - initiate prevention protocol immediately")
            urgency = "urgent"

        return TreatmentRecommendation(
            primary_dressing=primary_dressing,
            secondary_dressing=None,
            interventions=interventions,
            rationale=self._build_rationale(granulation_pct, slough_pct, eschar_pct, exudate_level),
            urgency=urgency,
            referral_needed=referral_needed,
            referral_reason=referral_reason,
        )

    def _build_rationale(
        self, granulation_pct: float, slough_pct: float, eschar_pct: float, exudate_level: str
    ) -> str:
        parts = []
        if eschar_pct > 0:
            parts.append(f"{eschar_pct:.0f}% necrotic tissue present")
        if slough_pct > 0:
            parts.append(f"{slough_pct:.0f}% slough requiring debridement")
        if granulation_pct > 0:
            parts.append(f"{granulation_pct:.0f}% healthy granulation tissue")
        parts.append(f"{exudate_level} exudate level")
        return "; ".join(parts) + "."


treatment_engine = TreatmentEngine()
