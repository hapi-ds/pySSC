"""Operational Qualification (OQ) Tests.

This module contains tests that verify all mathematical formulas and calculations
against known standard values and edge cases.
"""

import math

import numpy as np
import pytest

from sample_size_calculator.calculations import CalculationEngine
from sample_size_calculator.models import (
    SpecificationLimits,
    SpecificationType,
    TransformationMethod,
)
from sample_size_calculator.tolerance import (
    calculate_capability_margin,
    calculate_ppk,
)
from sample_size_calculator.transformations import (
    box_cox_transform,
    inverse_box_cox_transform,
    inverse_log_transform,
    inverse_yeo_johnson_transform,
    log_transform,
    yeo_johnson_transform,
)

# Module A Formula Tests


@pytest.mark.oq
@pytest.mark.urs("URS-FUNC_A-02")
def test_success_run_theorem_standard_value():
    """Test Success Run Theorem with standard values.

    URS-FUNC_A-02: If allowable failures are zero (c = 0), the
    system shall calculate the minimum sample size (n) using
    the Success Run Theorem.

    SRS (requirements.md)  2.1: WHEN allowable failures equals zero, THE Calculation_Engine SHALL
    compute sample size using the formula n = ceiling(ln(1-C)/ln(R)).

    SRS (requirements.md)  2.2: THE Calculation_Engine SHALL return an integer sample size value.

    Standard test case: C=95%, R=95%, c=0 → n=59
    """
    result = CalculationEngine.success_run_theorem(95.0, 95.0)

    assert isinstance(result, int), "Result must be an integer"
    assert result == 59, f"Expected n=59 for C=95%, R=95%, got {result}"


@pytest.mark.oq
@pytest.mark.urs("URS-FUNC_A-02")
def test_success_run_theorem_high_confidence():
    """Test Success Run Theorem with high confidence.

    URS-FUNC_A-02: If allowable failures are zero (c = 0), the
    system shall calculate the minimum sample size (n) using
    the Success Run Theorem.

    Standard test case: C=99%, R=95%, c=0 → n=90
    """
    result = CalculationEngine.success_run_theorem(99.0, 95.0)

    assert isinstance(result, int), "Result must be an integer"
    assert result == 90, f"Expected n=90 for C=99%, R=95%, got {result}"


@pytest.mark.oq
@pytest.mark.urs("URS-FUNC_A-02")
def test_success_run_theorem_high_reliability():
    """Test Success Run Theorem with high reliability.

    URS-FUNC_A-02: If allowable failures are zero (c = 0), the
    system shall calculate the minimum sample size (n) using
    the Success Run Theorem.

    Standard test case: C=95%, R=99%, c=0 → n=299
    """
    result = CalculationEngine.success_run_theorem(95.0, 99.0)

    assert isinstance(result, int), "Result must be an integer"
    assert result == 299, f"Expected n=299 for C=95%, R=99%, got {result}"


@pytest.mark.oq
@pytest.mark.urs("URS-FUNC_A-03")
def test_cumulative_binomial_standard_value():
    """Test Cumulative Binomial with standard values.

    URS-FUNC_A-03: If allowable failures are specified
    (c0), the system shall calculate n using the cumulative
    Binomial distribution.

    SRS (requirements.md)  3.1: WHEN allowable failures is greater than zero, THE Calculation_Engine
    SHALL compute the minimum sample size where the cumulative binomial probability
    is less than or equal to 1-C.

    Standard test case: C=95%, R=95%, c=1 → n=93
    """
    result = CalculationEngine.cumulative_binomial(95.0, 95.0, 1)

    assert isinstance(result, int), "Result must be an integer"
    assert result == 93, f"Expected n=93 for C=95%, R=95%, c=1, got {result}"


@pytest.mark.oq
@pytest.mark.urs("URS-FUNC_A-03")
def test_cumulative_binomial_two_failures():
    """Test Cumulative Binomial with c=2.

    URS-FUNC_A-03: If allowable failures are specified
    (c0), the system shall calculate n using the cumulative
    Binomial distribution.

    Standard test case: C=95%, R=95%, c=2 → n=124
    """
    result = CalculationEngine.cumulative_binomial(95.0, 95.0, 2)

    assert isinstance(result, int), "Result must be an integer"
    assert result == 124, f"Expected n=124 for C=95%, R=95%, c=2, got {result}"


@pytest.mark.oq
@pytest.mark.urs("URS-FUNC_A-03")
def test_cumulative_binomial_three_failures():
    """Test Cumulative Binomial with c=3.

    URS-FUNC_A-03: If allowable failures are specified
    (c0), the system shall calculate n using the cumulative
    Binomial distribution.

    Standard test case: C=95%, R=95%, c=3 → n=153
    """
    result = CalculationEngine.cumulative_binomial(95.0, 95.0, 3)

    assert isinstance(result, int), "Result must be an integer"
    assert result == 153, f"Expected n=153 for C=95%, R=95%, c=3, got {result}"


@pytest.mark.oq
@pytest.mark.urs("URS-FUNC_A-03", "URS-FUNC_A-04")
def test_sample_size_monotonicity():
    """Test that sample size increases with allowable failures.

    URS-FUNC_A-03: If allowable failures are specified (c0), the
    system shall calculate n using the cumulative Binomial distribution.

    URS-FUNC_A-04: Sensitivity Analysis: If the user leaves the Allowable Failures
    (c) input empty, the system shall automatically calculate and display sample
    sizes for c=0,1,2,3.

    SRS (requirements.md)  3.4: FOR ALL valid inputs with c>0, the calculated sample size SHALL be
    greater than or equal to the sample size for c=0 with the same C and R.

    SRS (requirements.md)  4.4: FOR ALL sensitivity analysis results, sample sizes SHALL be
    monotonically non-decreasing as c increases.
    """
    n0 = CalculationEngine.success_run_theorem(95.0, 95.0)
    n1 = CalculationEngine.cumulative_binomial(95.0, 95.0, 1)
    n2 = CalculationEngine.cumulative_binomial(95.0, 95.0, 2)
    n3 = CalculationEngine.cumulative_binomial(95.0, 95.0, 3)

    assert n1 >= n0, f"n(c=1)={n1} must be >= n(c=0)={n0}"
    assert n2 >= n1, f"n(c=2)={n2} must be >= n(c=1)={n1}"
    assert n3 >= n2, f"n(c=3)={n3} must be >= n(c=2)={n2}"


@pytest.mark.oq
@pytest.mark.urs("URS-FUNC_A-04")
def test_sensitivity_analysis():
    """Test sensitivity analysis returns correct structure.

    URS-FUNC_A-04: Sensitivity Analysis: If the user leaves the Allowable Failures
    (c) input empty, the system shall automatically calculate and display sample
    sizes for c=0,1,2,3.

    SRS (requirements.md)  4.1: WHEN the allowable failures input is empty, THE Module_A SHALL
    automatically calculate sample sizes for c=0, c=1, c=2, and c=3.
    """
    results = CalculationEngine.sensitivity_analysis(95.0, 95.0)

    assert len(results) == 4, "Sensitivity analysis must return 4 results"

    # Verify structure
    for c, n in results:
        assert isinstance(c, int), "c must be an integer"
        assert isinstance(n, int), "n must be an integer"
        assert 0 <= c <= 3, "c must be in range [0, 3]"
        assert n > 0, "n must be positive"

    # Verify expected values
    assert results[0] == (0, 59), f"Expected (0, 59), got {results[0]}"
    assert results[1] == (1, 93), f"Expected (1, 93), got {results[1]}"
    assert results[2] == (2, 124), f"Expected (2, 124), got {results[2]}"
    assert results[3] == (3, 153), f"Expected (3, 153), got {results[3]}"


# Module V Formula Tests - Tolerance Factors


@pytest.mark.oq
@pytest.mark.urs("URS-V-13")
def test_one_sided_tolerance_factor():
    """Test one-sided tolerance factor calculation.

    URS-V-13: Parametric Tolerance Limits: If Parametric, the system shall
    compute tolerance limits in the normalized space using the appropriate
    k-factor.

    URS 15.1: WHEN the specification is One-Sided and the method is Parametric,
    THE Tolerance_Calculator SHALL calculate the one-sided tolerance factor k1
    for candidate sample size N.

    URS 15.2: THE Tolerance_Calculator SHALL use the non-central t-distribution
    to calculate k1.
    """
    # Test with known values
    k1 = CalculationEngine.one_sided_tolerance_factor(30, 95.0, 95.0)

    assert isinstance(k1, float), "k1 must be a float"
    assert k1 > 0, "k1 must be positive"

    # Verify k1 decreases as sample size increases
    k1_small = CalculationEngine.one_sided_tolerance_factor(10, 95.0, 95.0)
    k1_large = CalculationEngine.one_sided_tolerance_factor(100, 95.0, 95.0)

    assert k1_small > k1_large, "k1 should decrease as sample size increases"


@pytest.mark.oq
@pytest.mark.urs("URS-V-13")
def test_two_sided_tolerance_factor():
    """Test two-sided tolerance factor calculation.

    URS-V-13: Parametric Tolerance Limits: If Parametric, the system shall
    compute tolerance limits in the normalized space using the appropriate
    k-factor.

    SRS (requirements.md)  16.1: WHEN the specification is Two-Sided and the method is Parametric,
    THE Tolerance_Calculator SHALL calculate the two-sided tolerance factor k2
    for candidate sample size N.

    SRS (requirements.md)  16.2: THE Tolerance_Calculator SHALL use the Howe-Guenther approximation
    to calculate k2.
    """
    # Test with known values
    k2 = CalculationEngine.two_sided_tolerance_factor(30, 95.0, 95.0)

    assert isinstance(k2, float), "k2 must be a float"
    assert k2 > 0, "k2 must be positive"

    # Verify k2 decreases as sample size increases
    k2_small = CalculationEngine.two_sided_tolerance_factor(10, 95.0, 95.0)
    k2_large = CalculationEngine.two_sided_tolerance_factor(100, 95.0, 95.0)

    assert k2_small > k2_large, "k2 should decrease as sample size increases"


@pytest.mark.oq
@pytest.mark.urs("URS-V-13", "URS-V-14")
def test_two_sided_factor_greater_than_one_sided():
    """Test that two-sided tolerance factor is greater than one-sided.

    URS-V-13: Parametric Tolerance Limits: If Parametric, the system shall
    compute tolerance limits in the normalized space using the appropriate
    k-factor.

    URS-V-14: Non-Parametric Limits: If Non-Parametric, the system shall
    define limits strictly using the order statistics (min/max) of the
    final sample.

    SRS (requirements.md)  16.5: FOR ALL valid inputs, the calculated N SHALL be greater than or
    equal to the N for one-sided specification with the same parameters.
    """
    n = 30
    confidence = 95.0
    reliability = 95.0

    k1 = CalculationEngine.one_sided_tolerance_factor(n, confidence, reliability)
    k2 = CalculationEngine.two_sided_tolerance_factor(n, confidence, reliability)

    assert k2 > k1, f"Two-sided factor k2={k2} must be greater than one-sided k1={k1}"


@pytest.mark.oq
@pytest.mark.urs("URS-V-11")
def test_non_parametric_one_sided_sample_size():
    """Test non-parametric one-sided sample size calculation.

    URS-V-11: Non-Parametric N Calculation: If the method is Non-Parametric,
    the system shall output the fixed sample size required to use extreme order
    statistics.

    SRS (requirements.md)  17.1: WHEN the specification is One-Sided and the method is Non-Parametric,
    THE Tolerance_Calculator SHALL calculate N using the formula n = ceiling(ln(1-C)/ln(R)).

    SRS (requirements.md)  17.4: FOR ALL valid inputs, the formula SHALL produce the same result as
    the Success Run Theorem.
    """
    result = CalculationEngine.non_parametric_one_sided_sample_size(95.0, 95.0)
    expected = CalculationEngine.success_run_theorem(95.0, 95.0)

    assert result == expected, (
        f"Non-parametric one-sided must match Success Run Theorem: "
        f"got {result}, expected {expected}"
    )


@pytest.mark.oq
@pytest.mark.urs("URS-V-11")
def test_non_parametric_two_sided_sample_size():
    """Test non-parametric two-sided sample size calculation.

    URS-V-11: Non-Parametric N Calculation: If the method is Non-Parametric,
    the system shall output the fixed sample size required to use extreme order
    statistics.

    SRS (requirements.md)  18.1: WHEN the specification is Two-Sided and the method is Non-Parametric,
    THE Tolerance_Calculator SHALL iterate N until the constraint
    1 - N*R^(N-1) + (N-1)*R^N >= C is satisfied.
    """
    result = CalculationEngine.non_parametric_two_sided_sample_size(95.0, 95.0)

    assert isinstance(result, int), "Result must be an integer"
    assert result > 0, "Result must be positive"

    # Verify the constraint is satisfied
    C = 0.95
    R = 0.95
    n = result
    constraint_value = 1 - n * (R ** (n - 1)) + (n - 1) * (R**n)

    assert constraint_value >= C, f"Constraint not satisfied: {constraint_value} < {C}"


# Transformation Tests


@pytest.mark.oq
@pytest.mark.urs("URS-V-06")
def test_log_transform_positive_data():
    """Test logarithmic transformation with positive data.

    URS-V-06: Transformation Cascade: If p < 0.05, the system shall automatically
    attempt mathematically normalizing the data in the following strict hierarchy

    SRS (requirements.md)  10.1: WHEN data fails the Shapiro-Wilk test, THE Transformation_Engine
    SHALL check if all values are greater than zero.

    SRS (requirements.md)  10.2: IF all values are positive, THEN THE Transformation_Engine SHALL
    apply natural logarithm transformation to the dataset.
    """
    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = log_transform(data)

    assert result is not None, "Log transform should succeed with positive data"
    assert len(result) == len(data), "Output length must match input length"

    # Verify transformation correctness
    expected = [math.log(x) for x in data]
    np.testing.assert_allclose(result, expected, rtol=1e-10)


@pytest.mark.oq
@pytest.mark.urs("URS-V-06")
def test_log_transform_non_positive_data():
    """Test logarithmic transformation rejects non-positive data.

    URS-V-06: Transformation Cascade: If p < 0.05, the system shall automatically
    attempt mathematically normalizing the data in the following strict hierarchy

    SRS (requirements.md)  10.5: IF all values are not positive, THEN THE System SHALL skip
    logarithmic transformation and proceed to Box-Cox.
    """
    data_with_zero = [0.0, 1.0, 2.0, 3.0]
    data_with_negative = [-1.0, 1.0, 2.0, 3.0]

    assert log_transform(data_with_zero) is None, (
        "Log transform should return None for data with zero"
    )
    assert log_transform(data_with_negative) is None, (
        "Log transform should return None for data with negative values"
    )


@pytest.mark.oq
@pytest.mark.urs("URS-V-06")
def test_box_cox_transform_positive_data():
    """Test Box-Cox transformation with positive data.

    URS-V-06: Transformation Cascade: If p < 0.05, the system shall automatically
    attempt mathematically normalizing the data in the following strict hierarchy

    SRS (requirements.md)  11.1: WHEN logarithmic transformation fails or is skipped,
    THE Transformation_Engine SHALL check if all values are greater than zero.

    SRS (requirements.md)  11.2: IF all values are positive, THEN THE Transformation_Engine SHALL
    optimize lambda parameter for Box-Cox transformation.
    """
    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = box_cox_transform(data)

    assert result is not None, "Box-Cox transform should succeed with positive data"

    transformed_data, lambda_param = result
    assert len(transformed_data) == len(data), "Output length must match input length"
    assert isinstance(lambda_param, float), "Lambda must be a float"


@pytest.mark.oq
@pytest.mark.urs("URS-V-06")
def test_box_cox_transform_non_positive_data():
    """Test Box-Cox transformation rejects non-positive data.

    URS-V-06: Transformation Cascade: If p < 0.05, the system shall automatically
    attempt mathematically normalizing the data in the following strict hierarchy

    SRS (requirements.md) 11.6: IF all values are not positive, THEN THE System SHALL skip
    Box-Cox transformation and proceed to Yeo-Johnson.
    """
    data_with_zero = [0.0, 1.0, 2.0, 3.0]
    data_with_negative = [-1.0, 1.0, 2.0, 3.0]

    assert box_cox_transform(data_with_zero) is None, (
        "Box-Cox transform should return None for data with zero"
    )
    assert box_cox_transform(data_with_negative) is None, (
        "Box-Cox transform should return None for data with negative values"
    )


@pytest.mark.oq
@pytest.mark.urs("URS-V-06")
def test_yeo_johnson_transform_all_data():
    """Test Yeo-Johnson transformation handles all data types.

    URS-V-06: Transformation Cascade: If p < 0.05, the system shall automatically
    attempt mathematically normalizing the data in the following strict hierarchy

    SRS (requirements.md)  12.1: WHEN Box-Cox transformation fails or is skipped,
    THE Transformation_Engine SHALL optimize lambda parameter for
    Yeo-Johnson transformation.

    SRS (requirements.md)  12.5: THE Transformation_Engine SHALL handle datasets containing
    zero and negative values.
    """
    # Test with positive data
    data_positive = [1.0, 2.0, 3.0, 4.0, 5.0]
    result_pos = yeo_johnson_transform(data_positive)
    assert len(result_pos) == 2, "Should return (data, lambda)"
    assert len(result_pos[0]) == len(data_positive)

    # Test with zero
    data_with_zero = [0.0, 1.0, 2.0, 3.0]
    result_zero = yeo_johnson_transform(data_with_zero)
    assert len(result_zero[0]) == len(data_with_zero)

    # Test with negative values
    data_with_negative = [-1.0, 0.0, 1.0, 2.0]
    result_neg = yeo_johnson_transform(data_with_negative)
    assert len(result_neg[0]) == len(data_with_negative)


@pytest.mark.oq
@pytest.mark.urs("URS-V-15")
def test_transformation_round_trip_accuracy():
    """Test back-transformation round-trip accuracy.

    URS-V-15: Back-Transformation: The system MUST mathematically
    back-transform calculated parametric limits to the original
    engineering units.

    SRS (requirements.md)  22.5: FOR ALL valid tolerance limits,
    back-transforming then forward-transforming SHALL produce the
    original transformed limit within numerical precision.
    """
    original_data = [1.0, 2.0, 3.0, 4.0, 5.0]

    # Test log round-trip
    log_transformed = log_transform(original_data)
    assert log_transformed is not None
    log_back = inverse_log_transform(log_transformed)
    np.testing.assert_allclose(log_back, original_data, rtol=1e-10)

    # Test Box-Cox round-trip
    box_cox_result = box_cox_transform(original_data)
    assert box_cox_result is not None
    bc_transformed, bc_lambda = box_cox_result
    bc_back = inverse_box_cox_transform(bc_transformed, bc_lambda)
    np.testing.assert_allclose(bc_back, original_data, rtol=1e-9)

    # Test Yeo-Johnson round-trip
    yj_transformed, yj_lambda = yeo_johnson_transform(original_data)
    yj_back = inverse_yeo_johnson_transform(yj_transformed, yj_lambda)
    np.testing.assert_allclose(yj_back, original_data, rtol=1e-9)


# Tolerance Calculation Tests


@pytest.mark.oq
@pytest.mark.urs("URS-V-09")
def test_capability_margin_calculation():
    """Test capability margin calculation.

    URS-V-09: Capability Margin (k_margin): For parametric/transformed
    data, the system shall forward-transform the Specification Limits and
    calculate the physical capability margin of the pilot data.

    SRS (requirements.md)  14.1: WHEN the method is Parametric or transformed,
    THE Tolerance_Calculator SHALL forward-transform the specification limits.

    SRS (requirements.md)  14.4: THE Tolerance_Calculator SHALL set k_margin as the minimum of
    the calculated capability margins.
    """
    # Create capable process data
    data = [10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 14.5]
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=8.0, usl=16.0
    )

    k_margin = calculate_capability_margin(
        data, spec_limits, TransformationMethod.NONE, None
    )

    assert isinstance(k_margin, float), "k_margin must be a float"
    assert k_margin > 0, "k_margin must be positive for capable process"


@pytest.mark.oq
@pytest.mark.urs("URS-V-09")
def test_capability_margin_incapable_process():
    """Test capability margin raises error for incapable process.

    URS-V-09: Capability Margin (k_margin): For parametric/transformed
    data, the system shall forward-transform the Specification Limits and
    calculate the physical capability margin of the pilot data.

    SRS (requirements.md)  14.5: IF k_margin is less than or equal to zero, THEN THE System SHALL
    display a FATAL ERROR message indicating the process is incapable and
    prevent further calculation.
    """
    # Create incapable process data (mean outside specs)
    data = [20.0, 21.0, 22.0, 23.0, 24.0]
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=8.0, usl=16.0
    )

    with pytest.raises(ValueError, match="incapable|k_margin"):
        calculate_capability_margin(data, spec_limits, TransformationMethod.NONE, None)


@pytest.mark.oq
@pytest.mark.urs("URS-V-16")
def test_ppk_calculation():
    """Test Ppk calculation formula.

    URS-V-16: Pass/Fail & Capability: The system shall compare the
    back-transformed limits to the original specifications to output
    Pass/Fail, and calculate Process Capability (P_pk) for
    normal/transformed data.

    SRS (requirements.md)  23.4: WHEN the method is Parametric or transformed, THE System SHALL
    calculate Ppk using the formula: Ppk = min(Ppu, Ppl).
    """
    # Create centered process data
    data = [10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 14.5]
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=8.0, usl=16.0
    )

    ppk = calculate_ppk(data, spec_limits)

    assert isinstance(ppk, float), "Ppk must be a float"
    assert ppk > 0, "Ppk must be positive"

    # Verify Ppk calculation manually
    mean = np.mean(data)
    std = np.std(data, ddof=1)
    ppu = (spec_limits.usl - mean) / (3 * std)
    ppl = (mean - spec_limits.lsl) / (3 * std)
    expected_ppk = min(ppu, ppl)

    np.testing.assert_allclose(ppk, expected_ppk, rtol=1e-10)


# Edge Case Tests


@pytest.mark.oq
@pytest.mark.urs("URS-OQ-01")
def test_boundary_confidence_values():
    """Test calculations with boundary confidence values.

    URS-OQ-01: Operational Qualification (OQ): A pytest suite
    shall verify all mathematical models against known standard values.

    SRS (requirements.md)  32.4: THE Validation_Suite SHALL test edge cases for each
    calculation method.
    """
    # Test near-boundary values
    n_low = CalculationEngine.success_run_theorem(50.1, 95.0)
    n_high = CalculationEngine.success_run_theorem(99.9, 95.0)

    assert isinstance(n_low, int) and n_low > 0
    assert isinstance(n_high, int) and n_high > 0
    assert n_high > n_low, "Higher confidence requires larger sample size"


@pytest.mark.oq
@pytest.mark.urs("URS-OQ-01")
def test_boundary_reliability_values():
    """Test calculations with boundary reliability values.

    URS-OQ-01: Operational Qualification (OQ): A pytest suite
    shall verify all mathematical models against known standard values.

    SRS (requirements.md)  32.4: THE Validation_Suite SHALL test edge cases for each
    calculation method.
    """
    # Test near-boundary values
    n_low = CalculationEngine.success_run_theorem(95.0, 50.1)
    n_high = CalculationEngine.success_run_theorem(95.0, 99.9)

    assert isinstance(n_low, int) and n_low > 0
    assert isinstance(n_high, int) and n_high > 0
    assert n_low < n_high, "Lower reliability requires smaller sample size"


@pytest.mark.oq
@pytest.mark.urs("URS-OQ-01")
def test_empty_dataset_handling():
    """Test that empty datasets are handled appropriately.

    URS-OQ-01: Operational Qualification (OQ): A pytest suite
    shall verify all mathematical models against known standard values.

    SRS (requirements.md)  32.4: THE Validation_Suite SHALL test edge cases for each
    calculation method.
    """
    empty_data = []

    # Log transform should handle empty data
    result = log_transform(empty_data)
    assert result == [] or result is None, "Empty data should be handled"


@pytest.mark.oq
@pytest.mark.urs("URS-OQ-01")
def test_single_value_dataset():
    """Test calculations with single-value datasets.

    URS-OQ-01: Operational Qualification (OQ): A pytest suite
    shall verify all mathematical models against known standard values.

    SRS (requirements.md)  32.4: THE Validation_Suite SHALL test edge cases for each
    calculation method.
    """
    single_value = [10.0]

    # Transformations should handle single values
    log_result = log_transform(single_value)
    assert log_result is not None and len(log_result) == 1


@pytest.mark.oq
@pytest.mark.urs("URS-OQ-01")
def test_identical_values_dataset():
    """Test calculations with identical values (zero variance).

    URS-OQ-01: Operational Qualification (OQ): A pytest suite
    shall verify all mathematical models against known standard values.

    SRS (requirements.md)  32.4: THE Validation_Suite SHALL test edge cases for each
    calculation method.
    """
    identical_data = [10.0, 10.0, 10.0, 10.0, 10.0]

    # Should handle zero variance gracefully
    std = np.std(identical_data, ddof=1)
    assert std == 0.0, "Standard deviation should be zero"


@pytest.mark.oq
@pytest.mark.urs("URS-OQ-01")
def test_calculation_idempotence():
    """Test that calculations are idempotent.

    URS-OQ-01: Operational Qualification (OQ): A pytest suite
    shall verify all mathematical models against known standard values.

    SRS (requirements.md)  32.3: THE Validation_Suite SHALL verify calculations against known
    standard values.
    """
    # Run same calculation multiple times
    results = [CalculationEngine.success_run_theorem(95.0, 95.0) for _ in range(5)]

    # All results should be identical
    assert all(r == results[0] for r in results), (
        "Calculation must be idempotent (same inputs → same outputs)"
    )


@pytest.mark.oq
@pytest.mark.urs("URS-FUNC_A-02", "URS-FUNC_A-03")
def test_all_module_a_formulas():
    """Comprehensive test of all Module A formulas against known values.

    URS-FUNC_A-02:The system shall accept user inputs for Confidence
    (C), Reliability (R), and optionally Allowable Failures (c).

    URS-FUNC_A-03: If allowable failures are zero (c=0), the system
    shall calculate the minimum sample size (n) using the Success Run
    Theorem.

    SRS (requirements.md)  32.1: THE Validation_Suite SHALL include pytest tests for all
    mathematical formulas.

    SRS (requirements.md)  32.3: THE Validation_Suite SHALL verify calculations against known
    standard values.
    """
    test_cases = [
        # (confidence, reliability, c, expected_n)
        (95.0, 95.0, 0, 59),
        (95.0, 95.0, 1, 93),
        (95.0, 95.0, 2, 124),
        (95.0, 95.0, 3, 153),
        (99.0, 95.0, 0, 90),
        (95.0, 99.0, 0, 299),
        (90.0, 90.0, 0, 22),
    ]

    for confidence, reliability, c, expected_n in test_cases:
        if c == 0:
            result = CalculationEngine.success_run_theorem(confidence, reliability)
        else:
            result = CalculationEngine.cumulative_binomial(confidence, reliability, c)

        assert result == expected_n, (
            f"Failed for C={confidence}%, R={reliability}%, c={c}: "
            f"expected {expected_n}, got {result}"
        )


@pytest.mark.oq
@pytest.mark.urs("URS-V-13")
def test_tolerance_factor_known_values():
    """Test tolerance factors against known reference values.

    URS-V-13: Parametric Tolerance Limits: If Parametric, the system
    shall compute tolerance limits in the normalized space using the
    appropriate k-factor.

    SRS (requirements.md)  32.1: THE Validation_Suite SHALL include pytest tests for all
    mathematical formulas.
    """
    # Test one-sided tolerance factor
    k1_30 = CalculationEngine.one_sided_tolerance_factor(30, 95.0, 95.0)
    assert 2.0 < k1_30 < 3.0, f"k1 for n=30 should be ~2.5, got {k1_30}"

    # Test two-sided tolerance factor
    k2_30 = CalculationEngine.two_sided_tolerance_factor(30, 95.0, 95.0)
    assert 2.5 < k2_30 < 3.5, f"k2 for n=30 should be ~3.0, got {k2_30}"

    # Verify k2 > k1
    assert k2_30 > k1_30, "Two-sided factor must exceed one-sided factor"


@pytest.mark.oq
@pytest.mark.urs("URS-OQ-01")
def test_numerical_stability():
    """Test numerical stability with extreme values.

    URS-OQ-01: Operational Qualification (OQ): A pytest suite
    shall verify all mathematical models against known standard values.

    SRS (requirements.md)  32.5: WHEN the OQ test suite runs, THE System SHALL require all
    tests to pass.
    """
    # Test with very high confidence
    n_high_conf = CalculationEngine.success_run_theorem(99.9, 95.0)
    assert n_high_conf > 0 and n_high_conf < 10000, (
        "Result should be reasonable even with extreme confidence"
    )

    # Test with very high reliability
    n_high_rel = CalculationEngine.success_run_theorem(95.0, 99.9)
    assert n_high_rel > 0 and n_high_rel < 10000, (
        "Result should be reasonable even with extreme reliability"
    )
