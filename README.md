# Laboratory LIMS

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![Domain](https://img.shields.io/badge/domain-Laboratory%20QC-8b5cf6.svg)]()
[![Tests](https://img.shields.io/badge/tests-68%20passing-brightgreen.svg)]()

> **P109** — Generic Laboratory Information Management System (LIMS) for pharmaceutical and analytical QA labs. Manages samples, tests, instruments, and reagent inventory with a full REST API and dark-theme web dashboard.

---

## The Problem

Analytical and QA laboratories operate across four domains simultaneously: incoming samples awaiting testing, in-progress analytical and microbiological tests, instrument calibration tracking, and reagent/consumable inventory management. Without a central system these are tracked in spreadsheets, paper registers, and email chains — leading to missed calibration dates, expired reagents being used, lost sample chains, and OOS results not being escalated on time.

**Laboratory LIMS** centralises all four domains in a single Flask application with SQLite persistence, filterable list views, a live triage dashboard, and a REST API for integration with upstream systems.

---

## What It Does

**1. Sample Tracking** — Receive, track, and release laboratory samples with full chain of custody. Supports Drug Substance, Drug Product, Raw Material, Environmental, and Water sample types. Priority levels (Critical / High / Routine) highlight urgent work.

**2. Test Management** — Register analytical and microbiological tests against samples, record results against specifications, and track pass/fail outcomes. Filterable by status (Requested / In Progress / Completed / Approved / Failed) and analyst.

**3. Instrument Register** — Track all laboratory equipment with calibration dates, calibration method references, serial numbers, and status. Instruments due for calibration or out of service surface automatically on the dashboard.

**4. Reagent & Inventory Management** — Manage reagent stock by lot number, catalog number, expiry date, quantity, and storage location. Expired and low-stock reagents are flagged automatically.

**5. Triage Dashboard** — Live KPI tiles for open samples, pending tests, calibration status, and inventory alerts. Bars charts for sample distribution by type and status.

**6. REST API** — Full JSON API for all four domains with filtering, detail retrieval, and dashboard statistics.

---

## Architecture

```
Laboratory-LIMS/
│
├── lims/
│   ├── app.py               # Flask factory — web routes + REST API
│   ├── model.py             # SQLite persistence (4 tables)
│   ├── seed.py              # Auto-seeds on first launch
│   └── templates/
│       ├── base.html        # Dark theme, navigation
│       ├── dashboard.html   # KPI tiles, attention queue
│       ├── samples.html     # Filterable sample list
│       ├── sample_detail.html # Sample + linked tests
│       ├── tests.html       # Filterable test list
│       ├── instruments.html # Instrument register + calibration status
│       └── reagents.html    # Reagent inventory + expiry tracking
│
├── data/
│   └── mock_data.py         # 10 samples, 10 tests, 8 instruments, 10 reagents
│
├── tests/
│   └── test_lims.py         # 68 tests across 4 test classes
│
├── run.py                   # Entrypoint (port 5109)
└── requirements.txt         # Flask + pytest
```

**Data flow:**

```
Sample registered → Tests requested → Results recorded → Pass/Fail assessed
       │
       └── Instruments tracked (calibration)
       └── Reagents consumed (lot, expiry, stock level)
       └── Dashboard: live triage view
       └── REST API: JSON for integration
```

---

## Database Schema

| Table | Key Fields | Purpose |
|-------|-----------|---------|
| `samples` | sample_id, barcode, sample_type, status, priority | Sample chain of custody |
| `tests` | test_id, sample_id (FK), test_name, method, result, pass_fail | Analytical + microbiological test results |
| `instruments` | instrument_id, status, last_calibration, next_calibration | Equipment register + calibration tracking |
| `reagents` | reagent_id, lot_number, expiry_date, quantity, status | Inventory with expiry and stock level |

---

## Sample Types

| Type | Examples |
|------|---------|
| Drug Substance | API bulk, in-process samples |
| Drug Product | Filled vials, final containers |
| Raw Material | Excipients, solvents, buffer salts |
| Environmental | Settle plates, surface swabs, active air |
| Water | WFI, Purified Water, RO permeate |

---

## Sample Statuses

| Status | Meaning |
|--------|---------|
| Received | Sample logged; awaiting test assignment |
| In Progress | Tests actively being run |
| Pending Review | Results available; QA review required |
| Approved | Results reviewed and approved |
| Released | Sample released; CoA issued |
| Rejected | Sample or results rejected |

---

## Instrument Statuses

| Status | Meaning |
|--------|---------|
| Active | In service; calibration current |
| Due for Calibration | Within calibration period but due soon |
| Out of Service | Removed from service; not to be used |
| Retired | Permanently decommissioned |

---

## Mock Data (seeded on first launch)

### Samples

| ID | Type | Description | Priority | Status |
|----|------|-------------|----------|--------|
| S-2024-0001 | Drug Substance | API bulk — in-process purity | High | Released |
| S-2024-0002 | Environmental | Grade B settle plate | High | In Progress |
| S-2024-0003 | Water | WFI Point-of-Use 4 | Routine | Pending Review |
| S-2024-0004 | Drug Product | Sterility — aseptic fill vials | Critical | In Progress |
| S-2024-0005 | Raw Material | Polysorbate 80 identity | Routine | Received |
| S-2024-0006 | Drug Substance | Stability 12-month time point | High | In Progress |
| S-2024-0007 | Environmental | Isolator glove port swab | High | In Progress |
| S-2024-0008 | Water | RO system permeate | Routine | Pending Review |
| S-2024-0009 | Drug Product | Endotoxin — DP lot 24-MFG-089 | Critical | Received |
| S-2024-0010 | Raw Material | Reference standard qualification | High | Received |

### Tests

| ID | Test Name | Method | Status |
|----|-----------|--------|--------|
| T-2024-0001 | Purity by HPLC | QC-HPLC-001 | Approved |
| T-2024-0002 | Residual Solvents by GC-HS | QC-GC-003 | Approved |
| T-2024-0003 | Viable Environmental Monitoring | QC-ENV-010 | In Progress |
| T-2024-0004 | Conductivity | QC-WTR-002 | Completed |
| T-2024-0005 | Endotoxin by LAL (Kinetic Turbidimetric) | QC-LAL-001 | Completed |
| T-2024-0006 | Sterility Test (Membrane Filtration) | QC-STR-001 | In Progress |
| T-2024-0007 | Identity by IR Spectroscopy | QC-ID-004 | Requested |
| T-2024-0008 | Potency by Cell-Based Assay | QC-BIO-007 | In Progress |
| T-2024-0009 | Total Viable Count (surface swab) | QC-ENV-012 | In Progress |
| T-2024-0010 | Endotoxin by LAL (Kinetic Chromogenic) | QC-LAL-002 | Requested |

### Instruments

| ID | Instrument | Status |
|----|-----------|--------|
| INS-001 | Agilent 1260 HPLC | Active |
| INS-002 | Agilent 7890B GC-HS | Active |
| INS-003 | Charles River Endosafe LAL Reader | Active |
| INS-004 | Mettler Toledo XPR205 Balance | Due for Calibration |
| INS-005 | Getinge HS66 Autoclave | Active |
| INS-006 | Thermo NanoDrop One UV-Vis | Active |
| INS-007 | Binder KBF 240 Stability Chamber | Active |
| INS-008 | Mettler Toledo SevenExcellence pH Meter | Out of Service |

---

## Quickstart

```bash
git clone https://github.com/timjm25/Laboratory-LIMS.git
cd Laboratory-LIMS

pip install -r requirements.txt

python run.py
# → http://127.0.0.1:5109
```

The system auto-seeds all mock data (10 samples, 10 tests, 8 instruments, 10 reagents) and is ready to use on first launch.

---

## Dashboard Pages

| Route | Description |
|-------|-------------|
| `/` | Triage dashboard: KPI tiles, sample/test breakdowns, attention queue |
| `/samples` | Full sample list with type / status / priority / client filters |
| `/sample/<id>` | Sample detail: metadata, storage, linked tests with results |
| `/tests` | All tests with status / analyst / pass-fail filters |
| `/instruments` | Equipment register with calibration status — sorted by next calibration |
| `/reagents` | Reagent inventory with expiry tracking — sorted by expiry date |

---

## REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/samples` | List all samples (filterable) |
| `GET` | `/api/v1/sample/<id>` | Sample + linked tests |
| `GET` | `/api/v1/tests` | List all tests (filterable) |
| `GET` | `/api/v1/instruments` | List all instruments (filterable) |
| `GET` | `/api/v1/reagents` | List all reagents (filterable) |
| `GET` | `/api/v1/stats` | Dashboard statistics |
| `GET` | `/healthz` | Health check |

### Query Parameters

**`/api/v1/samples`**

| Parameter | Values |
|-----------|--------|
| `sample_type` | Drug Substance, Drug Product, Raw Material, Environmental, Water |
| `status` | Received, In Progress, Pending Review, Approved, Released, Rejected |
| `priority` | Critical, High, Routine |
| `client` | Manufacturing, Quality Assurance, Quality Control, Engineering, … |

**`/api/v1/tests`**

| Parameter | Values |
|-----------|--------|
| `status` | Requested, In Progress, Completed, Reviewed, Approved, Failed |
| `assigned_to` | Analyst name |
| `pass_fail` | Pass, Fail |

**`/api/v1/instruments`**

| Parameter | Values |
|-----------|--------|
| `status` | Active, Due for Calibration, Out of Service, Retired |
| `department` | Quality Control, Manufacturing, Engineering |

**`/api/v1/reagents`**

| Parameter | Values |
|-----------|--------|
| `status` | In Stock, Low Stock, Expired, Quarantined, Depleted |
| `category` | Solvent, Acid/Modifier, Reagent Kit, Reference Standard, Culture Media, Buffer, … |

### Examples

```bash
# Dashboard stats
curl http://127.0.0.1:5109/api/v1/stats

# All Critical-priority samples
curl "http://127.0.0.1:5109/api/v1/samples?priority=Critical"

# All in-progress tests
curl "http://127.0.0.1:5109/api/v1/tests?status=In+Progress"

# Instruments due for calibration
curl "http://127.0.0.1:5109/api/v1/instruments?status=Due+for+Calibration"

# Expired reagents
curl "http://127.0.0.1:5109/api/v1/reagents?status=Expired"

# Sample detail with linked tests
curl http://127.0.0.1:5109/api/v1/sample/S-2024-0004
```

---

## Adding a Sample

Add a dict to `data/mock_data.py` in the `MOCK_SAMPLES` list:

```python
{
    "sample_id": "S-2024-0011",
    "barcode": "LB100011",
    "sample_type": "Drug Product",              # see Sample Types table
    "description": "Endotoxin — lot DP-2024-101",
    "client": "Quality Control",
    "project": "PRJ-MFG-2024-09",
    "received_date": "2026-06-26",
    "received_by": "Analyst Name",
    "storage_location": "Ambient store AS-01, Bay 3",
    "status": "Received",                       # see Sample Statuses table
    "priority": "Critical",                     # Critical | High | Routine
    "volume": "3 × 2 mL vials",
    "matrix": "Aqueous drug product",
}
```

Restart the app to pick up the new entry on next seed.

---

## Testing

```bash
python3 -m pytest tests/ -v
# 68 tests — MockData, Model, FlaskRoutes, RestAPI
```

Tests cover:

- **TestMockData (18)** — corpus size, unique IDs, required fields, valid statuses, cross-referential integrity (test sample_ids reference valid samples)
- **TestModel (23)** — seed counts, is_seeded, get by ID, filter by all parameters, status update, status validation, dashboard stats structure + totals, ordering guarantees (instruments by calibration date, reagents by expiry)
- **TestFlaskRoutes (15)** — all pages, filters, 404, status update redirect
- **TestRestAPI (12)** — all endpoints, filter parameters, 404, stats structure

---

## License

MIT License — see [LICENSE](LICENSE).

Copyright (c) 2026 Tim Maguire.
