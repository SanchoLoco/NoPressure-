from app.services.ehr_integration import FHIRClient, FHIRObservation
from datetime import datetime


def test_fhir_observation_structure():
    """FHIR Observation should conform to R4 resource structure."""
    client = FHIRClient(base_url="https://fhir.example.com", api_key="test-key")
    obs = FHIRObservation(
        patient_id="patient-123",
        wound_id="wound-456",
        scan_id="scan-789",
        measurements={"length_cm": 3.2, "width_cm": 2.1, "area_cm2": 5.3},
        tissue_composition={"granulation_pct": 60.0, "slough_pct": 30.0, "eschar_pct": 10.0},
        performed_by="nurse-001",
        performed_at=datetime(2024, 1, 15, 10, 30),
    )
    resource = client.build_wound_observation(obs)

    assert resource["resourceType"] == "Observation"
    assert resource["status"] == "final"
    assert resource["subject"]["reference"] == "Patient/patient-123"
    assert len(resource["component"]) >= 3
    assert any(c["code"]["coding"][0]["code"] == "length" for c in resource["component"])
    assert any(c["code"]["coding"][0]["code"] == "area" for c in resource["component"])


def test_fhir_tissue_extension():
    """FHIR resource should include tissue composition extension."""
    client = FHIRClient(base_url="https://fhir.example.com", api_key="test-key")
    obs = FHIRObservation(
        patient_id="p1",
        wound_id="w1",
        scan_id="s1",
        measurements={"length_cm": 2.0, "width_cm": 1.5, "area_cm2": 2.36},
        tissue_composition={"granulation_pct": 70.0, "slough_pct": 20.0, "eschar_pct": 10.0},
        performed_by="user-1",
        performed_at=datetime.utcnow(),
    )
    resource = client.build_wound_observation(obs)

    tissue_ext = next(
        (e for e in resource.get("extension", [])
         if "tissue-composition" in e.get("url", "")),
        None,
    )
    assert tissue_ext is not None
    granulation_ext = next(
        (e for e in tissue_ext["extension"] if e["url"] == "granulation"),
        None,
    )
    assert granulation_ext is not None
    assert granulation_ext["valueDecimal"] == 70.0
