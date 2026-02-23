"""Unit tests for outlier detection and exclusion functionality."""

import pytest

from sample_size_calculator.models import OutlierInfo, Phase1Results
from sample_size_calculator.outliers import apply_exclusions, detect_outliers


class TestDetectOutliers:
    """Test suite for detect_outliers function."""

    def test_detect_outliers_basic(self):
        """Test basic outlier detection with clear outliers."""
        # Dataset with obvious outliers at both ends
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 100.0, -50.0]

        results = detect_outliers(data)

        assert results.pilot_data == data
        assert len(results.outliers) == 2
        assert results.q1 == 2.5
        assert results.q3 == 7.5
        assert results.iqr == 5.0

        # Check outlier values
        outlier_values = {o.value for o in results.outliers}
        assert 100.0 in outlier_values
        assert -50.0 in outlier_values

    def test_detect_outliers_no_outliers(self):
        """Test detection when no outliers are present."""
        # Normal distribution-like data
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        results = detect_outliers(data)

        assert len(results.outliers) == 0
        assert results.iqr > 0

    def test_detect_outliers_upper_only(self):
        """Test detection with only upper outliers."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 100.0, 150.0]

        results = detect_outliers(data)

        assert len(results.outliers) >= 1
        outlier_values = {o.value for o in results.outliers}
        assert 100.0 in outlier_values or 150.0 in outlier_values

    def test_detect_outliers_lower_only(self):
        """Test detection with only lower outliers."""
        data = [-100.0, -50.0, 1.0, 2.0, 3.0, 4.0, 5.0]

        results = detect_outliers(data)

        assert len(results.outliers) >= 1
        outlier_values = {o.value for o in results.outliers}
        assert -100.0 in outlier_values or -50.0 in outlier_values

    def test_detect_outliers_minimum_data(self):
        """Test detection with minimum required data points."""
        data = [1.0, 2.0, 3.0]

        results = detect_outliers(data)

        assert results.pilot_data == data
        assert results.q1 == 1.5
        assert results.q3 == 2.5
        assert results.iqr == 1.0

    def test_detect_outliers_insufficient_data(self):
        """Test that insufficient data raises ValueError."""
        with pytest.raises(ValueError, match="at least 3 data points"):
            detect_outliers([1.0, 2.0])

        with pytest.raises(ValueError, match="at least 3 data points"):
            detect_outliers([1.0])

        with pytest.raises(ValueError, match="at least 3 data points"):
            detect_outliers([])

    def test_detect_outliers_idempotence(self):
        """Test that detection is idempotent (same results on repeated calls)."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 100.0]

        results1 = detect_outliers(data)
        results2 = detect_outliers(data)

        assert results1.q1 == results2.q1
        assert results1.q3 == results2.q3
        assert results1.iqr == results2.iqr
        assert len(results1.outliers) == len(results2.outliers)
        assert {o.value for o in results1.outliers} == {
            o.value for o in results2.outliers
        }

    def test_detect_outliers_returns_correct_types(self):
        """Test that returned values have correct types."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]

        results = detect_outliers(data)

        assert isinstance(results, Phase1Results)
        assert isinstance(results.q1, float)
        assert isinstance(results.q3, float)
        assert isinstance(results.iqr, float)
        assert isinstance(results.outliers, list)
        for outlier in results.outliers:
            assert isinstance(outlier, OutlierInfo)
            assert isinstance(outlier.value, float)
            assert outlier.is_excluded is False
            assert outlier.rationale is None


class TestApplyExclusions:
    """Test suite for apply_exclusions function."""

    def test_apply_exclusions_with_valid_rationale(self):
        """Test exclusion with valid engineering rationale."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 100.0]
        phase1 = detect_outliers(data)

        # Mark outlier for exclusion with rationale
        outlier = phase1.outliers[0]
        outlier.is_excluded = True
        outlier.rationale = "Measurement error - sensor malfunction"

        cleaned = apply_exclusions(phase1, [outlier])

        assert 100.0 not in cleaned
        assert len(cleaned) == 5
        assert cleaned == [1.0, 2.0, 3.0, 4.0, 5.0]

    def test_apply_exclusions_multiple_outliers(self):
        """Test exclusion of multiple outliers."""
        # Use data that will definitely have multiple outliers
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 100.0, -50.0]
        phase1 = detect_outliers(data)

        # Verify we have multiple outliers
        assert len(phase1.outliers) >= 2

        # Mark all outliers for exclusion
        for outlier in phase1.outliers:
            outlier.is_excluded = True
            outlier.rationale = "Invalid measurement"

        cleaned = apply_exclusions(phase1, phase1.outliers)

        # Verify all outliers are removed
        outlier_values = {o.value for o in phase1.outliers}
        for outlier_value in outlier_values:
            assert outlier_value not in cleaned

        # Should have removed 2 outliers from 11 data points
        assert len(cleaned) == len(data) - len(phase1.outliers)

    def test_apply_exclusions_no_exclusions(self):
        """Test that no exclusions returns original data."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 100.0]
        phase1 = detect_outliers(data)

        # Don't mark any outliers for exclusion
        cleaned = apply_exclusions(phase1, [])

        assert cleaned == data

    def test_apply_exclusions_empty_rationale_raises_error(self):
        """Test that empty rationale raises ValueError."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 100.0]
        phase1 = detect_outliers(data)

        outlier = phase1.outliers[0]
        outlier.is_excluded = True
        outlier.rationale = ""

        with pytest.raises(ValueError, match="non-empty rationale"):
            apply_exclusions(phase1, [outlier])

    def test_apply_exclusions_none_rationale_raises_error(self):
        """Test that None rationale raises ValueError."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 100.0]
        phase1 = detect_outliers(data)

        outlier = phase1.outliers[0]
        outlier.is_excluded = True
        outlier.rationale = None

        with pytest.raises(ValueError, match="non-empty rationale"):
            apply_exclusions(phase1, [outlier])

    def test_apply_exclusions_whitespace_rationale_raises_error(self):
        """Test that whitespace-only rationale raises ValueError."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 100.0]
        phase1 = detect_outliers(data)

        outlier = phase1.outliers[0]
        outlier.is_excluded = True
        outlier.rationale = "   "

        with pytest.raises(ValueError, match="non-empty rationale"):
            apply_exclusions(phase1, [outlier])

    def test_apply_exclusions_partial_exclusion(self):
        """Test excluding some outliers but not others."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 100.0, 200.0]
        phase1 = detect_outliers(data)

        # Only exclude the first outlier
        outlier1 = phase1.outliers[0]
        outlier1.is_excluded = True
        outlier1.rationale = "Sensor error"

        cleaned = apply_exclusions(phase1, [outlier1])

        # One outlier should be removed, one should remain
        assert outlier1.value not in cleaned
        assert len(cleaned) == 6

    def test_apply_exclusions_preserves_order(self):
        """Test that data order is preserved after exclusions."""
        data = [5.0, 1.0, 3.0, 2.0, 4.0, 100.0]
        phase1 = detect_outliers(data)

        outlier = phase1.outliers[0]
        outlier.is_excluded = True
        outlier.rationale = "Invalid"

        cleaned = apply_exclusions(phase1, [outlier])

        assert cleaned == [5.0, 1.0, 3.0, 2.0, 4.0]

    def test_apply_exclusions_not_excluded_flag(self):
        """Test that outliers with is_excluded=False are not removed."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 100.0]
        phase1 = detect_outliers(data)

        outlier = phase1.outliers[0]
        outlier.is_excluded = False
        outlier.rationale = "This should not matter"

        cleaned = apply_exclusions(phase1, [outlier])

        # Outlier should still be in the data
        assert 100.0 in cleaned
        assert len(cleaned) == 6
