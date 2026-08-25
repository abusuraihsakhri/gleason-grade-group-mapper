#!/usr/bin/env python3
"""
Gleason Grade Group & NCCN Risk Stratification Mapper

Implements the ISUP 2014 Grade Group system for prostate cancer and
NCCN risk stratification for treatment planning.

References:
  - Epstein JI et al. Am J Surg Pathol. 2016;40(2):244-252 (ISUP 2014)
  - NCCN Clinical Practice Guidelines in Oncology: Prostate Cancer (v4.2024)
  - Pierorazio PM et al. Eur Urol. 2013;63(1):116-122

Zero-dependency Python implementation (stdlib only).
License: MIT
"""

import argparse
import csv
import json
import sys
from typing import Dict, Any, Optional, List


# ---------------------------------------------------------------------------
# Gleason Score & Grade Group Mapping
# ---------------------------------------------------------------------------

def map_gleason_to_grade_group(primary_pattern: int, secondary_pattern: int,
                                tertiary_pattern: Optional[int] = None) -> Dict[str, Any]:
    """
    Map Gleason patterns to ISUP 2014 Grade Group.

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
    """
    for name, val in [("primary_pattern", primary_pattern),
                       ("secondary_pattern", secondary_pattern)]:
        if not isinstance(val, int) or val < 1 or val > 5:
            raise ValueError(f"{name} must be integer 1-5; got {val}")
    if tertiary_pattern is not None:
        if not isinstance(tertiary_pattern, int) or tertiary_pattern < 1 or tertiary_pattern > 5:
            raise ValueError(f"tertiary_pattern must be integer 1-5; got {tertiary_pattern}")

    gleason_score = primary_pattern + secondary_pattern

    # Grade Group determination based on ISUP 2014
    if primary_pattern == 3 and secondary_pattern == 3:
        grade_group = 1
        label = "Grade Group 1"
        risk = "Low risk"
        description = "Gleason 3+3=6. Well-differentiated, individual glands."
        prognosis = "Excellent. Most indolent form of prostate cancer."
    elif primary_pattern == 3 and secondary_pattern == 4:
        grade_group = 2
        label = "Grade Group 2"
        risk = "Favorable intermediate risk"
        description = "Gleason 3+4=7. Predominantly well-differentiated with some cribriform/fused glands."
        prognosis = "Good. Generally favorable outcome with appropriate treatment."
    elif primary_pattern == 4 and secondary_pattern == 3:
        grade_group = 3
        label = "Grade Group 3"
        risk = "Unfavorable intermediate risk"
        description = "Gleason 4+3=7. Predominantly cribriform/fused glands with some well-differentiated."
        prognosis = "Intermediate. Higher risk of progression than 3+4."
    elif (primary_pattern == 4 and secondary_pattern == 4) or \
         (primary_pattern == 3 and secondary_pattern == 5) or \
         (primary_pattern == 5 and secondary_pattern == 3):
        grade_group = 4
        label = "Grade Group 4"
        risk = "High risk"
        description = f"Gleason {primary_pattern}+{secondary_pattern}=8. Poorly differentiated."
        prognosis = "Poor without aggressive treatment. Significant risk of metastasis."
    elif (primary_pattern + secondary_pattern) >= 9:
        grade_group = 5
        label = "Grade Group 5"
        risk = "Highest risk"
        description = f"Gleason {primary_pattern}+{secondary_pattern}={gleason_score}. Undifferentiated."
        prognosis = "Very poor. Highest risk of metastasis and mortality."
    else:
        # Handle unusual combinations (e.g., 2+3, 2+2, etc.)
        if gleason_score <= 6:
            grade_group = 1
            label = "Grade Group 1"
            risk = "Low risk"
            description = f"Gleason {primary_pattern}+{secondary_pattern}={gleason_score}. Note: patterns 1-2 are rarely assigned in modern practice."
            prognosis = "Excellent if confirmed."
        elif gleason_score == 7:
            grade_group = 2
            label = "Grade Group 2"
            risk = "Favorable intermediate risk"
            description = f"Gleason {primary_pattern}+{secondary_pattern}=7."
            prognosis = "Good."
        elif gleason_score == 8:
            grade_group = 4
            label = "Grade Group 4"
            risk = "High risk"
            description = f"Gleason {primary_pattern}+{secondary_pattern}=8."
            prognosis = "Poor without aggressive treatment."
        else:
            grade_group = 5
            label = "Grade Group 5"
            risk = "Highest risk"
            description = f"Gleason {primary_pattern}+{secondary_pattern}={gleason_score}."
            prognosis = "Very poor."

    result = {
        "primary_pattern": primary_pattern,
        "secondary_pattern": secondary_pattern,
        "gleason_score": gleason_score,
        "grade_group": grade_group,
        "grade_group_label": label,
        "risk_category": risk,
        "description": description,
        "prognosis": prognosis,
    }

    if tertiary_pattern is not None:
        result["tertiary_pattern"] = tertiary_pattern
        if tertiary_pattern > secondary_pattern:
            result["note"] = (
                f"Tertiary pattern {tertiary_pattern} is higher than secondary {secondary_pattern}. "
                "Consider upgrading risk assessment."
            )

    return result


# ---------------------------------------------------------------------------
# NCCN Risk Stratification
# ---------------------------------------------------------------------------

def nccn_risk_stratification(grade_group: int, psa: float, t_stage: str,
                              num_positive_cores: Optional[int] = None,
                              total_cores: Optional[int] = None,
                              max_percent_per_core: Optional[float] = None) -> Dict[str, Any]:
    """
    NCCN risk stratification for prostate cancer.

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
    """
    if grade_group < 1 or grade_group > 5:
        raise ValueError(f"grade_group must be 1-5; got {grade_group}")
    if psa < 0:
        raise ValueError(f"psa must be >= 0; got {psa}")

    t = t_stage.upper().strip()

    # Determine risk group - check from HIGHEST risk down to LOWEST
    # so that the most severe classification takes priority
    risk_group = None
    criteria = []

    # Very High Risk (check first - highest priority)
    if t in ("T3B", "T4") or (grade_group == 5 and num_positive_cores is not None and num_positive_cores > 4):
        risk_group = "Very High Risk"
        criteria = [
            f"T-stage: {t_stage}",
            f"Grade Group: {grade_group}",
            f"PSA: {psa} ng/mL",
        ]

    # High Risk
    if risk_group is None:
        if t == "T3A" or grade_group in (4, 5) or psa > 20:
            risk_group = "High Risk"
            criteria = [
                f"T-stage: {t_stage}",
                f"Grade Group: {grade_group}",
                f"PSA: {psa} ng/mL",
            ]

    # Unfavorable Intermediate Risk
    if risk_group is None:
        if grade_group == 3 or (10 <= psa < 20) or t in ("T2B", "T2C"):
            risk_group = "Unfavorable Intermediate Risk"
            criteria = [
                f"T-stage: {t_stage}",
                f"Grade Group: {grade_group}",
                f"PSA: {psa} ng/mL",
            ]

    # Favorable Intermediate Risk
    if risk_group is None:
        if (grade_group in (1, 2) and
            10 <= psa < 20 and
            t in ("T2B", "T2C")):
            risk_group = "Favorable Intermediate Risk"
            criteria = [
                f"T-stage: {t_stage} (T2b-T2c)",
                f"Grade Group: {grade_group} (1-2)",
                f"PSA: {psa} ng/mL (10-20)",
            ]

    # Very Low Risk (more specific subset of Low Risk - check first)
    if risk_group is None:
        if (grade_group == 1 and psa < 10 and
            t in ("T1C",) and
            num_positive_cores is not None and num_positive_cores < 3 and
            max_percent_per_core is not None and max_percent_per_core <= 50):
            risk_group = "Very Low Risk"
            criteria = [
                f"T-stage: {t_stage}",
                f"Grade Group: {grade_group}",
                f"PSA: {psa} ng/mL",
                f"Positive cores: {num_positive_cores} (<3)",
                f"Max core involvement: {max_percent_per_core}% (<=50%)",
            ]

    # Low Risk
    if risk_group is None:
        if grade_group == 1 and psa < 10 and t in ("T1A", "T1B", "T1C", "T2A"):
            risk_group = "Low Risk"
            criteria = [
                f"T-stage: {t_stage} (T1-T2a)",
                f"Grade Group: {grade_group}",
                f"PSA: {psa} ng/mL (<10)",
            ]

    # Default fallback
    if risk_group is None:
        risk_group = "Unfavorable Intermediate Risk"
        criteria = [
            f"T-stage: {t_stage}",
            f"Grade Group: {grade_group}",
            f"PSA: {psa} ng/mL",
        ]

    # Treatment options by risk group
    treatments = _get_treatment_options(risk_group)

    return {
        "risk_group": risk_group,
        "criteria_met": criteria,
        "treatment_options": treatments,
    }


def _get_treatment_options(risk_group: str) -> List[str]:
    """Get NCCN treatment options by risk group."""
    options = {
        "Very Low Risk": [
            "Active surveillance (preferred)",
            "Watchful waiting (if life expectancy <10 years)",
            "Radical prostatectomy",
            "External beam radiation therapy (EBRT)",
            "Brachytherapy",
        ],
        "Low Risk": [
            "Active surveillance (preferred)",
            "Watchful waiting (if life expectancy <10 years)",
            "Radical prostatectomy",
            "EBRT",
            "Brachytherapy",
        ],
        "Favorable Intermediate Risk": [
            "Active surveillance (selected patients)",
            "Radical prostatectomy",
            "EBRT + short-term ADT (4-6 months)",
            "Brachytherapy +/- EBRT",
        ],
        "Unfavorable Intermediate Risk": [
            "Radical prostatectomy + PLND",
            "EBRT + short-term ADT (4-6 months)",
            "EBRT + brachytherapy boost + ADT",
        ],
        "High Risk": [
            "Radical prostatectomy + PLND",
            "EBRT + long-term ADT (18-36 months)",
            "EBRT + brachytherapy boost + ADT",
        ],
        "Very High Risk": [
            "EBRT + long-term ADT (18-36 months)",
            "EBRT + brachytherapy boost + ADT",
            "Radical prostatectomy (selected patients)",
            "Systemic therapy clinical trials",
        ],
    }
    return options.get(risk_group, ["Consult multidisciplinary tumor board"])


# ---------------------------------------------------------------------------
# Batch Processing
# ---------------------------------------------------------------------------

def process_batch(input_csv: str, output_csv: str) -> int:
    """
    Process a CSV of prostate cancer cases.

    Expected columns: primary_pattern, secondary_pattern, psa, t_stage
    Optional: tertiary_pattern, num_positive_cores, total_cores, max_percent_per_core
    """
    with open(input_csv, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    out_fields = fieldnames + ["gleason_score", "grade_group", "risk_group",
                               "treatment_options"]
    out_rows = []

    for row in rows:
        primary = int(row.get("primary_pattern", 3))
        secondary = int(row.get("secondary_pattern", 3))
        tertiary = row.get("tertiary_pattern")
        psa = float(row.get("psa", 5.0))
        t_stage = row.get("t_stage", "T1c")
        num_pos = row.get("num_positive_cores")
        total = row.get("total_cores")
        max_pct = row.get("max_percent_per_core")

        grade_result = map_gleason_to_grade_group(
            primary, secondary,
            int(tertiary) if tertiary else None
        )

        risk_result = nccn_risk_stratification(
            grade_group=grade_result["grade_group"],
            psa=psa,
            t_stage=t_stage,
            num_positive_cores=int(num_pos) if num_pos else None,
            total_cores=int(total) if total else None,
            max_percent_per_core=float(max_pct) if max_pct else None,
        )

        row_dict = dict(row)
        row_dict["gleason_score"] = grade_result["gleason_score"]
        row_dict["grade_group"] = grade_result["grade_group"]
        row_dict["risk_group"] = risk_result["risk_group"]
        row_dict["treatment_options"] = "; ".join(risk_result["treatment_options"])
        out_rows.append(row_dict)

    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    return len(out_rows)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Gleason Grade Group & NCCN Risk Stratification Mapper"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Grade group
    p_grade = subparsers.add_parser("grade", help="Map Gleason patterns to Grade Group")
    p_grade.add_argument("--primary", type=int, required=True,
                          help="Primary Gleason pattern (1-5)")
    p_grade.add_argument("--secondary", type=int, required=True,
                          help="Secondary Gleason pattern (1-5)")
    p_grade.add_argument("--tertiary", type=int, default=None,
                          help="Tertiary pattern (optional)")

    # Risk stratification
    p_risk = subparsers.add_parser("risk", help="NCCN risk stratification")
    p_risk.add_argument("--grade-group", type=int, required=True,
                         help="ISUP Grade Group (1-5)")
    p_risk.add_argument("--psa", type=float, required=True,
                         help="PSA level (ng/mL)")
    p_risk.add_argument("--t-stage", required=True,
                         help="Clinical T stage (e.g., T1c, T2a, T3a)")
    p_risk.add_argument("--positive-cores", type=int, default=None,
                         help="Number of positive cores")
    p_risk.add_argument("--total-cores", type=int, default=None,
                         help="Total cores taken")
    p_risk.add_argument("--max-percent", type=float, default=None,
                         help="Max % cancer in any core")

    # Full assessment
    p_full = subparsers.add_parser("assess", help="Full grade + risk assessment")
    p_full.add_argument("--primary", type=int, required=True)
    p_full.add_argument("--secondary", type=int, required=True)
    p_full.add_argument("--tertiary", type=int, default=None)
    p_full.add_argument("--psa", type=float, required=True)
    p_full.add_argument("--t-stage", required=True)
    p_full.add_argument("--positive-cores", type=int, default=None)
    p_full.add_argument("--total-cores", type=int, default=None)
    p_full.add_argument("--max-percent", type=float, default=None)

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    args = parser.parse_args(argv)

    if args.command == "grade":
        result = map_gleason_to_grade_group(args.primary, args.secondary, args.tertiary)
        print(json.dumps(result, indent=2))

    elif args.command == "risk":
        result = nccn_risk_stratification(
            grade_group=args.grade_group,
            psa=args.psa,
            t_stage=args.t_stage,
            num_positive_cores=args.positive_cores,
            total_cores=args.total_cores,
            max_percent_per_core=args.max_percent,
        )
        print(json.dumps(result, indent=2))

    elif args.command == "assess":
        grade = map_gleason_to_grade_group(args.primary, args.secondary, args.tertiary)
        risk = nccn_risk_stratification(
            grade_group=grade["grade_group"],
            psa=args.psa,
            t_stage=args.t_stage,
            num_positive_cores=args.positive_cores,
            total_cores=args.total_cores,
            max_percent_per_core=args.max_percent,
        )
        output = {
            "gleason_score": grade["gleason_score"],
            "grade_group": grade["grade_group"],
            "grade_group_label": grade["grade_group_label"],
            "risk_category": grade["risk_category"],
            "nccn_risk_group": risk["risk_group"],
            "criteria_met": risk["criteria_met"],
            "treatment_options": risk["treatment_options"],
        }
        print(json.dumps(output, indent=2))

    elif args.command == "batch":
        count = process_batch(args.input, args.output)
        print(f"Processed {count} records -> {args.output}")


if __name__ == "__main__":
    main()
