"""Tolerance interval calculation and process capability analysis.

This module implements tolerance interval calculations for both parametric
and non-parametric methods, including capability margin calculation, sample
size iteration, and Pass/Fail determination with Ppk calculation.

References:
- ISO 16269-6:2014 Statistical interpretation of data
- NIST/SEMATECH e-Handbook of Statistical Methods
"""

import math

import numpy as np

from sample_size_calculator.calculations import CalculationEngine
from sample_size_calculator.models import (
    AnalysisMethod,
    Phase2Results,
    Phase3Results,
    Phase4Results,
    SpecificationLimits,
    SpecificationType,
    TransformationMethod,
)
from sample_size_calculator.transformations import (
    inverse_yeo_johnson_transform,
)


def calculate_capability_margin(
    data: list[float],
    spec_limits: SpecificationLimits,
    transformation_method: TransformationMethod,
    lambda_param: float | None = None,
) -> float:
    """Calculate capability margin (k_margin) from pilot data.

    The capability margin represents the process capability in terms of
    standard deviations. It is calculated by forward-transforming the
    specification limits, then computing the distance from the mean to
    each limit in units of standard deviation.

    Steps:
    1. Forward-transform specification limits based on transformation method
    2. Calculate distance from mean to each transformed specification limit
    3. Divide each distance by standard deviation
    4. Return minimum margin

    Args:
        data: Pilot dataset (already transformed if applicable)
        spec_limits: Specification limits in original units
        transformation_method: The transformation method being used
        lambda_param: Lambda parameter for Box-Cox or Yeo-Johnson (if applicable)

    Returns:
        k_margin: Minimum capability margin in standard deviations

    Raises:
        ValueError: If k_margin <= 0 (process is incapable)

    Examples:
        >>> from sample_size_calculator.models import (
        ...     SpecificationLimits,
        ...     SpecificationType,
        ...     TransformationMethod,
        ... )
        >>> # Two-sided specification with no transformation
        >>> data = [10.0, 12.0, 11.0, 13.0, 12.5]
        >>> spec_limits = SpecificationLimits(
        ...     spec_type=SpecificationType.TWO_SIDED, lsl=5.0, usl=20.0
        ... )
        >>> k_margin = calculate_capability_margin(
        ...     data, spec_limits, TransformationMethod.NONE
        ... )
        >>> k_margin > 0
        True

    Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.5
    """
    # Calculate mean and standard deviation of transformed data
    mean = np.mean(data)
    std = np.std(data, ddof=1)

    # Forward-transform specification limits based on transformation method
    lsl_t = None
    usl_t = None

    if transformation_method == TransformationMethod.LOGARITHMIC:
        # Log transformation: y = ln(x)
        if spec_limits.lsl is not None:
            if spec_limits.lsl <= 0:
                raise ValueError("LSL must be positive for logarithmic transformation")
            lsl_t = math.log(spec_limits.lsl)
        if spec_limits.usl is not None:
            if spec_limits.usl <= 0:
                raise ValueError("USL must be positive for logarithmic transformation")
            usl_t = math.log(spec_limits.usl)

    elif transformation_method == TransformationMethod.BOX_COX:
        # Box-Cox transformation: y = (x^λ - 1) / λ (for λ ≠ 0)
        if lambda_param is None:
            raise ValueError("Lambda parameter required for Box-Cox transformation")

        if spec_limits.lsl is not None:
            if spec_limits.lsl <= 0:
                raise ValueError("LSL must be positive for Box-Cox transformation")
            if abs(lambda_param) < 1e-10:  # lambda ≈ 0
                lsl_t = math.log(spec_limits.lsl)
            else:
                lsl_t = (spec_limits.lsl**lambda_param - 1) / lambda_param

        if spec_limits.usl is not None:
            if spec_limits.usl <= 0:
                raise ValueError("USL must be positive for Box-Cox transformation")
            if abs(lambda_param) < 1e-10:  # lambda ≈ 0
                usl_t = math.log(spec_limits.usl)
            else:
                usl_t = (spec_limits.usl**lambda_param - 1) / lambda_param

    elif transformation_method == TransformationMethod.YEO_JOHNSON:
        # Yeo-Johnson transformation (works with all values)
        if lambda_param is None:
            raise ValueError("Lambda parameter required for Yeo-Johnson transformation")

        def yeo_johnson_forward_single(x: float, lmbda: float) -> float:
            """Apply Yeo-Johnson transformation to a single value."""
            if x >= 0:
                if abs(lmbda) < 1e-10:  # lambda ≈ 0
                    return math.log(x + 1)
                else:
                    return ((x + 1) ** lmbda - 1) / lmbda
            else:  # x < 0
                if abs(lmbda - 2) < 1e-10:  # lambda ≈ 2
                    return -math.log(-x + 1)
                else:
                    return -((-x + 1) ** (2 - lmbda) - 1) / (2 - lmbda)

        if spec_limits.lsl is not None:
            lsl_t = yeo_johnson_forward_single(spec_limits.lsl, lambda_param)
        if spec_limits.usl is not None:
            usl_t = yeo_johnson_forward_single(spec_limits.usl, lambda_param)

    else:  # TransformationMethod.NONE
        # No transformation - use original limits
        lsl_t = spec_limits.lsl
        usl_t = spec_limits.usl

    # Calculate capability margins
    margins = []

    if lsl_t is not None:
        # Lower margin: (mean - LSL) / std
        lower_margin = (mean - lsl_t) / std
        margins.append(lower_margin)

    if usl_t is not None:
        # Upper margin: (USL - mean) / std
        upper_margin = (usl_t - mean) / std
        margins.append(upper_margin)

    # k_margin is the minimum of the calculated margins
    k_margin = min(margins)

    # Check if process is capable
    if k_margin <= 0:
        raise ValueError(
            "Process is incapable: k_margin <= 0. "
            "Mean is outside specification limits or too close to limits."
        )

    return k_margin


def calculate_required_sample_size(
    k_margin: float,
    confidence: float,
    reliability: float,
    spec_type: SpecificationType,
    analysis_method: AnalysisMethod,
) -> Phase3Results:
    """Iteratively determine required sample size N.

    For parametric methods, iterates N upward until k_factor(N) <= k_margin.
    For non-parametric methods, uses direct formulas.

    Args:
        k_margin: Capability margin from pilot data
        confidence: Confidence level as percentage (0-100)
        reliability: Reliability level as percentage (0-100)
        spec_type: One-Sided or Two-Sided specification
        analysis_method: Parametric or Non-Parametric

    Returns:
        Phase3Results containing:
        - required_sample_size: Minimum N satisfying the constraint
        - k_margin: The capability margin used
        - k_factor: The tolerance factor at the required N (or 0 for non-parametric)
        - specification_type: The specification type used

    Raises:
        ValueError: If inputs are invalid or calculation does not converge

    Examples:
        >>> from sample_size_calculator.models import (
        ...     AnalysisMethod,
        ...     SpecificationType,
        ... )
        >>> # Parametric one-sided
        >>> result = calculate_required_sample_size(
        ...     k_margin=3.0,
        ...     confidence=95.0,
        ...     reliability=95.0,
        ...     spec_type=SpecificationType.ONE_SIDED,
        ...     analysis_method=AnalysisMethod.PARAMETRIC,
        ... )
        >>> result.required_sample_size > 0
        True

    Validates: Requirements 15.3, 15.4, 16.3, 16.4, 17.1, 17.2, 18.1, 18.2
    """
    if k_margin <= 0:
        raise ValueError("k_margin must be positive")
    if not (0 < confidence < 100):
        raise ValueError("Confidence must be between 0 and 100")
    if not (0 < reliability < 100):
        raise ValueError("Reliability must be between 0 and 100")

    if analysis_method == AnalysisMethod.NON_PARAMETRIC:
        # Non-parametric methods use direct formulas
        if spec_type == SpecificationType.ONE_SIDED:
            # Uses extreme order statistics (min or max)
            n = CalculationEngine.non_parametric_one_sided_sample_size(
                confidence, reliability
            )
            k_factor = 0.0  # Not applicable for non-parametric
        else:  # TWO_SIDED
            # Uses both min and max order statistics
            n = CalculationEngine.non_parametric_two_sided_sample_size(
                confidence, reliability
            )
            k_factor = 0.0  # Not applicable for non-parametric

        return Phase3Results(
            required_sample_size=n,
            k_margin=k_margin,
            k_factor=k_factor,
            specification_type=spec_type,
        )

    else:  # Parametric method
        # Iterate N upward until k_factor(N) <= k_margin
        n = 3  # Start with minimum sample size for parametric methods
        max_iterations = 10000  # Safety limit

        for _ in range(max_iterations):
            if spec_type == SpecificationType.ONE_SIDED:
                k_factor = CalculationEngine.one_sided_tolerance_factor(
                    n, confidence, reliability
                )
            else:  # TWO_SIDED
                k_factor = CalculationEngine.two_sided_tolerance_factor(
                    n, confidence, reliability
                )

            # Check if constraint is satisfied
            if k_factor <= k_margin:
                return Phase3Results(
                    required_sample_size=n,
                    k_margin=k_margin,
                    k_factor=k_factor,
                    specification_type=spec_type,
                )

            n += 1

        raise RuntimeError(
            "Sample size calculation did not converge within iteration limit"
        )


def calculate_tolerance_limits(
    final_data: list[float],
    phase2_results: Phase2Results,
    phase3_results: Phase3Results,
    spec_limits: SpecificationLimits,
) -> Phase4Results:
    """Calculate final tolerance limits and Pass/Fail determination.

    This function uses data from Phase 2 which has already undergone outlier
    exclusions. For parametric methods, it also uses the transformed version.
    It calculates tolerance limits using either parametric or non-parametric
    methods, back-transforms parametric limits to original space,
    and determines Pass/Fail by comparing to specification limits.

    Steps:
    1. Validate final dataset size is at least the required sample size
    2. Retrieve original_cleaned_data from Phase 2 (outlier-excluded but untransformed)
       or use cleaned_data if no transformation was applied
    3. Calculate tolerance limits:
       - Parametric: mean_t ± k*std_t (using transformed data), then back-transform
       - Non-parametric: min/max order statistics on original data
    4. Compare to specification limits for Pass/Fail
    5. Calculate Ppk using original cleaned data

    Args:
        final_data: Final validation dataset in original units (unused, kept for API compatibility)
        phase2_results: Results from Phase 2 (transformation method locked, includes cleaned_data and original_cleaned_data)

    Args:
        final_data: Final validation dataset in original units (unused, kept for API compatibility)
        phase2_results: Results from Phase 2 (transformation method locked, cleaned_data already transformed)
        phase3_results: Results from Phase 3 (required sample size and k_factor)
        spec_limits: Specification limits in original units

    Returns:
        Phase4Results containing:
        - final_data: The final dataset
        - tolerance_limits: Dict with "lower" and/or "upper" keys
        - pass_fail: "Pass" or "Fail"
        - ppk: Process capability index (or None for non-parametric)

    Raises:
        ValueError: If final dataset size is less than required sample size

    Examples:
        >>> from sample_size_calculator.models import (
        ...     AnalysisMethod,
        ...     Phase2Results,
        ...     Phase3Results,
        ...     SpecificationLimits,
        ...     SpecificationType,
        ...     TransformationMethod,
        ... )
        >>> # Parametric example with no transformation
        >>> final_data = [10.0, 12.0, 11.0, 13.0, 12.5, 11.5, 12.2, 11.8, 12.3, 11.9]
        >>> phase2 = Phase2Results(
        ...     cleaned_data=final_data,
    ...     original_cleaned_data=final_data,
        ...     shapiro_p_value=0.8,
        ...     transformation_method=TransformationMethod.NONE,
        ...     analysis_method=AnalysisMethod.PARAMETRIC,
        ...     lambda_param=None,
        ...     manual_override=False,
        ... )
        >>> phase3 = Phase3Results(
        ...     required_sample_size=10,
        ...     k_margin=3.0,
        ...     k_factor=2.5,
        ...     specification_type=SpecificationType.TWO_SIDED,
        ... )
        >>> spec_limits = SpecificationLimits(
        ...     spec_type=SpecificationType.TWO_SIDED, lsl=5.0, usl=20.0
        ... )
        >>> result = calculate_tolerance_limits(
        ...     final_data, phase2, phase3, spec_limits
        ... )
        >>> result.pass_fail in ["Pass", "Fail"]
        True

    Validates: Requirements 19.3, 20.1, 20.2, 20.3, 21.1, 21.2, 21.3
    """
    # Validate dataset size
    if len(final_data) < phase3_results.required_sample_size:
        raise ValueError(
            f"Final dataset must contain at least "
            f"{phase3_results.required_sample_size} data points. "
            f"Received {len(final_data)} data points."
        )

    # Use original_cleaned_data from Phase 2 if available (outlier-excluded but untransformed)
    # Otherwise use cleaned_data (which may be transformed) or final_data as fallback
    if phase2_results.original_cleaned_data is not None:
        original_data = phase2_results.original_cleaned_data
    else:
        original_data = phase2_results.cleaned_data if phase2_results.transformation_method == TransformationMethod.NONE else final_data

    # Use cleaned_data from Phase 2 which is already transformed and outlier-excluded
    transformed_data = phase2_results.cleaned_data

    # Calculate tolerance limits
    tolerance_limits = {}

    if phase2_results.analysis_method == AnalysisMethod.NON_PARAMETRIC:
        # Non-parametric: use extreme order statistics
        if phase3_results.specification_type == SpecificationType.ONE_SIDED:
            if spec_limits.lsl is not None:
                # Lower spec limit only - use minimum
                tolerance_limits["lower"] = min(original_data)
            else:
                # Upper spec limit only - use maximum
                tolerance_limits["upper"] = max(original_data)
        else:  # TWO_SIDED
            # Use both minimum and maximum
            tolerance_limits["lower"] = min(original_data)
            tolerance_limits["upper"] = max(original_data)

    else:  # Parametric method
        # Calculate mean and std of transformed data
        mean_t = np.mean(transformed_data)
        std_t = np.std(transformed_data, ddof=1)
        k = phase3_results.k_factor

        # Calculate tolerance limits in transformed space
        if phase3_results.specification_type == SpecificationType.ONE_SIDED:
            if spec_limits.lsl is not None:
                # Lower spec limit only
                limit_t = mean_t - k * std_t
                tolerance_limits["lower"] = limit_t
            else:
                # Upper spec limit only
                limit_t = mean_t + k * std_t
                tolerance_limits["upper"] = limit_t
        else:  # TWO_SIDED
            lower_t = mean_t - k * std_t
            upper_t = mean_t + k * std_t
            tolerance_limits["lower"] = lower_t
            tolerance_limits["upper"] = upper_t

        # Back-transform limits to original space
        if phase2_results.transformation_method == TransformationMethod.LOGARITHMIC:
            tolerance_limits = {
                key: math.exp(val) for key, val in tolerance_limits.items()
            }
        elif phase2_results.transformation_method == TransformationMethod.BOX_COX:
            if phase2_results.lambda_param is None:
                raise ValueError("Lambda parameter required for Box-Cox transformation")
            lmbda = phase2_results.lambda_param
            if abs(lmbda) < 1e-10:  # lambda ≈ 0
                tolerance_limits = {
                    key: math.exp(val) for key, val in tolerance_limits.items()
                }
            else:
                tolerance_limits = {
                    key: (lmbda * val + 1) ** (1 / lmbda)
                    for key, val in tolerance_limits.items()
                }
        elif phase2_results.transformation_method == TransformationMethod.YEO_JOHNSON:
            # Back-transform using inverse Yeo-Johnson
            if phase2_results.lambda_param is None:
                raise ValueError("Lambda parameter required for YJ transformation")
            back_transformed = {}
            for key, val in tolerance_limits.items():
                # Use the inverse transformation function
                back_transformed[key] = inverse_yeo_johnson_transform(
                    [val], phase2_results.lambda_param
                )[0]
            tolerance_limits = back_transformed

    # Pass/Fail determination
    pass_fail = "Pass"

    if "lower" in tolerance_limits and spec_limits.lsl is not None:
        if tolerance_limits["lower"] < spec_limits.lsl:
            pass_fail = "Fail"

    if "upper" in tolerance_limits and spec_limits.usl is not None:
        if tolerance_limits["upper"] > spec_limits.usl:
            pass_fail = "Fail"

    # Calculate Ppk (only for parametric methods)
    ppk = None
    if phase2_results.analysis_method == AnalysisMethod.PARAMETRIC:
        ppk = calculate_ppk(original_data, spec_limits)

    return Phase4Results(
        final_data=final_data,
        tolerance_limits=tolerance_limits,
        pass_fail=pass_fail,
        ppk=ppk,
    )


def calculate_ppk(data: list[float], spec_limits: SpecificationLimits) -> float:
    """Calculate process capability index Ppk.

    Ppk measures the process capability by comparing the process spread
    to the specification limits. It is calculated as the minimum of
    the upper and lower capability indices.

    Formula:
    - Ppu = (USL - mean) / (3 * std)
    - Ppl = (mean - LSL) / (3 * std)
    - Ppk = min(Ppu, Ppl)

    Args:
        data: Process data in original units
        spec_limits: Specification limits

    Returns:
        Ppk value (process capability index)

    Raises:
        ValueError: If specification limits are not defined

    Examples:
        >>> from sample_size_calculator.models import (
        ...     SpecificationLimits,
        ...     SpecificationType,
        ... )
        >>> data = [10.0, 12.0, 11.0, 13.0, 12.5]
        >>> spec_limits = SpecificationLimits(
        ...     spec_type=SpecificationType.TWO_SIDED, lsl=5.0, usl=20.0
        ... )
        >>> ppk = calculate_ppk(data, spec_limits)
        >>> ppk > 0
        True

    Validates: Requirement 23.4
    """
    mean = np.mean(data)
    std = np.std(data, ddof=1)

    indices = []

    if spec_limits.lsl is not None:
        # Lower capability index
        ppl = (mean - spec_limits.lsl) / (3 * std)
        indices.append(ppl)

    if spec_limits.usl is not None:
        # Upper capability index
        ppu = (spec_limits.usl - mean) / (3 * std)
        indices.append(ppu)

    if not indices:
        raise ValueError("At least one specification limit must be defined for Ppk")

    # Ppk is the minimum of the capability indices
    ppk = min(indices)

    return ppk
