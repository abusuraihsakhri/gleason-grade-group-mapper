# Gleason Grade Group Mapper

> **Domain:** Digital Pathology & Quantitative Histopathology  
> **Reference Guidelines & Standards:** `College of American Pathologists (CAP) Synoptic Protocols & DICOM WSI`

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

Zero-dependency Python implementation (stdlib only).
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
- **`main()`** — calculates and validates main parameters.

---

## 📐 Mathematical Formulation & Logic

```text
  gleason_score = primary_pattern + secondary_pattern
  risk = "Low risk"
  risk = "Favorable intermediate risk"
  risk = "Unfavorable intermediate risk"
  risk = "High risk"
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --input data.csv
```

### Parameter Reference
- `--interactive`: Launch guided terminal interactive wizard.
- `--input <path>`: Evaluate input from JSON or CSV specification.
- `--json`: Output deterministic structured results in JSON format.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Parameter / observation metric | Required |
| `v1` | Parameter / observation metric | Required |
| `v2` | Parameter / observation metric | Required |
| `v3` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t gleason-grade-group-mapper .
docker run -p 8000:8000 gleason-grade-group-mapper
```
