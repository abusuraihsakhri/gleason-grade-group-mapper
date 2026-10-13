"""Regression tests for clinical classification, invalid input and audit integrity."""
import csv
import pytest

from gleason_mapper import (map_gleason_to_grade_group,
                            nccn_risk_stratification, process_batch)
from agents.base import AuditTrail


@pytest.mark.parametrize("primary,secondary,expected", [
    (3, 3, 1), (3, 4, 2), (4, 3, 3),
    (3, 5, 4), (4, 4, 4), (5, 3, 4),
    (4, 5, 5), (5, 4, 5), (5, 5, 5),
])
def test_supported_gleason_pairs(primary, secondary, expected):
    result = map_gleason_to_grade_group(primary, secondary)
    assert result["grade_group"] == expected


def test_biopsy_highest_additional_pattern_changes_score():
    result = map_gleason_to_grade_group(3, 3, 5)
    assert result["gleason_score"] == 8
    assert result["grade_group"] == 4
    result = map_gleason_to_grade_group(3, 4, 5)
    assert result["gleason_score"] == 8
    assert result["grade_group"] == 4


def test_prostatectomy_tertiary_kept_separate():
    result = map_gleason_to_grade_group(3, 4, 5, "prostatectomy")
    assert result["grade_group"] == 2
    assert result["gleason_score"] == 7
    assert "Prostatectomy" in result["note"]


@pytest.mark.parametrize("value", [True, 1, 2, 6, 3.4, "4"])
def test_nonmodern_or_invalid_pattern_rejected(value):
    with pytest.raises(ValueError):
        map_gleason_to_grade_group(value, 3)


def test_favorable_intermediate_by_grade_group_alone():
    result = nccn_risk_stratification(2, 6, "cT1c", 2, 12)
    assert result["risk_group"] == "Favorable Intermediate Risk"


def test_intermediate_subgroup_undetermined_without_core_fraction():
    result = nccn_risk_stratification(2, 6, "T1c")
    assert result["risk_group"] == "Intermediate Risk (subgroup undetermined)"


def test_multiple_intermediate_factors_are_unfavorable():
    assert nccn_risk_stratification(2, 12, "T1c", 2, 12)["risk_group"] == \
        "Unfavorable Intermediate Risk"
    assert nccn_risk_stratification(2, 6, "T2a", 6, 12)["risk_group"] == \
        "Unfavorable Intermediate Risk"


def test_very_high_requires_multiple_features():
    assert nccn_risk_stratification(1, 6, "T3b")["risk_group"] == "High Risk"
    assert nccn_risk_stratification(5, 30, "T3b")["risk_group"] == "Very High Risk"
    assert nccn_risk_stratification(2, 45, "T2a")["risk_group"] == "High Risk"


def test_psa_boundary_and_very_low_density():
    assert nccn_risk_stratification(1, 20, "T1c", 2, 12)["risk_group"] == \
        "Favorable Intermediate Risk"
    assert nccn_risk_stratification(1, 20.01, "T1c")["risk_group"] == "High Risk"
    assert nccn_risk_stratification(1, 6, "T1c", 2, 12, 30)["risk_group"] == "Low Risk"
    assert nccn_risk_stratification(1, 6, "T1c", 2, 12, 30, 0.1)["risk_group"] == \
        "Very Low Risk"


@pytest.mark.parametrize("kwargs", [
    dict(grade_group=2, psa=float("nan"), t_stage="T1c"),
    dict(grade_group=2, psa=float("inf"), t_stage="T1c"),
    dict(grade_group=1, psa=3, t_stage="T2z"),
    dict(grade_group=1, psa=3, t_stage="T1c", num_positive_cores=4, total_cores=3),
    dict(grade_group=1, psa=3, t_stage="T1c", num_positive_cores=2),
    dict(grade_group=1, psa=3, t_stage="T1c", max_percent_per_core=101),
])
def test_invalid_risk_inputs(kwargs):
    with pytest.raises(ValueError):
        nccn_risk_stratification(**kwargs)


def test_batch_requires_columns_and_does_not_guess(tmp_path):
    src = tmp_path / "in.csv"
    dst = tmp_path / "out.csv"
    src.write_text("primary_pattern,secondary_pattern,psa,t_stage\n3,3,,T1c\n")
    with pytest.raises(ValueError, match="row 2"):
        process_batch(str(src), str(dst))
    assert not dst.exists()


def test_batch_formula_injection_is_escaped(tmp_path):
    src = tmp_path / "in.csv"
    dst = tmp_path / "out.csv"
    src.write_text("primary_pattern,secondary_pattern,psa,t_stage,annotation\n"
                   "3,3,5,T1c,=1+1\n")
    assert process_batch(str(src), str(dst)) == 1
    with dst.open(newline="") as file:
        row = next(csv.DictReader(file))
    assert row["annotation"].startswith("'=")


def test_audit_integrity_detects_mutations():
    log = AuditTrail(secret_key="test-only-secret")
    log.log("operator", "test", "event", {"status": "ok"})
    assert log.verify_integrity()
    copy = log.get_trail()
    copy[0]["actor"] = "modified"
    assert log.verify_integrity()
    log.logs[0]["actor"] = "modified"
    assert not log.verify_integrity()
