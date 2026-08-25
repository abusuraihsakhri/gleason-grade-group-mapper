#!/usr/bin/env python3
"""Tests for Gleason Grade Group Mapper - 20 real test cases."""
import pytest
from gleason_mapper import (
    map_gleason_to_grade_group, nccn_risk_stratification, process_batch
)


# ---------------------------------------------------------------------------
# Grade Group Mapping Tests
# ---------------------------------------------------------------------------

class TestGradeGroupMapping:

    def test_3_plus_3_group1(self):
        result = map_gleason_to_grade_group(3, 3)
        assert result["gleason_score"] == 6
        assert result["grade_group"] == 1
        assert result["risk_category"] == "Low risk"

    def test_3_plus_4_group2(self):
        result = map_gleason_to_grade_group(3, 4)
        assert result["gleason_score"] == 7
        assert result["grade_group"] == 2
        assert "Favorable" in result["risk_category"]

    def test_4_plus_3_group3(self):
        result = map_gleason_to_grade_group(4, 3)
        assert result["gleason_score"] == 7
        assert result["grade_group"] == 3
        assert "Unfavorable" in result["risk_category"]

    def test_4_plus_4_group4(self):
        result = map_gleason_to_grade_group(4, 4)
        assert result["gleason_score"] == 8
        assert result["grade_group"] == 4
        assert result["risk_category"] == "High risk"

    def test_3_plus_5_group4(self):
        result = map_gleason_to_grade_group(3, 5)
        assert result["gleason_score"] == 8
        assert result["grade_group"] == 4

    def test_5_plus_3_group4(self):
        result = map_gleason_to_grade_group(5, 3)
        assert result["gleason_score"] == 8
        assert result["grade_group"] == 4

    def test_4_plus_5_group5(self):
        result = map_gleason_to_grade_group(4, 5)
        assert result["gleason_score"] == 9
        assert result["grade_group"] == 5
        assert result["risk_category"] == "Highest risk"

    def test_5_plus_5_group5(self):
        result = map_gleason_to_grade_group(5, 5)
        assert result["gleason_score"] == 10
        assert result["grade_group"] == 5

    def test_5_plus_4_group5(self):
        result = map_gleason_to_grade_group(5, 4)
        assert result["gleason_score"] == 9
        assert result["grade_group"] == 5

    def test_tertiary_pattern_note(self):
        result = map_gleason_to_grade_group(3, 3, tertiary_pattern=5)
        assert result["tertiary_pattern"] == 5
        assert "note" in result

    def test_invalid_pattern_zero(self):
        with pytest.raises(ValueError, match="must be integer 1-5"):
            map_gleason_to_grade_group(0, 3)

    def test_invalid_pattern_six(self):
        with pytest.raises(ValueError, match="must be integer 1-5"):
            map_gleason_to_grade_group(3, 6)


# ---------------------------------------------------------------------------
# NCCN Risk Stratification Tests
# ---------------------------------------------------------------------------

class TestNCCNRiskStratification:

    def test_very_low_risk(self):
        result = nccn_risk_stratification(
            grade_group=1, psa=5.0, t_stage="T1c",
            num_positive_cores=2, total_cores=12, max_percent_per_core=30.0
        )
        assert result["risk_group"] == "Very Low Risk"

    def test_low_risk(self):
        result = nccn_risk_stratification(
            grade_group=1, psa=8.0, t_stage="T2a"
        )
        assert result["risk_group"] == "Low Risk"

    def test_high_risk_gg4(self):
        result = nccn_risk_stratification(
            grade_group=4, psa=15.0, t_stage="T2b"
        )
        assert result["risk_group"] == "High Risk"

    def test_high_risk_psa(self):
        result = nccn_risk_stratification(
            grade_group=2, psa=25.0, t_stage="T2a"
        )
        assert result["risk_group"] == "High Risk"

    def test_very_high_risk_t3b(self):
        result = nccn_risk_stratification(
            grade_group=5, psa=30.0, t_stage="T3b"
        )
        assert result["risk_group"] == "Very High Risk"

    def test_treatment_options_present(self):
        result = nccn_risk_stratification(
            grade_group=1, psa=5.0, t_stage="T1c"
        )
        assert len(result["treatment_options"]) > 0
        assert any("surveillance" in t.lower() for t in result["treatment_options"])

    def test_invalid_grade_group(self):
        with pytest.raises(ValueError, match="grade_group must be 1-5"):
            nccn_risk_stratification(grade_group=0, psa=5.0, t_stage="T1c")

    def test_invalid_psa(self):
        with pytest.raises(ValueError, match="psa must be >= 0"):
            nccn_risk_stratification(grade_group=1, psa=-1.0, t_stage="T1c")


# ---------------------------------------------------------------------------
# Batch Processing Tests
# ---------------------------------------------------------------------------

class TestBatchProcessing:

    def test_batch_basic(self, tmp_path):
        csv_in = tmp_path / "in.csv"
        csv_out = tmp_path / "out.csv"
        csv_in.write_text(
            "primary_pattern,secondary_pattern,psa,t_stage\n"
            "3,3,5.0,T1c\n"
            "4,3,15.0,T2b\n"
            "5,5,30.0,T3b\n",
            encoding="utf-8"
        )
        count = process_batch(str(csv_in), str(csv_out))
        assert count == 3
        content = csv_out.read_text(encoding="utf-8")
        assert "gleason_score" in content
        assert "grade_group" in content
        assert "risk_group" in content
