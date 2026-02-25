# NoPressure 🩹

**Digitally wound-scanning and skin-condition monitoring solution**

A HIPAA/GDPR-compliant clinical platform for AI-powered wound scanning, tissue segmentation, healing trend analytics, and EHR/EMR integration.

---

## Features

### 🔬 Core Scanning & AI Engine
- **3D Volumetric Imaging** — Photogrammetry/LiDAR-based wound measurement (length, width, area, depth) with <5% margin of error
- **AI Tissue Segmentation** — Automated classification of granulation (red), slough (yellow), and eschar (black/necrotic) tissue
- **Sub-Epidermal Analysis** — Early-stage pressure ulcer detection (Stage 1) via persistent redness and thermal sensor integration
- **Auto-Calibration** — Physical scale/visual marker detection for accurate measurements regardless of camera distance

### 🏥 Clinical Workflow
- **Guided Capture Interface** — 90° angle enforcement, focus/lighting checks, calibration marker validation
- **Smart Wound Labeling** — Pre-defined taxonomy (Diabetic Foot Ulcer, Venous Leg Ulcer, Surgical Site Infection, etc.)
- **Body Map** — Interactive 3D anatomical mannequin for multi-site wound tracking
- **Voice-to-Text Notes** — Hands-free clinical documentation during dressing changes

### 📊 Data Management & Decision Support
- **Healing Trend Analytics** — Automatic PAR (Percentage Area Reduction) calculation; stalled wound alert if <20% reduction in 4 weeks
- **Treatment Recommendation Engine** — Evidence-based dressing and intervention suggestions (e.g., "High exudate → Alginate dressing")
- **Time-Lapse Comparison** — Side-by-side or animated wound progression from Day 1 to present

### 🔒 Security & Compliance
- **HIPAA/GDPR Compliance** — AES-256 encryption at rest, TLS 1.3 in transit
- **Zero-Footprint Storage** — Images uploaded directly to encrypted cloud; never saved to device gallery
- **EHR/EMR Integration** — HL7/FHIR R4 support for Epic, Cerner, and Israeli HMO systems
- **Offline Mode** — Scan and save in dead zones (basement wards, rural visits) with automatic cloud sync

### ⚙️ Administration
- **Centralized Dashboard** — Facility-wide wound burden at a glance for head nurses/physicians
- **Audit Trail** — HIPAA-compliant logging of every scan, view, and modification
- **Resource Management** — Dressing inventory tracking with usage-based restocking forecasts

---

## Project Structure

```
NoPressure-/
├── frontend/
│   └── index.html              # Self-contained SPA (no build required)
└── backend/
    ├── requirements.txt
    └── app/
        ├── main.py              # FastAPI application entry point
        ├── core/
        │   ├── config.py        # Settings (HIPAA, FHIR, thresholds)
        │   └── security.py      # JWT auth, bcrypt password hashing
        ├── models/
        │   ├── patient.py       # Patient model (PHI fields)
        │   ├── wound.py         # Wound model (etiology, body map, stall detection)
        │   ├── scan.py          # Scan + AuditLog models
        │   └── user.py          # User roles (nurse, physician, admin)
        ├── services/
        │   ├── ai_engine.py     # Tissue segmentation, wound measurement, PAR
        │   ├── treatment_engine.py  # Evidence-based treatment recommendations
        │   ├── analytics.py     # Healing trends, facility dashboard
        │   ├── ehr_integration.py   # HL7/FHIR R4 client
        │   └── offline_sync.py  # Offline queue with auto-sync
        └── api/
            ├── patients.py      # Patient CRUD endpoints
            ├── wounds.py        # Wound management + body map
            ├── scans.py         # Image upload → AI analysis → scan record
            └── analytics.py     # Healing trends + facility dashboard
```

---

## Quick Start

### Frontend (no build required)
Open `frontend/index.html` directly in any modern browser.

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API documentation available at: http://localhost:8000/docs

### Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## API Overview

| Endpoint | Method | Description |
|---|---|---|
| `POST /api/v1/patients/` | POST | Register new patient |
| `GET /api/v1/patients/{id}` | GET | Get patient details |
| `POST /api/v1/wounds/` | POST | Create wound record |
| `PATCH /api/v1/wounds/{id}/location` | PATCH | Pin wound on body map |
| `POST /api/v1/scans/{wound_id}/scan` | POST | Upload image → AI scan |
| `GET /api/v1/scans/wound/{wound_id}` | GET | Wound scan history |
| `GET /api/v1/analytics/wound/{id}/trend` | GET | Healing trend + PAR |
| `GET /api/v1/analytics/facility/{id}/dashboard` | GET | Facility command center |

---

## Compliance

- **HIPAA** — PHI encrypted at rest (AES-256) and in transit (TLS 1.3)
- **GDPR** — Data minimisation, right to erasure, audit trail
- **FHIR R4** — Wound observations pushed as FHIR `Observation` resources
- **Zero-footprint** — No PHI or images stored on end-user devices
