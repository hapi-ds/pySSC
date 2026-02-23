"""Property-based tests for outlier detection.

This module contains property-based tests using Hypothesis to verify
the correctness and idempotence of outlier detection and exclusion.
"""

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.sample_size_calculator.outliers import apply_exclusions, detect_outliers


class TestOutlierDetectionProperties:
    """Property-based tests for outlier detection correctness."""

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False),
            min_size=3,
            max_size=100,
        )
    )
    @settings(deadline=1000)
    def test_property_9_iqr_outlier_detection_correctness(
        self, data: list[float]
    ) -> None:
        """Property 9: IQR Outlier Detection Correctness.

        **Validates: Requirements 7.1, 7.2, 7.3**

        For any pilot dataset, outliers should be correctly identified as values
        less than Q1 - 1.5*IQR or greater than Q3 + 1.5*IQR, where Q1, Q3, and
        IQR are calculated from the dataset.
        """
        # Detect outliers
        results = detect_outliers(data)

        # Verify Q1, Q3, IQR calculations are correct
        expected_q1 = float(np.percentile(data, 25))
        expected_q3 = float(np.percentile(data, 75))
        expected_iqr = expected_q3 - expected_q1

        assert np.isclose(results.q1, expected_q1, rtol=1e-9, atol=1e-12), (
            f"Q1 calculation incorrect: expected={expected_q1}, got={results.q1}"
        )
        assert np.isclose(results.q3, expected_q3, rtol=1e-9, atol=1e-12), (
            f"Q3 calculation incorrect: expected={expected_q3}, got={results.q3}"
        )
        assert np.isclose(results.iqr, expected_iqr, rtol=1e-9, atol=1e-12), (
            f"IQR calculation incorrect: expected={expected_iqr}, got={results.iqr}"
        )

        # Calculate outlier bounds
        lower_bound = results.q1 - 1.5 * results.iqr
        upper_bound = results.q3 + 1.5 * results.iqr

        # Verify all flagged outliers are actually outliers
        for outlier in results.outliers:
            assert outlier.value < lower_bound or outlier.value > upper_bound, (
                f"Value {outlier.value} flagged as outlier but is within bounds "
                f"[{lower_bound}, {upper_bound}]"
            )

        # Verify all outliers in the dataset are flagged
        outlier_values = {outlier.value for outlier in results.outliers}
        for value in data:
            if value < lower_bound or value > upper_bound:
                assert value in outlier_values, (
                    f"Value {value} is an outlier but was not flagged"
                )

        # Verify all flagged outliers are in the original dataset
        for outlier in results.outliers:
            assert outlier.value in data, (
                f"Outlier {outlier.value} not found in original dataset"
            )

        # Verify data length is preserved in Phase1Results
        assert len(results.pilot_data) == len(data), (
            f"Pilot data length mismatch: expected={len(data)}, "
            f"got={len(results.pilot_data)}"
        )
        assert results.pilot_data == data, "Pilot data should match input data"


class TestOutlierDetectionIdempotence:
    """Property-based tests for outlier detection idempotence."""

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False),
            min_size=3,
            max_size=100,
        )
    )
    @settings(deadline=1000)
    def test_property_10_outlier_detection_idempotence(self, data: list[float]) -> None:
        """Property 10: Outlier Detection Idempotence.

        **Validates: Requirements 7.5**

        For any dataset, running outlier detection multiple times should identify
        the same outliers each time.
        """
        # Run outlier detection multiple times
        results1 = detect_outliers(data)
        results2 = detect_outliers(data)
        results3 = detect_outliers(data)

        # Verify Q1, Q3, IQR values don't change
        assert results1.q1 == results2.q1 == results3.q1, (
            "Q1 values differ across multiple runs"
        )
        assert results1.q3 == results2.q3 == results3.q3, (
            "Q3 values differ across multiple runs"
        )
        assert results1.iqr == results2.iqr == results3.iqr, (
            "IQR values differ across multiple runs"
        )

        # Verify outlier lists are identical
        outliers1 = {outlier.value for outlier in results1.outliers}
        outliers2 = {outlier.value for outlier in results2.outliers}
        outliers3 = {outlier.value for outlier in results3.outliers}

        assert outliers1 == outliers2 == outliers3, (
            f"Outlier lists differ across multiple runs: "
            f"run1={outliers1}, run2={outliers2}, run3={outliers3}"
        )

        # Verify the number of outliers is consistent
        assert (
            len(results1.outliers) == len(results2.outliers) == len(results3.outliers)
        ), "Number of outliers differs across multiple runs"


class TestOutlierExclusionValidation:
    """Property-based tests for outlier exclusion validation."""

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False),
            min_size=3,
            max_size=100,
        )
    )
    @settings(deadline=1000)
    def test_property_11_outlier_exclusion_requires_rationale(
        self, data: list[float]
    ) -> None:
        """Property 11a: Outlier Exclusion Requires Non-Empty Rationale.

        **Validates: Requirements 8.2, 8.3**

        For any outlier exclusion attempt, the system should require a non-empty
        engineering rationale and reject exclusions without rationale.
        """
        # Detect outliers
        phase1_results = detect_outliers(data)

        # If there are no outliers, skip this test
        if len(phase1_results.outliers) == 0:
            return

        # Test 1: Exclusion without rationale should raise error
        outlier_to_exclude = phase1_results.outliers[0]
        outlier_to_exclude.is_excluded = True
        outlier_to_exclude.rationale = None

        with pytest.raises(ValueError, match="non-empty rationale"):
            apply_exclusions(phase1_results, [outlier_to_exclude])

        # Test 2: Exclusion with empty string rationale should raise error
        outlier_to_exclude.rationale = ""

        with pytest.raises(ValueError, match="non-empty rationale"):
            apply_exclusions(phase1_results, [outlier_to_exclude])

        # Test 3: Exclusion with whitespace-only rationale should raise error
        outlier_to_exclude.rationale = "   "

        with pytest.raises(ValueError, match="non-empty rationale"):
            apply_exclusions(phase1_results, [outlier_to_exclude])

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False),
            min_size=3,
            max_size=100,
        ),
        rationale=st.text(min_size=1, max_size=200).filter(lambda x: x.strip() != ""),
    )
    @settings(deadline=1000)
    def test_property_11_outlier_exclusion_with_valid_rationale(
        self, data: list[float], rationale: str
    ) -> None:
        """Property 11b: Outlier Exclusion with Valid Rationale Succeeds.

        **Validates: Requirements 8.2, 8.3**

        For any outlier exclusion with a non-empty rationale, the system should
        successfully exclude the outlier from the cleaned dataset.
        """
        # Detect outliers
        phase1_results = detect_outliers(data)

        # If there are no outliers, skip this test
        if len(phase1_results.outliers) == 0:
            return

        # Exclude outliers with valid rationale
        outliers_to_exclude = []
        for outlier in phase1_results.outliers:
            outlier.is_excluded = True
            outlier.rationale = rationale
            outliers_to_exclude.append(outlier)

        # Apply exclusions - should succeed
        cleaned_data = apply_exclusions(phase1_results, outliers_to_exclude)

        # Verify excluded outliers are removed from cleaned dataset
        excluded_values = {o.value for o in outliers_to_exclude}
        for value in cleaned_data:
            assert value not in excluded_values, (
                f"Excluded outlier {value} still present in cleaned dataset"
            )

        # Verify non-excluded values remain in cleaned dataset
        # Note: apply_exclusions removes ALL occurrences of excluded values
        for value in data:
            if value not in excluded_values:
                assert value in cleaned_data, (
                    f"Non-excluded value {value} missing from cleaned dataset"
                )

        # Verify cleaned dataset size
        # Count how many values in original data match excluded values
        excluded_count = sum(1 for v in data if v in excluded_values)
        expected_size = len(data) - excluded_count
        assert len(cleaned_data) == expected_size, (
            f"Cleaned dataset size incorrect: expected={expected_size}, "
            f"got={len(cleaned_data)}"
        )

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False),
            min_size=5,
            max_size=100,
        ),
        rationale=st.text(min_size=1, max_size=200).filter(lambda x: x.strip() != ""),
    )
    @settings(deadline=1000)
    def test_property_11_partial_outlier_exclusion(
        self, data: list[float], rationale: str
    ) -> None:
        """Property 11c: Partial Outlier Exclusion.

        **Validates: Requirements 8.2, 8.3**

        When only some outliers are excluded, the system should remove only the
        excluded outliers and keep the non-excluded outliers in the dataset.
        """
        # Detect outliers
        phase1_results = detect_outliers(data)

        # If there are fewer than 2 outliers, skip this test
        if len(phase1_results.outliers) < 2:
            return

        # Find outliers with unique values to ensure we can test partial exclusion
        unique_outlier_values = list({o.value for o in phase1_results.outliers})
        if len(unique_outlier_values) < 2:
            # All outliers have the same value, skip this test
            return

        # Exclude only the first unique outlier value
        value_to_exclude = unique_outlier_values[0]
        outlier_to_exclude = None
        for outlier in phase1_results.outliers:
            if outlier.value == value_to_exclude:
                outlier_to_exclude = outlier
                break

        # Type assertion: we know outlier_to_exclude is not None because we found it in the loop
        assert outlier_to_exclude is not None, "Outlier to exclude must be found"
        outlier_to_exclude.is_excluded = True
        outlier_to_exclude.rationale = rationale

        # Apply exclusions
        cleaned_data = apply_exclusions(phase1_results, [outlier_to_exclude])

        # Verify the excluded outlier value is removed (all occurrences)
        assert value_to_exclude not in cleaned_data, (
            f"Excluded outlier {value_to_exclude} still in cleaned dataset"
        )

        # Verify non-excluded outlier values remain in the dataset
        for unique_value in unique_outlier_values[1:]:
            # Check if this value exists in the original data
            if unique_value in data:
                assert unique_value in cleaned_data, (
                    f"Non-excluded outlier {unique_value} missing from cleaned dataset"
                )

        # Verify cleaned dataset size
        # Count how many values in original data match the excluded value
        excluded_count = sum(1 for v in data if v == value_to_exclude)
        expected_size = len(data) - excluded_count
        assert len(cleaned_data) == expected_size, (
            f"Cleaned dataset size incorrect: expected={expected_size}, "
            f"got={len(cleaned_data)}"
        )
