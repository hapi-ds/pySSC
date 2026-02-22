"""Property-based tests for normality testing.

This module contains property-based tests using Hypothesis to verify
the correctness and determinism of Shapiro-Wilk normality testing and
classification logic.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from src.sample_size_calculator.normality import is_normal, shapiro_wilk_test


class TestNormalityTestingProperties:
    """Property-based tests for normality testing correctness."""

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False),
            min_size=3,
            max_size=100,
        )
    )
    @settings(deadline=1000)
    def test_property_13_shapiro_wilk_returns_valid_p_value(
        self, data: list[float]
    ) -> None:
        """Property 13a: Shapiro-Wilk Returns Valid P-Value.

        **Validates: Requirements 9.1, 9.2**

        For any cleaned pilot dataset, the Shapiro-Wilk test should return
        a valid p-value in the range [0, 1].
        """
        # Perform Shapiro-Wilk test
        p_value = shapiro_wilk_test(data)

        # Verify p-value is a float
        assert isinstance(p_value, float), (
            f"P-value should be a float, got {type(p_value)}"
        )

        # Verify p-value is in valid range [0, 1]
        assert 0.0 <= p_value <= 1.0, (
            f"P-value should be in range [0, 1], got {p_value}"
        )

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False),
            min_size=3,
            max_size=100,
        )
    )
    @settings(deadline=1000)
    def test_property_13_shapiro_wilk_deterministic(
        self, data: list[float]
    ) -> None:
        """Property 13b: Shapiro-Wilk Test is Deterministic.

        **Validates: Requirements 9.1, 9.2**

        For any cleaned pilot dataset, running the Shapiro-Wilk test multiple
        times on the same data should produce identical p-values.
        """
        # Run Shapiro-Wilk test multiple times
        p_value1 = shapiro_wilk_test(data)
        p_value2 = shapiro_wilk_test(data)
        p_value3 = shapiro_wilk_test(data)

        # Verify all p-values are identical
        assert p_value1 == p_value2 == p_value3, (
            f"P-values differ across multiple runs: "
            f"run1={p_value1}, run2={p_value2}, run3={p_value3}"
        )

    @given(
        p_value=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        alpha=st.floats(min_value=0.01, max_value=0.20, allow_nan=False),
    )
    @settings(deadline=1000)
    def test_property_13_is_normal_classification_correctness(
        self, p_value: float, alpha: float
    ) -> None:
        """Property 13c: is_normal Classification Correctness.

        **Validates: Requirements 9.3, 9.4**

        For any p-value and alpha, the is_normal function should correctly
        classify data as normal (p > alpha) or non-normal (p <= alpha).
        """
        # Classify normality
        result = is_normal(p_value, alpha)

        # Verify classification is correct
        if p_value > alpha:
            assert result is True, (
                f"Data should be classified as normal when p={p_value} > alpha={alpha}"
            )
        else:
            assert result is False, (
                f"Data should be classified as non-normal when "
                f"p={p_value} <= alpha={alpha}"
            )

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False),
            min_size=3,
            max_size=100,
        )
    )
    @settings(deadline=1000)
    def test_property_13_is_normal_with_default_alpha(
        self, data: list[float]
    ) -> None:
        """Property 13d: is_normal with Default Alpha (0.05).

        **Validates: Requirements 9.3, 9.4**

        For any cleaned pilot dataset, when using the default alpha=0.05,
        the system should classify data as Normal if p > 0.05 and proceed
        to transformation attempts if p <= 0.05.
        """
        # Perform Shapiro-Wilk test
        p_value = shapiro_wilk_test(data)

        # Classify with default alpha
        result = is_normal(p_value)

        # Verify classification matches expected behavior
        if p_value > 0.05:
            assert result is True, (
                f"Data should be classified as Normal when p={p_value} > 0.05"
            )
        else:
            assert result is False, (
                f"Data should proceed to transformation when p={p_value} <= 0.05"
            )

    @given(
        p_value=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    @settings(deadline=1000)
    def test_property_13_is_normal_boundary_behavior(
        self, p_value: float
    ) -> None:
        """Property 13e: is_normal Boundary Behavior.

        **Validates: Requirements 9.3, 9.4**

        For any p-value, the is_normal function should handle boundary
        conditions correctly (p > alpha vs p <= alpha).
        """
        # Test with alpha = 0.05 (default)
        alpha = 0.05
        result = is_normal(p_value, alpha)

        # Verify boundary behavior
        if p_value > alpha:
            assert result is True, (
                f"Should return True when p={p_value} > alpha={alpha}"
            )
        elif p_value < alpha:
            assert result is False, (
                f"Should return False when p={p_value} < alpha={alpha}"
            )
        else:  # p_value == alpha
            assert result is False, (
                f"Should return False when p={p_value} == alpha={alpha} "
                f"(boundary case: p <= alpha)"
            )

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False),
            min_size=3,
            max_size=100,
        ),
        alpha1=st.floats(min_value=0.01, max_value=0.10, allow_nan=False),
        alpha2=st.floats(min_value=0.01, max_value=0.10, allow_nan=False),
    )
    @settings(deadline=1000)
    def test_property_13_is_normal_with_various_alpha_values(
        self, data: list[float], alpha1: float, alpha2: float
    ) -> None:
        """Property 13f: is_normal with Various Alpha Values.

        **Validates: Requirements 9.3, 9.4**

        For any cleaned pilot dataset and various alpha values, the
        classification should be consistent with the p-value threshold.
        """
        # Perform Shapiro-Wilk test once
        p_value = shapiro_wilk_test(data)

        # Test with different alpha values
        result1 = is_normal(p_value, alpha1)
        result2 = is_normal(p_value, alpha2)

        # Verify classification is correct for each alpha
        assert result1 == (p_value > alpha1), (
            f"Classification incorrect for alpha={alpha1}: "
            f"p={p_value}, result={result1}"
        )
        assert result2 == (p_value > alpha2), (
            f"Classification incorrect for alpha={alpha2}: "
            f"p={p_value}, result={result2}"
        )

        # Verify monotonicity: if alpha1 < alpha2, then
        # result1 implies result2 (stricter threshold implies looser)
        if alpha1 < alpha2:
            if result1:
                # If p > alpha1 (stricter), then p > alpha2 (looser) must also be true
                # unless p is between alpha1 and alpha2
                if p_value > alpha2:
                    assert result2 is True, (
                        f"Monotonicity violated: p={p_value} > alpha2={alpha2} "
                        f"but result2={result2}"
                    )
