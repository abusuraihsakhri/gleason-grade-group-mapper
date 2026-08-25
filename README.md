# Gleason Grade Group & NCCN Risk Stratification Mapper

> **Prostate Cancer Grading and Risk Assessment**
> Reference: Epstein JI et al. Am J Surg Pathol. 2016;40(2):244-252 (ISUP 2014)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg)

## Overview

Real implementation of the ISUP 2014 Gleason Grade Group system and NCCN risk stratification for prostate cancer:

- **Grade Group mapping** from Gleason primary + secondary patterns (1-5)
- **NCCN risk stratification**: Very Low, Low, Favorable Intermediate, Unfavorable Intermediate, High, Very High
- **Treatment recommendations** by risk group per NCCN guidelines
- **Tertiary pattern** handling with risk upgrade consideration

## Quick Start

```bash
# Map Gleason patterns to Grade Group
python gleason_mapper.py grade --primary 4 --secondary 3

# NCCN risk stratification
python gleason_mapper.py risk --grade-group 2 --psa 8.0 --t-stage T2a

# Full assessment
python gleason_mapper.py assess --primary 3 --secondary 4 --psa 5.0 --t-stage T1c \
    --positive-cores 2 --total-cores 12 --max-percent 30

# Batch processing
python gleason_mapper.py batch -i cases.csv -o results.csv
```

## ISUP 2014 Grade Groups

| Grade Group | Gleason Score | Pattern | Risk | Prognosis |
|-------------|---------------|---------|------|-----------|
| 1 | 3+3=6 | Well-differentiated | Low | Excellent |
| 2 | 3+4=7 | Predominantly well-differentiated | Favorable Intermediate | Good |
| 3 | 4+3=7 | Predominantly cribriform | Unfavorable Intermediate | Intermediate |
| 4 | 4+4=8, 3+5=8, 5+3=8 | Poorly differentiated | High | Poor |
| 5 | 9-10 | Undifferentiated | Highest | Very poor |

## NCCN Risk Groups

| Risk Group | Criteria | Primary Treatment Options |
|------------|----------|--------------------------|
| Very Low | T1c, GG1, PSA <10, <3 cores, ≤50%/core | Active surveillance |
| Low | T1-T2a, GG1, PSA <10 | Active surveillance, surgery, radiation |
| Favorable Intermediate | T2b-T2c, GG1-2, PSA 10-20 | Active surveillance (selected), surgery, radiation + short ADT |
| Unfavorable Intermediate | GG3 or PSA 10-20 or T2b-T2c | Surgery + PLND, radiation + short ADT |
| High | T3a or GG4-5 or PSA >20 | Surgery + PLND, radiation + long ADT |
| Very High | T3b-T4 or GG5 with >4 cores | Radiation + long ADT, clinical trials |

## Python API

```python
from gleason_mapper import map_gleason_to_grade_group, nccn_risk_stratification

# Grade group
result = map_gleason_to_grade_group(primary_pattern=4, secondary_pattern=3)
print(result["grade_group"])  # 3
print(result["gleason_score"])  # 7

# Risk stratification
result = nccn_risk_stratification(grade_group=1, psa=5.0, t_stage="T1c",
                                   num_positive_cores=2, total_cores=12,
                                   max_percent_per_core=30.0)
print(result["risk_group"])  # "Very Low Risk"
print(result["treatment_options"])  # ["Active surveillance (preferred)", ...]
```

## Running Tests

```bash
python -m pytest test_gleason_mapper.py -v
```

## License

MIT License. See [LICENSE](LICENSE) for details.
