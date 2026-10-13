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
import math
from typing import Dict, Any, Optional, List


# ---------------------------------------------------------------------------
# Gleason Score & Grade Group Mapping
# ---------------------------------------------------------------------------

def map_gleason_to_grade_group(primary_pattern: int, secondary_pattern: int,
                               tertiary_pattern: Optional[int] = None,
                               specimen_type: str = "biopsy") -> Dict[str, Any]:
    """Map a pathologist-assigned Gleason pattern pair to an ISUP Grade Group.

    For needle biopsy, a third higher pattern replaces the secondary pattern.
    For prostatectomy, minor/tertiary patterns are reported separately because
    their percentage and pathological context are required before regrading.
    """
    for name, value in (("primary_pattern", primary_pattern),
                        ("secondary_pattern", secondary_pattern),
                        ("tertiary_pattern", tertiary_pattern)):
        if value is None and name == "tertiary_pattern":
            continue
        if type(value) is not int or not 3 <= value <= 5:
            raise ValueError(f"{name} must be an integer Gleason pattern 3-5; got {value!r}")
    if specimen_type not in ("biopsy", "prostatectomy"):
        raise ValueError("specimen_type must be 'biopsy' or 'prostatectomy'")

    effective_secondary = secondary_pattern
    notes = []
    if tertiary_pattern is not None:
        if specimen_type == "biopsy":
            if tertiary_pattern > secondary_pattern:
                effective_secondary = tertiary_pattern
                notes.append("Needle biopsy: highest additional pattern is incorporated into the score.")
        else:
            notes.append("Prostatectomy: minor/tertiary pattern reported separately; "
                         "percentage and specialist review are needed before any grade adjustment.")

    score = primary_pattern + effective_secondary
    grades = {
        (3, 3): 1, (3, 4): 2, (4, 3): 3,
        (4, 4): 4, (3, 5): 4, (5, 3): 4,
        (4, 5): 5, (5, 4): 5, (5, 5): 5,
    }
    grade = grades[(primary_pattern, effective_secondary)]
    # Historical compatibility only; clinical risk is NOT determined by grade alone.
    grade_risk_labels = {
        1: "Low risk", 2: "Favorable intermediate risk",
        3: "Unfavorable intermediate risk", 4: "High risk", 5: "Highest risk",
    }
    result = {
        "primary_pattern": primary_pattern,
        "secondary_pattern": secondary_pattern,
        "gleason_score": score,
        "grade_group": grade,
        "grade_group_label": f"Grade Group {grade}",
        "risk_category": grade_risk_labels[grade],
        "description": f"Gleason {primary_pattern}+{effective_secondary}={score} (Grade Group {grade}).",
        "prognosis": "Prognosis requires staging, PSA, disease extent and other clinical findings.",
        "specimen_type": specimen_type,
        "effective_secondary_pattern": effective_secondary,
    }
    if tertiary_pattern is not None:
        result["tertiary_pattern"] = tertiary_pattern
        result["note"] = " ".join(notes) if notes else "Additional pattern does not increase the score."
    return result

# ---------------------------------------------------------------------------
# NCCN Risk Stratification
# ---------------------------------------------------------------------------

def nccn_risk_stratification(grade_group: int, psa: float, t_stage: str,
                             num_positive_cores: Optional[int] = None,
                             total_cores: Optional[int] = None,
                             max_percent_per_core: Optional[float] = None,
                             psa_density: Optional[float] = None) -> Dict[str, Any]:
    """Exploratory localized prostate-cancer risk grouping, not a treatment decision.

    Uses clinical T stage, PSA, Grade Group and (where available) biopsy-core
    involvement. Missing required subgroup information is flagged rather than
    being silently assigned a favorable or unfavorable category.
    """
    if type(grade_group) is not int or not 1 <= grade_group <= 5:
        raise ValueError(f"grade_group must be 1-5; got {grade_group}")
    if isinstance(psa, bool) or not isinstance(psa, (int, float)) or not math.isfinite(psa) or psa < 0:
        raise ValueError(f"psa must be a finite number >= 0; got {psa}")
    if not isinstance(t_stage, str):
        raise ValueError("t_stage must be a clinical T-stage string")
    t = t_stage.strip().upper()
    if t.startswith("C"):
        t = t[1:]
    stages = {"T1A", "T1B", "T1C", "T2A", "T2B", "T2C", "T3A", "T3B", "T4"}
    if t not in stages:
        raise ValueError(f"unsupported clinical t_stage: {t_stage!r}")
    if (num_positive_cores is None) != (total_cores is None):
        raise ValueError("num_positive_cores and total_cores must be supplied together")
    if total_cores is not None:
        if (type(total_cores) is not int or type(num_positive_cores) is not int
                or total_cores <= 0 or not 0 <= num_positive_cores <= total_cores):
            raise ValueError("biopsy core counts must be integers with 0 <= positive <= total and total > 0")
    for name, value in (("max_percent_per_core", max_percent_per_core),
                        ("psa_density", psa_density)):
        if value is not None and (isinstance(value, bool) or
                                  not isinstance(value, (int, float)) or
                                  not math.isfinite(value) or value < 0 or
                                  (name == "max_percent_per_core" and value > 100)):
            raise ValueError(f"{name} must be a finite, nonnegative number in its valid range")

    criteria = [f"Clinical T stage: {t}", f"Grade Group: {grade_group}",
                f"PSA: {psa} ng/mL"]
    high_stage = t in {"T3A", "T3B", "T4"}
    high_grade = grade_group >= 4
    high_psa = psa > 20
    # Distinct very-high-risk features in the contemporary multi-feature schema.
    very_high_count = int(high_stage) + int(high_grade) + int(psa > 40)
    intermediate_factors = (int(t in {"T2B", "T2C"}) +
                            int(grade_group in (2, 3)) +
                            int(10 <= psa <= 20))
    core_fraction = (num_positive_cores / total_cores) if total_cores is not None else None

    if very_high_count >= 2:
        group = "Very High Risk"
    elif high_stage or high_grade or high_psa:
        group = "High Risk"
    elif intermediate_factors:
        if grade_group == 3 or intermediate_factors >= 2 or (
                core_fraction is not None and core_fraction >= 0.5):
            group = "Unfavorable Intermediate Risk"
        elif core_fraction is None:
            group = "Intermediate Risk (subgroup undetermined)"
            criteria.append("Biopsy core fraction required to resolve favorable vs unfavorable")
        else:
            group = "Favorable Intermediate Risk"
    elif grade_group == 1 and psa < 10 and t in {"T1A", "T1B", "T1C", "T2A"}:
        group = "Low Risk"
        if (t == "T1C" and num_positive_cores is not None and
                num_positive_cores < 3 and max_percent_per_core is not None and
                max_percent_per_core <= 50 and psa_density is not None and
                psa_density < 0.15):
            group = "Very Low Risk"
    else:
        raise ValueError("input combination cannot be assigned a localized risk group")
    if core_fraction is not None:
        criteria.append(f"Positive biopsy cores: {num_positive_cores}/{total_cores} ({core_fraction:.1%})")
    if psa_density is not None:
        criteria.append(f"PSA density: {psa_density} ng/mL/cm3")
    return {
        "risk_group": group,
        "criteria_met": criteria,
        "treatment_options": _get_treatment_options(group),
        "note": "Educational risk grouping only; verify current clinical guidance and complete staging.",
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

    # Audit (enterprise supervisor task dispatch)
    p_audit = subparsers.add_parser("audit", help="Dispatch task to enterprise supervisor")
    p_audit.add_argument("--task-id", required=True, help="Task identifier")
    p_audit.add_argument("--target", default="SPECIMEN-001", help="Target identifier")
    p_audit.add_argument("--primary-metric", type=float, default=10.0, help="Primary metric value")
    p_audit.add_argument("--secondary-metric", type=float, default=5.0, help="Secondary metric value")
    p_audit.add_argument("--status", default="NOMINAL", help="Status descriptor")
    p_audit.add_argument("--critical", action="store_true", help="Mark as critical")

    # Chat (enterprise supervisor chat)
    p_chat = subparsers.add_parser("chat", help="Enterprise supervisory chat")
    p_chat.add_argument("query", nargs="+", help="Chat query text")

    # Verify audit trail
    subparsers.add_parser("verify-audit", help="Verify HMAC audit trail integrity")

    # Serve (FastAPI server)
    p_serve = subparsers.add_parser("serve", help="Start FastAPI REST server")
    p_serve.add_argument("--host", default="0.0.0.0", help="Host to bind")
    p_serve.add_argument("--port", type=int, default=8000, help="Port to bind")

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

    elif args.command == "audit":
        from agents.supervisor import SystemSupervisor
        from agents.models import SystemTaskPayload
        supervisor = SystemSupervisor(model_provider="mock")
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary_metric,
            secondary_metric=args.secondary_metric,
            status_descriptor=args.status,
            is_critical_flag=args.critical,
        )
        dossier = supervisor.process_task(payload)
        print(json.dumps(dossier.to_dict(), indent=2, default=str))

    elif args.command == "chat":
        from agents.supervisor import SystemSupervisor
        supervisor = SystemSupervisor(model_provider="mock")
        query = " ".join(args.query)
        response = supervisor.query_supervisory_chat(query)
        print(json.dumps({"response": response}, indent=2))

    elif args.command == "verify-audit":
        from agents.base import AuditLogger
        valid = AuditLogger.verify_integrity()
        trail_len = len(AuditLogger.get_trail())
        print(json.dumps({"audit_valid": valid, "trail_length": trail_len}, indent=2))

    elif args.command == "serve":
        import uvicorn
        from agents.api import app
        uvicorn.run(app, host=args.host, port=args.port)

    return 0


if __name__ == "__main__":
    main()
