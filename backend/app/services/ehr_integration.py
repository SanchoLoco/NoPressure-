"""
EHR/EMR Integration via HL7/FHIR protocols.
Supports Epic, Cerner, and local HMO systems.
"""
from dataclasses import dataclass
from typing import Dict, Optional, List
import json
from datetime import datetime


@dataclass
class FHIRObservation:
    """FHIR R4 Observation resource for wound measurements."""
    patient_id: str
    wound_id: str
    scan_id: str
    measurements: Dict
    tissue_composition: Dict
    performed_by: str
    performed_at: datetime


class FHIRClient:
    """
    HL7 FHIR R4 client for EHR integration.
    Pushes wound observations and PDF reports to Epic, Cerner, or other FHIR servers.
    """

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key

    def build_wound_observation(self, observation: FHIRObservation) -> Dict:
        """Build FHIR R4 Observation resource for wound scan data."""
        return {
            "resourceType": "Observation",
            "id": observation.scan_id,
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "exam",
                            "display": "Exam",
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "39135-9",
                        "display": "Wound measurement",
                    }
                ]
            },
            "subject": {"reference": f"Patient/{observation.patient_id}"},
            "effectiveDateTime": observation.performed_at.isoformat(),
            "performer": [{"display": observation.performed_by}],
            "component": [
                {
                    "code": {"coding": [{"code": "length", "display": "Wound Length"}]},
                    "valueQuantity": {
                        "value": observation.measurements.get("length_cm"),
                        "unit": "cm",
                        "system": "http://unitsofmeasure.org",
                    },
                },
                {
                    "code": {"coding": [{"code": "width", "display": "Wound Width"}]},
                    "valueQuantity": {
                        "value": observation.measurements.get("width_cm"),
                        "unit": "cm",
                        "system": "http://unitsofmeasure.org",
                    },
                },
                {
                    "code": {"coding": [{"code": "area", "display": "Wound Area"}]},
                    "valueQuantity": {
                        "value": observation.measurements.get("area_cm2"),
                        "unit": "cm2",
                        "system": "http://unitsofmeasure.org",
                    },
                },
            ],
            "extension": [
                {
                    "url": "http://nopressure.io/fhir/tissue-composition",
                    "extension": [
                        {"url": "granulation", "valueDecimal": observation.tissue_composition.get("granulation_pct", 0)},
                        {"url": "slough", "valueDecimal": observation.tissue_composition.get("slough_pct", 0)},
                        {"url": "eschar", "valueDecimal": observation.tissue_composition.get("eschar_pct", 0)},
                    ],
                }
            ],
        }

    def push_observation(self, observation: FHIRObservation) -> Dict:
        """
        Push wound observation to EHR system via FHIR REST API.
        Production: Use httpx to POST to FHIR server.
        """
        fhir_resource = self.build_wound_observation(observation)
        # Production: POST to self.base_url/Observation
        # response = httpx.post(f"{self.base_url}/Observation", json=fhir_resource, headers={"Authorization": f"Bearer {self.api_key}"})
        return {"status": "queued", "resource": fhir_resource}
