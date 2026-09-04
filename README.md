# Gleason Grade Group Mapper

> **Domain:** Digital Pathology & Quantitative Histopathology
> **Reference Guidelines & Standards:** College of American Pathologists (CAP) Synoptic Protocols & DICOM WSI

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Gleason Grade Group & NCCN Risk Stratification Mapper

Implements the ISUP 2014 Grade Group system for prostate cancer and
NCCN risk stratification for treatment planning.

References:
  - Epstein JI et al. Am J Surg Pathol. 2016;40(2):244-252 (ISUP 2014)
  - NCCN Clinical Practice Guidelines in Oncology: Prostate Cancer (v4.2024)
  - Pierorazio PM et al. Eur Urol. 2013;63(1):116-122

License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`map_gleason_to_grade_group()`**: Map Gleason patterns to ISUP 2014 Grade Group.

Parameters
----------
primary_pattern : int
    Primary (most prevalent) Gleason pattern (1-5).
secondary_pattern : int
    Secondary (second most prevalent) Gleason pattern (1-5).
tertiary_pattern : int, optional
    Tertiary (highest) pattern if present. If provided and higher than
    secondary, the score uses primary + tertiary for grade group.

Returns
-------
dict with gleason_score, grade_group, grade_group_label, risk_category,
description, prognosis

- **`nccn_risk_stratification()`**: NCCN risk stratification for prostate cancer.

Parameters
----------
grade_group : int
    ISUP Grade Group (1-5).
psa : float
    PSA level in ng/mL.
t_stage : str
    Clinical T stage (e.g., 'T1c', 'T2a', 'T2b', 'T2c', 'T3a', 'T3b', 'T4').
num_positive_cores : int, optional
    Number of biopsy cores positive for cancer.
total_cores : int, optional
    Total number of cores taken.
max_percent_per_core : float, optional
    Maximum percentage of cancer in any single core (0-100).

Returns
-------
dict with risk_group, risk_category, criteria_met, treatment_options

- **`process_batch()`**: Process a CSV of prostate cancer cases.

Expected columns: primary_pattern, secondary_pattern, psa, t_stage
Optional: tertiary_pattern, num_positive_cores, total_cores, max_percent_per_core

---

## 📐 Mathematical Formulation & Logic

```text
  gleason_score = primary_pattern + secondary_pattern
  grade_group = f(gleason_score, primary_pattern, secondary_pattern)
  risk = nccn_risk_stratification(grade_group, psa, t_stage, ...)
```

---

## 💻 CLI Quickstart & Usage

### Installation

```bash
pip install -r requirements.txt
```

### 1. Grade Group Mapping
```bash
python cli.py grade --primary 3 --secondary 4
```

### 2. NCCN Risk Stratification
```bash
python cli.py risk --grade-group 2 --psa 15.0 --t-stage T2b
```

### 3. Full Assessment (Grade + Risk)
```bash
python cli.py assess --primary 4 --secondary 3 --psa 15.0 --t-stage T2b
```

### 4. Batch Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 5. Enterprise Supervisor (Audit)
```bash
python cli.py audit --task-id TASK-001 --primary-metric 12.0
```

### 6. Supervisory Chat
```bash
python cli.py chat "Explain the ISUP Grade Group system"
```

### 7. Verify Audit Trail
```bash
python cli.py verify-audit
```

### 8. Start REST Server
```bash
python cli.py serve --host 0.0.0.0 --port 8000
```

### Command Reference
- `grade`: Map Gleason patterns to Grade Group
- `risk`: NCCN risk stratification
- `assess`: Full grade + risk assessment
- `batch`: Batch process CSV file
- `audit`: Dispatch task to enterprise supervisor
- `chat`: Enterprise supervisory chat
- `verify-audit`: Verify HMAC audit trail integrity
- `serve`: Start FastAPI REST server

### Input Data Schema (for batch processing)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `primary_pattern` | Primary Gleason pattern (1-5) | Required |
| `secondary_pattern` | Secondary Gleason pattern (1-5) | Required |
| `psa` | PSA level in ng/mL | Required |
| `t_stage` | Clinical T stage (e.g., T1c, T2a, T3a) | Required |
| `tertiary_pattern` | Tertiary pattern if present | Optional |
| `num_positive_cores` | Number of positive biopsy cores | Optional |
| `total_cores` | Total cores taken | Optional |
| `max_percent_per_core` | Max % cancer in any core (0-100) | Optional |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Security Configuration

Set the `AUDIT_SECRET_KEY` environment variable for persistent audit trail integrity:

```bash
# Linux/macOS
export AUDIT_SECRET_KEY="your-secure-random-key"

# Windows
set AUDIT_SECRET_KEY=your-secure-random-key
```

If not set, an ephemeral random key is used (audit trail won't persist across restarts).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute the enterprise simulation:

```bash
python simulator.py 100
```

---

## 🐳 Container Deployment

```bash
docker build -t gleason-grade-group-mapper .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key gleason-grade-group-mapper
```

Or using Docker Compose:

```bash
AUDIT_SECRET_KEY=your-secret-key docker-compose up -d
```

---

## 📁 Project Structure

```
gleason-grade-group-mapper/
├── gleason_mapper.py      # Core logic: grade group mapping, NCCN risk, CLI
├── cli.py                 # CLI entry point
├── enrichment.py          # Enrichment engines (longitudinal tracking, etc.)
├── simulator.py           # Enterprise simulation/testing
├── agents/                # Enterprise agent framework
│   ├── __init__.py
│   ├── api.py            # FastAPI REST server
│   ├── base.py           # Security, PHI guard, HMAC audit trail
│   ├── models.py         # Pydantic schemas
│   ├── supervisor.py     # Supervisor orchestrator
│   ├── workers.py        # Specialized domain workers
│   ├── llm_factory.py    # LLM provider factory
│   ├── learning.py       # Bayesian calibration engine
│   ├── metrics.py        # Prometheus metrics collector
│   └── streamer.py       # WebSocket telemetry streamer
├── tests/                 # Test suites
│   ├── test_gleason_grade_group_mapper.py
│   └── test_enrichment.py
├── test_gleason_mapper.py # Core gleason mapper tests
├── web/
│   └── index.html        # Operations console UI
├── requirements.txt       # Python dependencies
├── Dockerfile
├── docker-compose.yml
├── sample.csv             # Sample input data
└── openapi_spec.json      # OpenAPI specification
```
