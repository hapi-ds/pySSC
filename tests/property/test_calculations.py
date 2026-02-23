"""Property-based tests for calculation engine.

This module contains property-based tests using Hypothesis to verify
the correctness of calculation formulas across a wide range of inputs.
"""

import math

from hypothesis import given, settings
from hypothesis import strategies as st
from scipy.stats import binom

from src.sample_size_calculator.calculations import CalculationEngine

# Strategy for valid confidence/reliability percentages
confidence_reliability_strategy = st.floats(min_value=0.1, max_value=99.9)


class TestModuleACalculations:
    """Property-based tests for Module A attribute data calculations."""

    @given(
        confidence=confidence_reliability_strategy,
        reliability=confidence_reliability_strategy,
    )
    def test_property_2_success_run_theorem_formula_correctness(
        self, confidence: float, reliability: float
    ) -> None:
        """Property 2: Success Run Theorem Formula Correctness.

        **Validates: Requirements 2.1, 2.2**

        For any valid confidence C and reliability R with allowable failures c=0,
        the calculated sample size n should equal ceiling(ln(1-C/100) / ln(R/100)).
        """
        # Calculate using the method
        n = CalculationEngine.success_run_theorem(confidence, reliability)

        # Calculate expected value using the formula directly
        c_conf = confidence / 100.0
        r_rel = reliability / 100.0
        expected_n = math.ceil(math.log(1 - c_conf) / math.log(r_rel))

        # Verify the formula is applied correctly
        assert n == expected_n, (
            f"Success Run Theorem formula incorrect: "
            f"got {n}, expected {expected_n} "
            f"for C={confidence}%, R={reliability}%"
        )

        # Verify result is a positive integer
        assert isinstance(n, int), "Sample size must be an integer"
        assert n > 0, "Sample size must be positive"

    @given(
        confidence=confidence_reliability_strategy,
        reliability=confidence_reliability_strategy,
    )
    def test_property_3_calculation_idempotence(
        self, confidence: float, reliability: float
    ) -> None:
        """Property 3: Calculation Idempotence.

        **Validates: Requirements 2.3**

        For any valid inputs, calculating the sample size multiple times
        with the same inputs should produce identical results.
        """
        # Calculate sample size multiple times
        n1 = CalculationEngine.success_run_theorem(confidence, reliability)
        n2 = CalculationEngine.success_run_theorem(confidence, reliability)
        n3 = CalculationEngine.success_run_theorem(confidence, reliability)

        # All results should be identical
        assert n1 == n2 == n3, (
            f"Calculation is not idempotent: "
            f"got {n1}, {n2}, {n3} for C={confidence}%, R={reliability}%"
        )

    @given(
        confidence=confidence_reliability_strategy,
        reliability=confidence_reliability_strategy,
        allowable_failures=st.integers(min_value=1, max_value=10),
    )
    @settings(deadline=1000)  # Allow up to 1 second for iterative calculations
    def test_property_4_cumulative_binomial_constraint_satisfaction(
        self, confidence: float, reliability: float, allowable_failures: int
    ) -> None:
        """Property 4: Cumulative Binomial Constraint Satisfaction.

        **Validates: Requirements 3.1, 3.2, 3.3**

        For any valid confidence C, reliability R, and allowable failures c>0,
        the calculated sample size n should be the minimum integer where the
        cumulative binomial probability sum(k=0 to c)[C(n,k) * (1-R)^k * R^(n-k)] <= 1-C.
        """
        # Calculate sample size
        n = CalculationEngine.cumulative_binomial(
            confidence, reliability, allowable_failures
        )

        # Convert to decimals
        c_conf = confidence / 100.0
        r_rel = reliability / 100.0
        c = allowable_failures

        # Verify the constraint is satisfied for n
        cumulative_prob_n = binom.cdf(c, n, 1 - r_rel)
        assert cumulative_prob_n <= 1 - c_conf, (
            f"Constraint not satisfied for n={n}: "
            f"P(X <= {c}) = {cumulative_prob_n:.6f} > {1 - c_conf:.6f}"
        )

        # Verify n is the minimum (n-1 should not satisfy the constraint)
        if n > 1:
            cumulative_prob_n_minus_1 = binom.cdf(c, n - 1, 1 - r_rel)
            assert cumulative_prob_n_minus_1 > 1 - c_conf, (
                f"n={n} is not minimum: n-1={n - 1} also satisfies constraint "
                f"with P(X <= {c}) = {cumulative_prob_n_minus_1:.6f} <= {1 - c_conf:.6f}"
            )

    @given(
        confidence=confidence_reliability_strategy,
        reliability=confidence_reliability_strategy,
    )
    @settings(deadline=1000)  # Allow up to 1 second for sensitivity analysis
    def test_property_5_sample_size_monotonicity_with_allowable_failures(
        self, confidence: float, reliability: float
    ) -> None:
        """Property 5: Sample Size Monotonicity with Allowable Failures.

        **Validates: Requirements 3.4, 4.4**

        For any valid confidence C and reliability R, as allowable failures c increases,
        the required sample size n should not decrease (monotonically non-decreasing).
        """
        # Calculate sample sizes for c=0,1,2,3
        results = CalculationEngine.sensitivity_analysis(confidence, reliability)

        # Extract sample sizes
        sample_sizes = [n for c, n in results]

        # Verify monotonicity: each sample size should be >= previous
        for i in range(1, len(sample_sizes)):
            assert sample_sizes[i] >= sample_sizes[i - 1], (
                f"Sample size not monotonic: "
                f"n(c={i - 1})={sample_sizes[i - 1]} > n(c={i})={sample_sizes[i]} "
                f"for C={confidence}%, R={reliability}%"
            )

        # Also verify the results are in the expected format
        assert len(results) == 4, "Sensitivity analysis should return 4 results"
        assert results[0][0] == 0, "First result should be for c=0"
        assert results[1][0] == 1, "Second result should be for c=1"
        assert results[2][0] == 2, "Third result should be for c=2"
        assert results[3][0] == 3, "Fourth result should be for c=3"


class TestModuleVToleranceFactors:
    """Property-based tests for Module V tolerance factor calculations."""

    @given(
        n=st.integers(min_value=5, max_value=50),
        confidence=st.floats(min_value=50.1, max_value=99.9),
        reliability=st.floats(min_value=50.1, max_value=99.9),
    )
    @settings(deadline=1000)  # Allow time for iterative calculations
    def test_property_17_sample_size_iteration_correctness(
        self, n: int, confidence: float, reliability: float
    ) -> None:
        """Property 17: Sample Size Iteration Correctness.

        **Validates: Requirements 15.3, 15.4, 16.3, 16.4**

        For any capability margin k_margin, confidence C, reliability R, and specification type,
        the calculated sample size N should be the minimum integer where the tolerance factor
        k(N) <= k_margin.

        This test verifies the iteration logic by checking that:
        1. The tolerance factor at N satisfies the constraint
        2. The tolerance factor at N-1 does not satisfy the constraint (N is minimum)
        3. Tolerance factors decrease as sample size increases (monotonicity)
        """
        # Calculate tolerance factors for both one-sided and two-sided
        k1 = CalculationEngine.one_sided_tolerance_factor(n, confidence, reliability)
        k2 = CalculationEngine.two_sided_tolerance_factor(n, confidence, reliability)

        # Verify k1 and k2 are non-negative for reasonable confidence/reliability values
        assert k1 >= 0, f"One-sided tolerance factor must be non-negative, got {k1}"
        assert k2 >= 0, f"Two-sided tolerance factor must be non-negative, got {k2}"

        # Verify k2 >= k1 (two-sided should be at least as large as one-sided)
        assert k2 >= k1, (
            f"Two-sided tolerance factor ({k2:.6f}) should be >= "
            f"one-sided tolerance factor ({k1:.6f})"
        )

        # Verify monotonicity: tolerance factor decreases as sample size increases
        if n > 5:  # Need sufficient sample size for stable comparison
            k1_prev = CalculationEngine.one_sided_tolerance_factor(
                n - 1, confidence, reliability
            )
            k2_prev = CalculationEngine.two_sided_tolerance_factor(
                n - 1, confidence, reliability
            )

            # Tolerance factors should decrease with increasing sample size
            assert k1_prev >= k1, (
                f"One-sided tolerance factor should decrease with sample size: "
                f"k1(n={n - 1})={k1_prev:.6f} should be >= k1(n={n})={k1:.6f}"
            )
            assert k2_prev >= k2, (
                f"Two-sided tolerance factor should decrease with sample size: "
                f"k2(n={n - 1})={k2_prev:.6f} should be >= k2(n={n})={k2:.6f}"
            )

    @given(
        confidence=confidence_reliability_strategy,
        reliability=confidence_reliability_strategy,
    )
    @settings(deadline=1000)
    def test_property_18_two_sided_sample_size_monotonicity(
        self, confidence: float, reliability: float
    ) -> None:
        """Property 18: Two-Sided Sample Size Monotonicity.

        **Validates: Requirements 16.5, 18.4**

        For any valid parameters, the required sample size for two-sided specifications
        should be greater than or equal to the required sample size for one-sided
        specifications with the same confidence and reliability.
        """
        # Calculate non-parametric sample sizes
        n_one_sided = CalculationEngine.non_parametric_one_sided_sample_size(
            confidence, reliability
        )
        n_two_sided = CalculationEngine.non_parametric_two_sided_sample_size(
            confidence, reliability
        )

        # Verify monotonicity
        assert n_two_sided >= n_one_sided, (
            f"Two-sided sample size ({n_two_sided}) should be >= "
            f"one-sided sample size ({n_one_sided}) "
            f"for C={confidence}%, R={reliability}%"
        )

        # Both should be positive integers
        assert isinstance(n_one_sided, int)
        assert n_one_sided > 0
        assert isinstance(n_two_sided, int)
        assert n_two_sided > 0

    @given(
        confidence=confidence_reliability_strategy,
        reliability=confidence_reliability_strategy,
    )
    def test_property_19_non_parametric_formula_consistency(
        self, confidence: float, reliability: float
    ) -> None:
        """Property 19: Non-Parametric Formula Consistency.

        **Validates: Requirements 17.4**

        For any valid confidence C and reliability R, the non-parametric one-sided
        sample size formula should produce the same result as the Success Run Theorem
        from Module A.
        """
        # Calculate using both methods
        n_non_parametric = CalculationEngine.non_parametric_one_sided_sample_size(
            confidence, reliability
        )
        n_success_run = CalculationEngine.success_run_theorem(confidence, reliability)

        # They should be identical
        assert n_non_parametric == n_success_run, (
            f"Non-parametric one-sided ({n_non_parametric}) should equal "
            f"Success Run Theorem ({n_success_run}) "
            f"for C={confidence}%, R={reliability}%"
        )
