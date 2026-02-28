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

## 🎬 Demo — Happy Flow Walkthrough

A demo physician account and a sample patient/wound are created automatically
when the server starts for the first time.

| Account | Email | Password |
|---|---|---|
| Admin | `admin@nopressure.demo` | `Admin1234!` |
| Physician (demo) | `demo@nopressure.demo` | `Demo1234!` |

Follow the steps below with `curl` (or use the interactive Swagger UI at
`http://localhost:8000/docs`).

---

### Step 1 — Log in and obtain a JWT

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@nopressure.demo","password":"Demo1234!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Token: $TOKEN"
```

---

### Step 2 — View the pre-seeded demo patient

```bash
curl -s http://localhost:8000/api/v1/patients/ \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

The response includes **John Demo** (MRN `DEMO-MRN-001`).  
Copy the patient `id` for use in later steps:

```bash
PATIENT_ID=<paste patient id here>
```

---

### Step 3 — View the pre-seeded wound

```bash
curl -s "http://localhost:8000/api/v1/wounds/patient/$PATIENT_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Copy the wound `id`:

```bash
WOUND_ID=<paste wound id here>
```

---

### Step 4 — Upload a wound scan (AI analysis)

```bash
# Create a minimal test image (any JPEG/PNG will work)
echo "fake-image-bytes" > /tmp/demo_wound.jpg

curl -s -X POST "http://localhost:8000/api/v1/scans/$WOUND_ID/scan" \
  -H "Authorization: Bearer $TOKEN" \
  -F "patient_id=$PATIENT_ID" \
  -F "scanned_by=demo_physician" \
  -F "capture_angle=90" \
  -F "has_calibration_marker=true" \
  -F "clinical_notes=Initial assessment during demo" \
  -F "image=@/tmp/demo_wound.jpg;type=image/jpeg" \
  | python3 -m json.tool
```

The response includes AI-generated measurements, tissue segmentation,
severity score, NPIAP stage, and a treatment recommendation.  
Copy the scan `id`:

```bash
SCAN_ID=<paste scan id here>
```

---

### Step 5 — Clinician confirms the AI result

```bash
curl -s -X PATCH "http://localhost:8000/api/v1/scans/$SCAN_ID/confirm" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"confirmed_by":"demo_physician"}' | python3 -m json.tool
```

---

### Step 6 — View healing trend analytics

```bash
curl -s "http://localhost:8000/api/v1/analytics/wound/$WOUND_ID/trend" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### Step 7 — View the full scan timeline

```bash
curl -s "http://localhost:8000/api/v1/analytics/wound/$WOUND_ID/timeline" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### Step 8 — Download a PDF wound report

```bash
curl -s "http://localhost:8000/api/v1/analytics/wound/$WOUND_ID/report" \
  -H "Authorization: Bearer $TOKEN" \
  -o /tmp/wound_report.pdf
echo "Report saved to /tmp/wound_report.pdf"
```

---

### Step 9 — View the facility dashboard

```bash
curl -s "http://localhost:8000/api/v1/analytics/facility/demo-facility-1/dashboard" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### Step 10 — Register a new user (admin only)

```bash
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@nopressure.demo","password":"Admin1234!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nurse@demo.hospital",
    "username": "demo_nurse",
    "password": "Nurse1234!",
    "full_name": "Demo Nurse",
    "role": "nurse",
    "facility_id": "demo-facility-1"
  }' | python3 -m json.tool
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
