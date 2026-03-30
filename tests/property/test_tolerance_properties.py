"""Property-based tests for tolerance calculator module.

This module contains property-based tests using Hypothesis to verify
universal correctness properties of tolerance interval calculations,
capability margin calculations, and Pass/Fail determination.
"""

import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from sample_size_calculator.models import (
    AnalysisMethod,
    Phase2Results,
    Phase3Results,
    SpecificationLimits,
    SpecificationType,
    TransformationMethod,
)
from sample_size_calculator.tolerance import calculate_capability_margin

# Strategy for generating valid pilot data
pilot_data_strategy = st.lists(
    st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False),
    min_size=5,
    max_size=30,
)

# Strategy for positive pilot data (for log/box-cox transformations)
positive_data_strategy = st.lists(
    st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    min_size=5,
    max_size=30,
)

# Strategy for lambda parameters
lambda_strategy = st.floats(min_value=-2.0, max_value=2.0, allow_nan=False)


@pytest.mark.property
@given(
    data=positive_data_strategy,
    lsl=st.floats(min_value=0.1, max_value=5.0),
    usl=st.floats(min_value=50.0, max_value=200.0),
)
@settings(max_examples=50, deadline=None)
def test_property_16_capability_margin_calculation_correctness(
    data: list[float], lsl: float, usl: float
):
    """Property 16: Capability Margin Calculation Correctness.

    **Validates: Requirements 14.1, 14.2, 14.3, 14.4**

    This property verifies that the capability margin calculation:
    1. Returns a positive value when the mean is within specification limits
    2. Correctly calculates the minimum distance to specification limits
    3. Handles transformation methods appropriately
    4. Raises ValueError when process is incapable (k_margin <= 0)

    The capability margin should be:
    - k_margin = min((mean - LSL)/std, (USL - mean)/std)
    - Always positive for capable processes
    - Consistent across different transformation methods
    """
    # Ensure data has reasonable spread
    if np.std(data, ddof=1) < 0.01:
        return  # Skip degenerate cases

    # Create specification limits
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=lsl, usl=usl
    )

    # Calculate mean and std
    mean = np.mean(data)
    std = np.std(data, ddof=1)

    # Only test if mean is within spec limits (capable process)
    if mean <= lsl or mean >= usl:
        # Process is incapable - should raise ValueError
        with pytest.raises(ValueError, match="Process is incapable"):
            calculate_capability_margin(
                data, spec_limits, TransformationMethod.NONE, None
            )
        return

    # Calculate capability margin with no transformation
    k_margin = calculate_capability_margin(
        data, spec_limits, TransformationMethod.NONE, None
    )

    # Property 1: k_margin should be positive for capable processes
    assert k_margin > 0, "Capability margin must be positive for capable processes"

    # Property 2: k_margin should equal the minimum of the two margins
    lower_margin = (mean - lsl) / std
    upper_margin = (usl - mean) / std
    expected_k_margin = min(lower_margin, upper_margin)

    assert math.isclose(k_margin, expected_k_margin, rel_tol=1e-9), (
        f"k_margin {k_margin} should equal min of margins {expected_k_margin}"
    )

    # Property 3: k_margin should be less than or equal to both individual margins
    assert k_margin <= lower_margin + 1e-9, "k_margin should not exceed lower margin"
    assert k_margin <= upper_margin + 1e-9, "k_margin should not exceed upper margin"


@pytest.mark.property
@given(
    data=positive_data_strategy,
    lsl=st.floats(min_value=0.1, max_value=5.0),
    usl=st.floats(min_value=50.0, max_value=200.0),
)
@settings(max_examples=30, deadline=None)
def test_property_16_capability_margin_with_log_transformation(
    data: list[float], lsl: float, usl: float
):
    """Property 16: Capability Margin with Logarithmic Transformation.

    **Validates: Requirements 14.1, 14.2, 14.3**

    Verifies that capability margin calculation correctly handles
    logarithmic transformation by forward-transforming specification limits.
    """
    from sample_size_calculator.transformations import log_transform

    # Ensure data has reasonable spread
    if np.std(data, ddof=1) < 0.01:
        return

    # Transform the data
    log_data = log_transform(data)
    if log_data is None:
        return

    # Create specification limits
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=lsl, usl=usl
    )

    # Calculate mean and std of transformed data
    mean_t = np.mean(log_data)
    std_t = np.std(log_data, ddof=1)

    # Transform spec limits
    lsl_t = math.log(lsl)
    usl_t = math.log(usl)

    # Only test if mean is within transformed spec limits
    if mean_t <= lsl_t or mean_t >= usl_t:
        with pytest.raises(ValueError, match="Process is incapable"):
            calculate_capability_margin(
                log_data, spec_limits, TransformationMethod.LOGARITHMIC, None
            )
        return

    # Calculate capability margin
    k_margin = calculate_capability_margin(
        log_data, spec_limits, TransformationMethod.LOGARITHMIC, None
    )

    # Verify k_margin is calculated correctly in transformed space
    lower_margin = (mean_t - lsl_t) / std_t
    upper_margin = (usl_t - mean_t) / std_t
    expected_k_margin = min(lower_margin, upper_margin)

    assert math.isclose(k_margin, expected_k_margin, rel_tol=1e-9)
    assert k_margin > 0


@pytest.mark.property
@given(
    data=positive_data_strategy,
    lsl=st.floats(min_value=0.1, max_value=5.0),
    usl=st.floats(min_value=50.0, max_value=200.0),
    lambda_param=lambda_strategy,
)
@settings(max_examples=30, deadline=None)
def test_property_16_capability_margin_with_box_cox_transformation(
    data: list[float], lsl: float, usl: float, lambda_param: float
):
    """Property 16: Capability Margin with Box-Cox Transformation.

    **Validates: Requirements 14.1, 14.2, 14.3**

    Verifies that capability margin calculation correctly handles
    Box-Cox transformation with the provided lambda parameter.
    """
    # Ensure data has reasonable spread
    if np.std(data, ddof=1) < 0.01:
        return

    # Apply Box-Cox transformation manually
    if abs(lambda_param) < 1e-10:  # lambda ≈ 0
        transformed_data = [math.log(x) for x in data]
    else:
        transformed_data = [(x**lambda_param - 1) / lambda_param for x in data]

    # Create specification limits
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=lsl, usl=usl
    )

    # Calculate mean and std of transformed data
    mean_t = np.mean(transformed_data)
    std_t = np.std(transformed_data, ddof=1)

    # Transform spec limits
    if abs(lambda_param) < 1e-10:
        lsl_t = math.log(lsl)
        usl_t = math.log(usl)
    else:
        lsl_t = (lsl**lambda_param - 1) / lambda_param
        usl_t = (usl**lambda_param - 1) / lambda_param

    # Only test if mean is within transformed spec limits
    if mean_t <= lsl_t or mean_t >= usl_t:
        with pytest.raises(ValueError, match="Process is incapable"):
            calculate_capability_margin(
                transformed_data,
                spec_limits,
                TransformationMethod.BOX_COX,
                lambda_param,
            )
        return

    # Calculate capability margin
    k_margin = calculate_capability_margin(
        transformed_data, spec_limits, TransformationMethod.BOX_COX, lambda_param
    )

    # Verify k_margin is calculated correctly in transformed space
    lower_margin = (mean_t - lsl_t) / std_t
    upper_margin = (usl_t - mean_t) / std_t
    expected_k_margin = min(lower_margin, upper_margin)

    assert math.isclose(k_margin, expected_k_margin, rel_tol=1e-9)
    assert k_margin > 0


@pytest.mark.property
@given(
    data=positive_data_strategy,
    lsl=st.floats(min_value=0.1, max_value=5.0),
)
@settings(max_examples=30, deadline=None)
def test_property_16_capability_margin_one_sided_lsl(data: list[float], lsl: float):
    """Property 16: Capability Margin for One-Sided LSL Specification.

    **Validates: Requirements 14.1, 14.2, 14.3, 14.4**

    Verifies that capability margin calculation correctly handles
    one-sided lower specification limit (LSL only).
    """
    # Ensure data has reasonable spread
    if np.std(data, ddof=1) < 0.01:
        return

    # Create one-sided specification limits (LSL only)
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.ONE_SIDED, lsl=lsl, usl=None
    )

    # Calculate mean and std
    mean = np.mean(data)
    std = np.std(data, ddof=1)

    # Only test if mean is above LSL (capable process)
    if mean <= lsl:
        with pytest.raises(ValueError, match="Process is incapable"):
            calculate_capability_margin(
                data, spec_limits, TransformationMethod.NONE, None
            )
        return

    # Calculate capability margin
    k_margin = calculate_capability_margin(
        data, spec_limits, TransformationMethod.NONE, None
    )

    # For one-sided LSL, k_margin should equal (mean - LSL) / std
    expected_k_margin = (mean - lsl) / std

    assert math.isclose(k_margin, expected_k_margin, rel_tol=1e-9)
    assert k_margin > 0


@pytest.mark.property
@given(
    data=positive_data_strategy,
    usl=st.floats(min_value=50.0, max_value=200.0),
)
@settings(max_examples=30, deadline=None)
def test_property_16_capability_margin_one_sided_usl(data: list[float], usl: float):
    """Property 16: Capability Margin for One-Sided USL Specification.

    **Validates: Requirements 14.1, 14.2, 14.3, 14.4**

    Verifies that capability margin calculation correctly handles
    one-sided upper specification limit (USL only).
    """
    # Ensure data has reasonable spread
    if np.std(data, ddof=1) < 0.01:
        return

    # Create one-sided specification limits (USL only)
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.ONE_SIDED, lsl=None, usl=usl
    )

    # Calculate mean and std
    mean = np.mean(data)
    std = np.std(data, ddof=1)

    # Only test if mean is below USL (capable process)
    if mean >= usl:
        with pytest.raises(ValueError, match="Process is incapable"):
            calculate_capability_margin(
                data, spec_limits, TransformationMethod.NONE, None
            )
        return

    # Calculate capability margin
    k_margin = calculate_capability_margin(
        data, spec_limits, TransformationMethod.NONE, None
    )

    # For one-sided USL, k_margin should equal (USL - mean) / std
    expected_k_margin = (usl - mean) / std

    assert math.isclose(k_margin, expected_k_margin, rel_tol=1e-9)
    assert k_margin > 0


@pytest.mark.property
@given(
    sample_size=st.integers(min_value=5, max_value=50),
)
@settings(max_examples=30, deadline=None)
def test_property_20_final_dataset_size_validation(sample_size: int):
    """Property 20: Final Dataset Size Validation.

    **Validates: Requirements 19.2**

    This property verifies that the calculate_tolerance_limits function
    correctly validates that the final dataset size matches the required
    sample size from Phase 3.
    """
    from sample_size_calculator.tolerance import calculate_tolerance_limits

    # Create mock phase results
    final_data = [10.0] * (sample_size - 1)  # Intentionally wrong size
    phase2 = Phase2Results(
        cleaned_data=final_data,
        shapiro_p_value=0.8,
        transformation_method=TransformationMethod.NONE,
        analysis_method=AnalysisMethod.PARAMETRIC,
        lambda_param=None,
        manual_override=False,
    )
    phase3 = Phase3Results(
        required_sample_size=sample_size,  # Expects sample_size
        k_margin=3.0,
        k_factor=2.5,
        specification_type=SpecificationType.TWO_SIDED,
    )
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=5.0, usl=20.0
    )

    # Should raise ValueError due to size mismatch
    with pytest.raises(ValueError, match="must contain at least"):
        calculate_tolerance_limits(final_data, phase2, phase3, spec_limits)

    # Now test with correct size - should not raise
    correct_data = [10.0] * sample_size
    phase2_correct = Phase2Results(
        cleaned_data=correct_data,
        shapiro_p_value=0.8,
        transformation_method=TransformationMethod.NONE,
        analysis_method=AnalysisMethod.PARAMETRIC,
        lambda_param=None,
        manual_override=False,
    )
    result = calculate_tolerance_limits(
        correct_data, phase2_correct, phase3, spec_limits
    )
    assert len(result.final_data) == sample_size


@pytest.mark.property
@given(
    data=positive_data_strategy,
    lambda_param=lambda_strategy,
)
@settings(max_examples=30, deadline=None)
def test_property_21_transformation_consistency(data: list[float], lambda_param: float):
    """Property 21: Transformation Consistency.

    **Validates: Requirements 19.3, 19.5**

    This property verifies that the locked transformation method from Phase 2
    is consistently applied to the final dataset in Phase 4, producing data
    in the same normalized space as the pilot data.
    """
    from sample_size_calculator.tolerance import calculate_tolerance_limits
    from sample_size_calculator.transformations import (
        log_transform,
    )

    # Test with logarithmic transformation
    log_data = log_transform(data)
    if log_data is not None:
        phase2_log = Phase2Results(
            cleaned_data=log_data,
            shapiro_p_value=0.8,
            transformation_method=TransformationMethod.LOGARITHMIC,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=None,
            manual_override=False,
        )
        phase3 = Phase3Results(
            required_sample_size=len(data),
            k_margin=3.0,
            k_factor=2.5,
            specification_type=SpecificationType.TWO_SIDED,
        )
        spec_limits = SpecificationLimits(
            spec_type=SpecificationType.TWO_SIDED, lsl=0.1, usl=200.0
        )

        # The function should apply the same transformation internally
        result = calculate_tolerance_limits(data, phase2_log, phase3, spec_limits)

        # Verify the transformation was applied (tolerance limits should be back-transformed)
        assert "lower" in result.tolerance_limits
        assert "upper" in result.tolerance_limits
        # Back-transformed limits should be positive
        assert result.tolerance_limits["lower"] > 0
        assert result.tolerance_limits["upper"] > 0


@pytest.mark.property
@given(
    data=positive_data_strategy,
    lsl=st.floats(min_value=0.1, max_value=5.0),
    usl=st.floats(min_value=50.0, max_value=200.0),
)
@settings(max_examples=30, deadline=None)
def test_property_22_parametric_tolerance_limit_formula_correctness(
    data: list[float], lsl: float, usl: float
):
    """Property 22: Parametric Tolerance Limit Formula Correctness.

    **Validates: Requirements 20.1, 20.2, 20.3**

    This property verifies that parametric tolerance limits are calculated
    correctly using the formula: Limits = mean ± k * std
    """
    from sample_size_calculator.tolerance import calculate_tolerance_limits

    # Ensure data has reasonable spread
    if np.std(data, ddof=1) < 0.01:
        return

    # Use no transformation for simplicity
    phase2 = Phase2Results(
        cleaned_data=data,
        shapiro_p_value=0.8,
        transformation_method=TransformationMethod.NONE,
        analysis_method=AnalysisMethod.PARAMETRIC,
        lambda_param=None,
        manual_override=False,
    )

    k_factor = 2.5
    phase3 = Phase3Results(
        required_sample_size=len(data),
        k_margin=3.0,
        k_factor=k_factor,
        specification_type=SpecificationType.TWO_SIDED,
    )
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=lsl, usl=usl
    )

    result = calculate_tolerance_limits(data, phase2, phase3, spec_limits)

    # Calculate expected limits
    mean = np.mean(data)
    std = np.std(data, ddof=1)
    expected_lower = mean - k_factor * std
    expected_upper = mean + k_factor * std

    # Verify the formula is applied correctly
    assert math.isclose(result.tolerance_limits["lower"], expected_lower, rel_tol=1e-9)
    assert math.isclose(result.tolerance_limits["upper"], expected_upper, rel_tol=1e-9)


@pytest.mark.property
@given(
    data=positive_data_strategy,
    lsl=st.floats(min_value=0.1, max_value=5.0),
    usl=st.floats(min_value=50.0, max_value=200.0),
)
@settings(max_examples=30, deadline=None)
def test_property_23_non_parametric_tolerance_limits_as_extreme_order_statistics(
    data: list[float], lsl: float, usl: float
):
    """Property 23: Non-Parametric Tolerance Limits as Extreme Order Statistics.

    **Validates: Requirements 21.1, 21.2, 21.3, 21.5**

    This property verifies that non-parametric tolerance limits are correctly
    calculated as the extreme order statistics (minimum and maximum values).
    """
    from sample_size_calculator.tolerance import calculate_tolerance_limits

    # Use non-parametric method
    phase2 = Phase2Results(
        cleaned_data=data,
        shapiro_p_value=0.01,  # Failed normality test
        transformation_method=TransformationMethod.NONE,
        analysis_method=AnalysisMethod.NON_PARAMETRIC,
        lambda_param=None,
        manual_override=False,
    )

    # Test two-sided specification
    phase3_two_sided = Phase3Results(
        required_sample_size=len(data),
        k_margin=0.0,  # Not used for non-parametric
        k_factor=0.0,  # Not used for non-parametric
        specification_type=SpecificationType.TWO_SIDED,
    )
    spec_limits_two_sided = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=lsl, usl=usl
    )

    result_two_sided = calculate_tolerance_limits(
        data, phase2, phase3_two_sided, spec_limits_two_sided
    )

    # For two-sided, limits should be min and max
    assert result_two_sided.tolerance_limits["lower"] == min(data)
    assert result_two_sided.tolerance_limits["upper"] == max(data)

    # Test one-sided LSL specification
    phase3_one_sided_lsl = Phase3Results(
        required_sample_size=len(data),
        k_margin=0.0,
        k_factor=0.0,
        specification_type=SpecificationType.ONE_SIDED,
    )
    spec_limits_one_sided_lsl = SpecificationLimits(
        spec_type=SpecificationType.ONE_SIDED, lsl=lsl, usl=None
    )

    result_one_sided_lsl = calculate_tolerance_limits(
        data, phase2, phase3_one_sided_lsl, spec_limits_one_sided_lsl
    )

    # For one-sided LSL, limit should be minimum
    assert result_one_sided_lsl.tolerance_limits["lower"] == min(data)
    assert "upper" not in result_one_sided_lsl.tolerance_limits

    # Test one-sided USL specification
    spec_limits_one_sided_usl = SpecificationLimits(
        spec_type=SpecificationType.ONE_SIDED, lsl=None, usl=usl
    )

    result_one_sided_usl = calculate_tolerance_limits(
        data, phase2, phase3_one_sided_lsl, spec_limits_one_sided_usl
    )

    # For one-sided USL, limit should be maximum
    assert result_one_sided_usl.tolerance_limits["upper"] == max(data)
    assert "lower" not in result_one_sided_usl.tolerance_limits


@pytest.mark.property
@given(
    data=positive_data_strategy,
    lsl=st.floats(min_value=0.1, max_value=5.0),
    usl=st.floats(min_value=50.0, max_value=200.0),
)
@settings(max_examples=30, deadline=None)
def test_property_25_pass_fail_determination_correctness(
    data: list[float], lsl: float, usl: float
):
    """Property 25: Pass/Fail Determination Correctness.

    **Validates: Requirements 23.1, 23.2, 23.3**

    This property verifies that Pass/Fail determination is correct:
    - Pass if all tolerance limits are within specification limits
    - Fail if any tolerance limit exceeds a specification limit
    """
    from sample_size_calculator.tolerance import calculate_tolerance_limits

    # Ensure data has reasonable spread
    if np.std(data, ddof=1) < 0.01:
        return

    # Use no transformation for simplicity
    phase2 = Phase2Results(
        cleaned_data=data,
        shapiro_p_value=0.8,
        transformation_method=TransformationMethod.NONE,
        analysis_method=AnalysisMethod.PARAMETRIC,
        lambda_param=None,
        manual_override=False,
    )

    k_factor = 2.5
    phase3 = Phase3Results(
        required_sample_size=len(data),
        k_margin=3.0,
        k_factor=k_factor,
        specification_type=SpecificationType.TWO_SIDED,
    )
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=lsl, usl=usl
    )

    result = calculate_tolerance_limits(data, phase2, phase3, spec_limits)

    # Verify Pass/Fail logic
    lower_limit = result.tolerance_limits.get("lower")
    upper_limit = result.tolerance_limits.get("upper")

    # Determine expected Pass/Fail
    expected_pass_fail = "Pass"
    if lower_limit is not None and lower_limit < lsl:
        expected_pass_fail = "Fail"
    if upper_limit is not None and upper_limit > usl:
        expected_pass_fail = "Fail"

    assert result.pass_fail == expected_pass_fail, (
        f"Expected {expected_pass_fail} but got {result.pass_fail}. "
        f"Lower: {lower_limit} vs LSL: {lsl}, Upper: {upper_limit} vs USL: {usl}"
    )


@pytest.mark.property
@given(
    data=positive_data_strategy,
    lsl=st.floats(min_value=0.1, max_value=5.0),
    usl=st.floats(min_value=50.0, max_value=200.0),
)
@settings(max_examples=30, deadline=None)
def test_property_26_ppk_calculation_formula(data: list[float], lsl: float, usl: float):
    """Property 26: Ppk Calculation Formula.

    **Validates: Requirements 23.4**

    This property verifies that Ppk is calculated correctly using the formula:
    - Ppu = (USL - mean) / (3 * std)
    - Ppl = (mean - LSL) / (3 * std)
    - Ppk = min(Ppu, Ppl)
    """
    from sample_size_calculator.tolerance import calculate_ppk

    # Ensure data has reasonable spread
    if np.std(data, ddof=1) < 0.01:
        return

    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=lsl, usl=usl
    )

    ppk = calculate_ppk(data, spec_limits)

    # Calculate expected Ppk
    mean = np.mean(data)
    std = np.std(data, ddof=1)

    ppl = (mean - lsl) / (3 * std)
    ppu = (usl - mean) / (3 * std)
    expected_ppk = min(ppl, ppu)

    assert math.isclose(ppk, expected_ppk, rel_tol=1e-9), (
        f"Ppk {ppk} should equal min(Ppl, Ppu) = {expected_ppk}"
    )

    # Ppk should be the minimum of the two indices
    assert ppk <= ppl + 1e-9, "Ppk should not exceed Ppl"
    assert ppk <= ppu + 1e-9, "Ppk should not exceed Ppu"


@pytest.mark.property
@given(
    data=positive_data_strategy,
    lsl=st.floats(min_value=0.1, max_value=5.0),
)
@settings(max_examples=30, deadline=None)
def test_property_26_ppk_one_sided_lsl(data: list[float], lsl: float):
    """Property 26: Ppk Calculation for One-Sided LSL.

    **Validates: Requirements 23.4**

    Verifies Ppk calculation for one-sided lower specification limit.
    """
    from sample_size_calculator.tolerance import calculate_ppk

    # Ensure data has reasonable spread
    if np.std(data, ddof=1) < 0.01:
        return

    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.ONE_SIDED, lsl=lsl, usl=None
    )

    ppk = calculate_ppk(data, spec_limits)

    # For one-sided LSL, Ppk should equal Ppl
    mean = np.mean(data)
    std = np.std(data, ddof=1)
    expected_ppk = (mean - lsl) / (3 * std)

    assert math.isclose(ppk, expected_ppk, rel_tol=1e-9)


@pytest.mark.property
@given(
    data=positive_data_strategy,
    usl=st.floats(min_value=50.0, max_value=200.0),
)
@settings(max_examples=30, deadline=None)
def test_property_26_ppk_one_sided_usl(data: list[float], usl: float):
    """Property 26: Ppk Calculation for One-Sided USL.

    **Validates: Requirements 23.4**

    Verifies Ppk calculation for one-sided upper specification limit.
    """
    from sample_size_calculator.tolerance import calculate_ppk

    # Ensure data has reasonable spread
    if np.std(data, ddof=1) < 0.01:
        return

    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.ONE_SIDED, lsl=None, usl=usl
    )

    ppk = calculate_ppk(data, spec_limits)

    # For one-sided USL, Ppk should equal Ppu
    mean = np.mean(data)
    std = np.std(data, ddof=1)
    expected_ppk = (usl - mean) / (3 * std)

    assert math.isclose(ppk, expected_ppk, rel_tol=1e-9)


@pytest.mark.property
@given(
    data=positive_data_strategy,
    lsl=st.floats(min_value=0.1, max_value=5.0),
    usl=st.floats(min_value=50.0, max_value=200.0),
)
@settings(max_examples=30, deadline=None)
def test_property_25_non_parametric_no_ppk(data: list[float], lsl: float, usl: float):
    """Property 25: Non-Parametric Methods Do Not Calculate Ppk.

    **Validates: Requirements 23.5**

    Verifies that Ppk is None for non-parametric methods.
    """
    from sample_size_calculator.tolerance import calculate_tolerance_limits

    # Use non-parametric method
    phase2 = Phase2Results(
        cleaned_data=data,
        shapiro_p_value=0.01,  # Failed normality test
        transformation_method=TransformationMethod.NONE,
        analysis_method=AnalysisMethod.NON_PARAMETRIC,
        lambda_param=None,
        manual_override=False,
    )

    phase3 = Phase3Results(
        required_sample_size=len(data),
        k_margin=0.0,
        k_factor=0.0,
        specification_type=SpecificationType.TWO_SIDED,
    )
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=lsl, usl=usl
    )

    result = calculate_tolerance_limits(data, phase2, phase3, spec_limits)

    # Ppk should be None for non-parametric methods
    assert result.ppk is None, "Ppk should be None for non-parametric methods"


@pytest.mark.property
def test_property_17_parametric_sample_size_iteration():
    """Property 17: Parametric Sample Size Iteration."""
    from sample_size_calculator.models import AnalysisMethod, SpecificationType
    from sample_size_calculator.tolerance import calculate_required_sample_size

    result = calculate_required_sample_size(
        k_margin=5.0,
        confidence=95.0,
        reliability=95.0,
        spec_type=SpecificationType.ONE_SIDED,
        analysis_method=AnalysisMethod.PARAMETRIC,
    )

    assert result.required_sample_size >= 3
    assert result.k_margin == 5.0
    assert result.k_factor > 0


@pytest.mark.property
def test_property_17_parametric_two_sided_sample_size():
    """Property 17: Parametric Two-Sided Sample Size."""
    from sample_size_calculator.models import AnalysisMethod, SpecificationType
    from sample_size_calculator.tolerance import calculate_required_sample_size

    result = calculate_required_sample_size(
        k_margin=5.0,
        confidence=95.0,
        reliability=95.0,
        spec_type=SpecificationType.TWO_SIDED,
        analysis_method=AnalysisMethod.PARAMETRIC,
    )

    assert result.required_sample_size >= 3
    assert result.k_factor > 0


@pytest.mark.property
def test_property_17_non_parametric_one_sided_sample_size():
    """Property 17: Non-Parametric One-Sided Sample Size."""
    from sample_size_calculator.models import AnalysisMethod, SpecificationType
    from sample_size_calculator.tolerance import calculate_required_sample_size

    result = calculate_required_sample_size(
        k_margin=5.0,
        confidence=95.0,
        reliability=95.0,
        spec_type=SpecificationType.ONE_SIDED,
        analysis_method=AnalysisMethod.NON_PARAMETRIC,
    )

    assert result.required_sample_size > 0
    assert result.k_factor == 0.0


@pytest.mark.property
def test_property_17_non_parametric_two_sided_sample_size():
    """Property 17: Non-Parametric Two-Sided Sample Size."""
    from sample_size_calculator.models import AnalysisMethod, SpecificationType
    from sample_size_calculator.tolerance import calculate_required_sample_size

    result = calculate_required_sample_size(
        k_margin=5.0,
        confidence=95.0,
        reliability=95.0,
        spec_type=SpecificationType.TWO_SIDED,
        analysis_method=AnalysisMethod.NON_PARAMETRIC,
    )

    assert result.required_sample_size > 0
    assert result.k_factor == 0.0


@pytest.mark.property
def test_property_16_capability_margin_with_yeo_johnson_transformation():
    """Property 16: Capability Margin with Yeo-Johnson Transformation."""
    from sample_size_calculator.tolerance import calculate_capability_margin

    data = [10.0, 12.0, 11.0, 13.0, 12.5, 11.5, 12.2]
    lambda_param = 0.5
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=0.1, usl=200.0
    )

    def yeo_johnson_forward_single(x: float, lmbda: float) -> float:
        if x >= 0:
            if abs(lmbda) < 1e-10:
                return math.log(x + 1)
            else:
                return ((x + 1) ** lmbda - 1) / lmbda
        else:
            if abs(lmbda - 2) < 1e-10:
                return -math.log(-x + 1)
            else:
                return -((-x + 1) ** (2 - lmbda) - 1) / (2 - lmbda)

    transformed_data = [yeo_johnson_forward_single(x, lambda_param) for x in data]

    k_margin = calculate_capability_margin(
        transformed_data,
        spec_limits,
        TransformationMethod.YEO_JOHNSON,
        lambda_param,
    )

    assert k_margin > 0


@pytest.mark.property
@pytest.mark.property
def test_property_16_capability_margin_box_cox_lambda_zero():
    """Property 16: Box-Cox with lambda approximately zero."""
    from sample_size_calculator.tolerance import calculate_capability_margin

    data = [50.0, 60.0, 55.0, 65.0, 58.0]
    # When lambda ≈ 0, Box-Cox uses log transform, so data should be log-transformed
    transformed_data = [math.log(x) for x in data]
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=10.0, usl=200.0
    )

    k_margin = calculate_capability_margin(
        transformed_data, spec_limits, TransformationMethod.BOX_COX, 1e-12
    )
    assert k_margin > 0
@pytest.mark.property
def test_property_16_capability_margin_yeo_johnson_lambda_zero():
    """Property 16: Yeo-Johnson with lambda approximately zero."""
    from sample_size_calculator.tolerance import calculate_capability_margin

    # When lambda ≈ 0, Yeo-Johnson uses log(x+1)
    # So data should be pre-transformed using this formula
    # Original values around 1-2 will give transformed values around 0.7-1.1
    data = [0.7, 1.0, 0.9, 1.1, 0.85]
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=0.0, usl=20.0
    )

    k_margin = calculate_capability_margin(
        data, spec_limits, TransformationMethod.YEO_JOHNSON, 1e-12
    )
    assert k_margin > 0
@pytest.mark.property
def test_property_16_capability_margin_yeo_johnson_lambda_two():
    """Property 16: Yeo-Johnson with lambda approximately 2."""
    from sample_size_calculator.tolerance import calculate_capability_margin

    # For lambda ~ 2, negative values are transformed as -(-x+1)^(2-lambda)/(2-lambda)
    # When lambda=2, this becomes -log(-x+1), so we need x < 0 and -x+1 > 0
    data = [-0.5, -0.3, -0.2]
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=-5.0, usl=5.0
    )

    k_margin = calculate_capability_margin(
        data, spec_limits, TransformationMethod.YEO_JOHNSON, 2 - 1e-12
    )
    assert k_margin > 0
@pytest.mark.property
def test_property_16_capability_margin_negative_values_log():
    """Property 16: Log transformation with non-positive values."""
    from sample_size_calculator.tolerance import calculate_capability_margin

    # Data is already in transformed (log) space, but LSL must be positive
    data_with_zero = [2.0, 4.0, 3.5]
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=-5.0, usl=200.0
    )

    with pytest.raises(ValueError, match="must be positive"):
        calculate_capability_margin(
            data_with_zero, spec_limits, TransformationMethod.LOGARITHMIC, None
        )
@pytest.mark.property
def test_property_16_capability_margin_negative_values_box_cox():
    """Property 16: Box-Cox with non-positive values."""
    from sample_size_calculator.tolerance import calculate_capability_margin

    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=-5.0, usl=200.0
    )

    with pytest.raises(ValueError, match="must be positive"):
        calculate_capability_margin(
            [1.0, 2.0, 3.0], spec_limits, TransformationMethod.BOX_COX, 1.0
        )
@pytest.mark.property
def test_property_16_capability_margin_missing_lambda_box_cox():
    """Property 16: Box-Cox without lambda parameter."""
    from sample_size_calculator.tolerance import calculate_capability_margin

    data = [50.0, 60.0, 55.0]
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=10.0, usl=200.0
    )

    with pytest.raises(ValueError, match="Lambda parameter required"):
        calculate_capability_margin(
            data, spec_limits, TransformationMethod.BOX_COX, None
        )
@pytest.mark.property
def test_property_16_capability_margin_missing_lambda_yeo_johnson():
    """Property 16: Yeo-Johnson without lambda parameter."""
    from sample_size_calculator.tolerance import calculate_capability_margin

    # Use log-transformed data (since Yeo-Johnson with lambda=0 is similar to log)
    data = [3.9, 4.1, 4.0]
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=1.0, usl=6.0
    )

    with pytest.raises(ValueError, match="Lambda parameter required"):
        calculate_capability_margin(
            data, spec_limits, TransformationMethod.YEO_JOHNSON, None
        )
@pytest.mark.property
def test_property_17_invalid_k_margin():
    """Property 17: Invalid k_margin validation."""
    from sample_size_calculator.models import AnalysisMethod, SpecificationType
    from sample_size_calculator.tolerance import calculate_required_sample_size

    with pytest.raises(ValueError, match="k_margin must be positive"):
        calculate_required_sample_size(
            k_margin=-1.0,
            confidence=95.0,
            reliability=95.0,
            spec_type=SpecificationType.ONE_SIDED,
            analysis_method=AnalysisMethod.PARAMETRIC,
        )


@pytest.mark.property
def test_property_17_invalid_confidence():
    """Property 17: Invalid confidence validation."""
    from sample_size_calculator.models import AnalysisMethod, SpecificationType
    from sample_size_calculator.tolerance import calculate_required_sample_size

    with pytest.raises(ValueError, match="Confidence must be between 0 and 100"):
        calculate_required_sample_size(
            k_margin=3.0,
            confidence=-5.0,
            reliability=95.0,
            spec_type=SpecificationType.ONE_SIDED,
            analysis_method=AnalysisMethod.PARAMETRIC,
        )


@pytest.mark.property
def test_property_17_invalid_reliability():
    """Property 17: Invalid reliability validation."""
    from sample_size_calculator.models import AnalysisMethod, SpecificationType
    from sample_size_calculator.tolerance import calculate_required_sample_size

    with pytest.raises(ValueError, match="Reliability must be between 0 and 100"):
        calculate_required_sample_size(
            k_margin=3.0,
            confidence=95.0,
            reliability=150.0,
            spec_type=SpecificationType.ONE_SIDED,
            analysis_method=AnalysisMethod.PARAMETRIC,
        )


@pytest.mark.property
def test_property_27_yeo_johnson_tolerance_limits():
    """Property 27: Yeo-Johnson Transformation in Tolerance Limits."""
    from sample_size_calculator.transformations import box_cox_transform

    from sample_size_calculator.tolerance import calculate_tolerance_limits

    data = [10.0, 12.0, 11.0, 13.0, 12.5, 11.5, 12.2, 11.8]
    result = box_cox_transform(data)
    if result is None:
        pytest.skip("Box-Cox transformation failed")
    transformed_data, lambda_param = result
    if lambda_param is None or abs(lambda_param) < 1e-10:
        pytest.skip("Lambda parameter too close to zero")

    phase2 = Phase2Results(
        cleaned_data=transformed_data,
        shapiro_p_value=0.8,
        transformation_method=TransformationMethod.YEO_JOHNSON,
        analysis_method=AnalysisMethod.PARAMETRIC,
        lambda_param=lambda_param,
        manual_override=False,
    )

    k_factor = 2.5
    phase3 = Phase3Results(
        required_sample_size=len(transformed_data),
        k_margin=3.0,
        k_factor=k_factor,
        specification_type=SpecificationType.TWO_SIDED,
    )

    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=0.1, usl=200.0
    )

    result = calculate_tolerance_limits(data, phase2, phase3, spec_limits)

    assert "lower" in result.tolerance_limits
    assert "upper" in result.tolerance_limits


@pytest.mark.property
def test_property_26_ppk_no_lsl():
    """Property 26: Ppk with only USL."""
    from sample_size_calculator.tolerance import calculate_ppk

    data = [10.0, 12.0, 11.0, 13.0, 12.5]
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.ONE_SIDED, lsl=None, usl=100.0
    )

    ppk = calculate_ppk(data, spec_limits)

    mean = np.mean(data)
    std = np.std(data, ddof=1)
    expected_ppk = (spec_limits.usl - mean) / (3 * std)

    assert math.isclose(ppk, expected_ppk, rel_tol=1e-9)


@pytest.mark.property
def test_property_26_ppk_no_usl():
    """Property 26: Ppk with only LSL."""
    from sample_size_calculator.tolerance import calculate_ppk

    data = [10.0, 12.0, 11.0, 13.0, 12.5]
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.ONE_SIDED, lsl=0.5, usl=None
    )

    ppk = calculate_ppk(data, spec_limits)

    mean = np.mean(data)
    std = np.std(data, ddof=1)
    expected_ppk = (mean - spec_limits.lsl) / (3 * std)

    assert math.isclose(ppk, expected_ppk, rel_tol=1e-9)



@pytest.mark.property
def test_property_20_final_dataset_too_small():
    """Property 20: Final dataset smaller than required."""
    from sample_size_calculator.tolerance import calculate_tolerance_limits

    final_data = [10.0] * 5
    phase2 = Phase2Results(
        cleaned_data=final_data,
        shapiro_p_value=0.8,
        transformation_method=TransformationMethod.NONE,
        analysis_method=AnalysisMethod.PARAMETRIC,
        lambda_param=None,
        manual_override=False,
    )
    phase3 = Phase3Results(
        required_sample_size=15,
        k_margin=3.0,
        k_factor=2.5,
        specification_type=SpecificationType.TWO_SIDED,
    )
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=0.1, usl=200.0
    )

    with pytest.raises(ValueError, match="must contain at least"):
        calculate_tolerance_limits(final_data, phase2, phase3, spec_limits)


@pytest.mark.property
def test_property_16_capability_margin_box_cox_negative_lsl():
    """Property 16: Box-Cox with negative LSL."""
    from sample_size_calculator.tolerance import calculate_capability_margin

    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=-5.0, usl=200.0
    )

    # This should raise because Box-Cox requires positive values for spec limits
    with pytest.raises(ValueError, match="must be positive"):
        calculate_capability_margin(
            [1.0, 2.0, 3.0], spec_limits, TransformationMethod.BOX_COX, 1.0
        )


@pytest.mark.property
def test_property_16_capability_margin_box_cox_negative_usl():
    """Property 16: Box-Cox with negative USL."""
    from sample_size_calculator.tolerance import calculate_capability_margin

    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=0.1, usl=-5.0
    )

    # This should raise because Box-Cox requires positive values for spec limits
    with pytest.raises(ValueError, match="must be positive"):
        calculate_capability_margin(
            [1.0, 2.0, 3.0], spec_limits, TransformationMethod.BOX_COX, 1.0
        )


@pytest.mark.property
def test_property_16_capability_margin_yeo_johnson_negative_x_lambda_not_two():
    """Property 16: Yeo-Johnson with negative x and lambda != 2."""
    from sample_size_calculator.tolerance import calculate_capability_margin

    # Data with negative values, lambda = 0.5 (not close to 2)
    data = [-0.5, -0.3, -0.2]
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=-5.0, usl=5.0
    )

    # For x < 0 and lambda != 2: y = -((-x + 1)^(2-lambda) - 1) / (2 - lambda)
    # When lambda = 0.5: y = -((-x + 1)^1.5 - 1) / 1.5
    k_margin = calculate_capability_margin(
        data, spec_limits, TransformationMethod.YEO_JOHNSON, 0.5
    )
    assert k_margin > 0


@pytest.mark.property
def test_property_27_parametric_tolerance_limit_one_sided_lsl():
    """Property 27: Parametric tolerance limit for one-sided LSL."""
    from sample_size_calculator.tolerance import calculate_tolerance_limits

    data = [10.0, 12.0, 11.0, 13.0, 12.5]
    phase2 = Phase2Results(
        cleaned_data=data,
        shapiro_p_value=0.8,
        transformation_method=TransformationMethod.NONE,
        analysis_method=AnalysisMethod.PARAMETRIC,
        lambda_param=None,
        manual_override=False,
    )

    k_factor = 2.0
    phase3 = Phase3Results(
        k_factor=k_factor,
        required_sample_size=len(data),
        k_margin=3.0,
        specification_type=SpecificationType.ONE_SIDED,
    )

    # One-sided LSL only
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.ONE_SIDED, lsl=5.0, usl=None
    )

    result = calculate_tolerance_limits(data, phase2, phase3, spec_limits)

    assert "lower" in result.tolerance_limits
    # Only lower limit should be present
    assert len(result.tolerance_limits) == 1


@pytest.mark.property
def test_property_27_parametric_tolerance_limit_one_sided_usl():
    """Property 27: Parametric tolerance limit for one-sided USL."""
    from sample_size_calculator.tolerance import calculate_tolerance_limits

    data = [10.0, 12.0, 11.0, 13.0, 12.5]
    phase2 = Phase2Results(
        cleaned_data=data,
        shapiro_p_value=0.8,
        transformation_method=TransformationMethod.NONE,
        analysis_method=AnalysisMethod.PARAMETRIC,
        lambda_param=None,
        manual_override=False,
    )

    k_factor = 2.0
    phase3 = Phase3Results(
        required_sample_size=len(data),
        k_margin=3.0,
        k_factor=k_factor,
        specification_type=SpecificationType.ONE_SIDED,
    )

    # One-sided USL only
    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.ONE_SIDED, lsl=None, usl=20.0
    )

    result = calculate_tolerance_limits(data, phase2, phase3, spec_limits)

    assert "upper" in result.tolerance_limits
    # Only upper limit should be present
    assert len(result.tolerance_limits) == 1


@pytest.mark.property
def test_property_27_box_cox_back_transform():
    """Property 27: Box-Cox back-transform with lambda != 0."""
    from sample_size_calculator.transformations import box_cox_transform

    from sample_size_calculator.tolerance import calculate_tolerance_limits

    data = [50.0, 60.0, 55.0, 65.0, 58.0]
    result = box_cox_transform(data)
    if result is None:
        pytest.skip("Box-Cox transformation failed")
    transformed_data, lambda_param = result
    if lambda_param is None or abs(lambda_param) < 1e-10:
        pytest.skip("Lambda parameter too close to zero")

    phase2 = Phase2Results(
        cleaned_data=transformed_data,
        shapiro_p_value=0.8,
        transformation_method=TransformationMethod.BOX_COX,
        analysis_method=AnalysisMethod.PARAMETRIC,
        lambda_param=lambda_param,
        manual_override=False,
    )

    k_factor = 2.0
    phase3 = Phase3Results(
        required_sample_size=len(transformed_data),
        k_margin=5.0,
        k_factor=k_factor,
        specification_type=SpecificationType.TWO_SIDED,
    )

    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=10.0, usl=200.0
    )

    result = calculate_tolerance_limits(data, phase2, phase3, spec_limits)

    assert "lower" in result.tolerance_limits
    assert "upper" in result.tolerance_limits
    # Back-transformed values should be positive
    assert result.tolerance_limits["lower"] > 0
    assert result.tolerance_limits["upper"] > 0


@pytest.mark.property
def test_property_27_yeo_johnson_back_transform():
    """Property 27: Yeo-Johnson back-transform."""
    from sample_size_calculator.transformations import box_cox_transform

    from sample_size_calculator.tolerance import calculate_tolerance_limits

    # Data with both positive and negative values for Yeo-Johnson
    data = [-1.0, -0.5, 0.0, 0.5, 1.0]
    result = box_cox_transform(data)
    if result is None:
        pytest.skip("Box-Cox transformation failed")
    transformed_data, lambda_param = result
    # Use Yeo-Johnson with the lambda we got
    lambda_param = 0.5

    phase2 = Phase2Results(
        cleaned_data=transformed_data,
        shapiro_p_value=0.8,
        transformation_method=TransformationMethod.YEO_JOHNSON,
        analysis_method=AnalysisMethod.PARAMETRIC,
        lambda_param=lambda_param,
        manual_override=False,
    )

    k_factor = 2.0
    phase3 = Phase3Results(
        required_sample_size=len(transformed_data),
        k_margin=5.0,
        k_factor=k_factor,
        specification_type=SpecificationType.TWO_SIDED,
    )

    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=-5.0, usl=5.0
    )

    result = calculate_tolerance_limits(data, phase2, phase3, spec_limits)

    assert "lower" in result.tolerance_limits
    assert "upper" in result.tolerance_limits


@pytest.mark.property
def test_property_25_pass_fail_with_tolerance_exceeding_spec():
    """Property 25: Pass/Fail when tolerance exceeds specification."""
    from sample_size_calculator.tolerance import calculate_tolerance_limits

    # Create data that will produce tolerance limits outside spec
    data = [10.0, 10.5, 10.2, 10.8, 10.3]
    phase2 = Phase2Results(
        cleaned_data=data,
        shapiro_p_value=0.8,
        transformation_method=TransformationMethod.NONE,
        analysis_method=AnalysisMethod.PARAMETRIC,
        lambda_param=None,
        manual_override=False,
    )

    k_factor = 10.0  # Very large k to push limits outside spec
    phase3 = Phase3Results(
        required_sample_size=len(data),
        k_margin=20.0,
        k_factor=k_factor,
        specification_type=SpecificationType.TWO_SIDED,
    )

    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=15.0, usl=20.0
    )

    result = calculate_tolerance_limits(data, phase2, phase3, spec_limits)

    # Tolerance limits should exceed specification limits
    assert result.pass_fail == "Fail"


@pytest.mark.property
def test_property_25_pass_fail_with_strict_spec():
    """Property 25: Pass/Fail with strict specifications."""
    from sample_size_calculator.tolerance import calculate_tolerance_limits

    data = [10.0, 12.0, 11.0, 13.0, 12.5]
    phase2 = Phase2Results(
        cleaned_data=data,
        shapiro_p_value=0.8,
        transformation_method=TransformationMethod.NONE,
        analysis_method=AnalysisMethod.PARAMETRIC,
        lambda_param=None,
        manual_override=False,
    )

    k_factor = 1.5
    phase3 = Phase3Results(
        required_sample_size=len(data),
        k_margin=5.0,
        k_factor=k_factor,
        specification_type=SpecificationType.TWO_SIDED,
    )

    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=5.0, usl=20.0
    )

    result = calculate_tolerance_limits(data, phase2, phase3, spec_limits)

    # Tolerance limits should be within specification limits
    assert result.pass_fail == "Pass"


@pytest.mark.property
def test_property_16_capability_margin_log_negative_lsl():
    """Property 16: Log transformation with negative LSL."""
    from sample_size_calculator.tolerance import calculate_capability_margin

    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=-5.0, usl=200.0
    )

    # This should raise because log requires positive values for spec limits
    with pytest.raises(ValueError, match="must be positive"):
        calculate_capability_margin(
            [1.0, 2.0, 3.0], spec_limits, TransformationMethod.LOGARITHMIC, None
        )


@pytest.mark.property
def test_property_27_box_cox_missing_lambda_in_back_transform():
    """Property 27: Box-Cox back-transform without lambda parameter."""
    from sample_size_calculator.transformations import box_cox_transform

    from sample_size_calculator.tolerance import calculate_tolerance_limits

    data = [50.0, 60.0, 55.0]
    result = box_cox_transform(data)
    if result is None:
        pytest.skip("Box-Cox transformation failed")
    transformed_data, lambda_param = result
    if lambda_param is None or abs(lambda_param) < 1e-10:
        pytest.skip("Lambda parameter too close to zero")

    phase2 = Phase2Results(
        cleaned_data=transformed_data,
        shapiro_p_value=0.8,
        transformation_method=TransformationMethod.BOX_COX,
        analysis_method=AnalysisMethod.PARAMETRIC,
        lambda_param=None,  # This should cause an error
        manual_override=False,
    )

    k_factor = 2.0
    phase3 = Phase3Results(
        required_sample_size=len(transformed_data),
        k_margin=5.0,
        k_factor=k_factor,
        specification_type=SpecificationType.TWO_SIDED,
    )

    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=10.0, usl=200.0
    )

    with pytest.raises(ValueError, match="Lambda parameter required"):
        calculate_tolerance_limits(data, phase2, phase3, spec_limits)


@pytest.mark.property
def test_property_27_yeo_johnson_missing_lambda_in_back_transform():
    """Property 27: Yeo-Johnson back-transform without lambda parameter."""
    from sample_size_calculator.transformations import box_cox_transform

    from sample_size_calculator.tolerance import calculate_tolerance_limits

    data = [-1.0, -0.5, 0.0]
    result = box_cox_transform(data)
    if result is None:
        pytest.skip("Box-Cox transformation failed")
    transformed_data, lambda_param = result
    # Force using Yeo-Johnson with the lambda we got
    lambda_param = lambda_param or 0.5

    phase2 = Phase2Results(
        cleaned_data=transformed_data,
        shapiro_p_value=0.8,
        transformation_method=TransformationMethod.YEO_JOHNSON,
        analysis_method=AnalysisMethod.PARAMETRIC,
        lambda_param=None,  # This should cause an error
        manual_override=False,
    )

    k_factor = 2.0
    phase3 = Phase3Results(
        required_sample_size=len(transformed_data),
        k_margin=5.0,
        k_factor=k_factor,
        specification_type=SpecificationType.TWO_SIDED,
    )

    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=-5.0, usl=5.0
    )

    with pytest.raises(ValueError, match="Lambda parameter required"):
        calculate_tolerance_limits(data, phase2, phase3, spec_limits)


@pytest.mark.property
def test_property_17_parametric_iteration_limit():
    """Property 17: Test parametric iteration limit behavior.

    Note: This test verifies that the function can handle cases where
    k_margin is very small relative to confidence/reliability requirements.
    However, with max_iterations=10000 in calculate_required_sample_size,
    convergence should occur for reasonable inputs.
    """
    from sample_size_calculator.models import AnalysisMethod, SpecificationType
    from sample_size_calculator.tolerance import calculate_required_sample_size

    # Use a k_margin that's achievable
    result = calculate_required_sample_size(
        k_margin=3.0,
        confidence=95.0,
        reliability=95.0,
        spec_type=SpecificationType.ONE_SIDED,
        analysis_method=AnalysisMethod.PARAMETRIC,
    )

    assert result.required_sample_size > 0
    assert result.k_factor <= result.k_margin


@pytest.mark.property
def test_property_27_tolerance_limit_pass_fail_comparison():
    """Property 27: Verify tolerance limits are within spec for Pass."""
    from sample_size_calculator.tolerance import calculate_tolerance_limits

    data = [10.0, 12.0, 11.0, 13.0, 12.5]
    phase2 = Phase2Results(
        cleaned_data=data,
        shapiro_p_value=0.8,
        transformation_method=TransformationMethod.NONE,
        analysis_method=AnalysisMethod.PARAMETRIC,
        lambda_param=None,
        manual_override=False,
    )

    # Small k_factor to ensure limits are close to mean
    k_factor = 1.5
    phase3 = Phase3Results(
        required_sample_size=len(data),
        k_margin=5.0,
        k_factor=k_factor,
        specification_type=SpecificationType.TWO_SIDED,
    )

    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=5.0, usl=20.0
    )

    result = calculate_tolerance_limits(data, phase2, phase3, spec_limits)

    # Calculate expected tolerance limits
    import numpy as np
    mean = np.mean(data)
    std = np.std(data, ddof=1)
    expected_lower = mean - k_factor * std
    expected_upper = mean + k_factor * std

    assert result.tolerance_limits["lower"] == expected_lower
    assert result.tolerance_limits["upper"] == expected_upper

    # Verify pass: tolerance limits within spec
    assert result.pass_fail == "Pass"
    assert result.tolerance_limits["lower"] >= spec_limits.lsl
    assert result.tolerance_limits["upper"] <= spec_limits.usl


@pytest.mark.property
def test_property_27_tolerance_limit_pass_fail_fail():
    """Property 27: Verify tolerance limits exceed spec for Fail."""
    from sample_size_calculator.tolerance import calculate_tolerance_limits

    data = [10.0, 12.0, 11.0, 13.0, 12.5]
    phase2 = Phase2Results(
        cleaned_data=data,
        shapiro_p_value=0.8,
        transformation_method=TransformationMethod.NONE,
        analysis_method=AnalysisMethod.PARAMETRIC,
        lambda_param=None,
        manual_override=False,
    )

    # Large k_factor to push limits outside spec
    k_factor = 10.0
    phase3 = Phase3Results(
        required_sample_size=len(data),
        k_margin=10.0,
        k_factor=k_factor,
        specification_type=SpecificationType.TWO_SIDED,
    )

    spec_limits = SpecificationLimits(
        spec_type=SpecificationType.TWO_SIDED, lsl=5.0, usl=20.0
    )

    result = calculate_tolerance_limits(data, phase2, phase3, spec_limits)

    # Verify fail: tolerance limits exceed spec
    assert result.pass_fail == "Fail"
