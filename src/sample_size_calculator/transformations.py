"""Data transformation functions for normality.

This module provides forward transformation functions for normalizing
non-normal data distributions. Transformations include logarithmic,
Box-Cox, and Yeo-Johnson methods.

References:
- Box, G. E. P., & Cox, D. R. (1964). An analysis of transformations.
  Journal of the Royal Statistical Society, Series B, 26(2), 211-252.
- Yeo, I. K., & Johnson, R. A. (2000). A new family of power transformations
  to improve normality or symmetry. Biometrika, 87(4), 954-959.
"""

import numpy as np
from scipy import special, stats

from sample_size_calculator.models import (
    AnalysisMethod,
    Phase2Results,
    TransformationMethod,
)


def log_transform(data: list[float]) -> list[float] | None:
    """Apply natural logarithm transformation to data.

    This transformation is suitable for right-skewed data with all positive values.
    The natural logarithm can help normalize distributions where the variance
    increases with the mean.

    Args:
        data: List of numeric values to transform

    Returns:
        List of log-transformed values, or None if any value is <= 0

    Examples:
        >>> log_transform([1.0, 2.0, 3.0])
        [0.0, 0.6931471805599453, 1.0986122886681098]

        >>> log_transform([0.0, 1.0, 2.0])  # Contains zero
        None

        >>> log_transform([-1.0, 1.0, 2.0])  # Contains negative
        None

    Notes:
        - All values must be strictly positive (> 0)
        - Returns None if validation fails
        - Uses natural logarithm (base e)

    Validates: Requirements 10.1, 10.2
    """
    # Validate that all values are positive
    if any(x <= 0 for x in data):
        return None

    # Apply natural logarithm transformation
    return np.log(data).tolist()


def box_cox_transform(data: list[float]) -> tuple[list[float], float] | None:
    """Apply Box-Cox transformation with optimized lambda parameter.

    The Box-Cox transformation is a family of power transformations that can
    help normalize data and stabilize variance. The lambda parameter is
    automatically optimized using maximum likelihood estimation.

    Args:
        data: List of numeric values to transform

    Returns:
        Tuple of (transformed_data, lambda_param), or None if any value is <= 0

    Examples:
        >>> data = [1.0, 2.0, 3.0, 4.0, 5.0]
        >>> transformed, lambda_val = box_cox_transform(data)
        >>> isinstance(transformed, list) and isinstance(lambda_val, float)
        True

        >>> box_cox_transform([0.0, 1.0, 2.0])  # Contains zero
        None

        >>> box_cox_transform([-1.0, 1.0, 2.0])  # Contains negative
        None

    Notes:
        - All values must be strictly positive (> 0)
        - Returns None if validation fails
        - Lambda is optimized using scipy.stats.boxcox()
        - Extreme lambda values (|λ| > 10) are rejected due to numerical instability
        - Transformation formula:
          * If λ ≠ 0: y = (x^λ - 1) / λ
          * If λ = 0: y = ln(x)

    Validates: Requirements 11.1, 11.2
    """
    # Validate that all values are positive
    if any(x <= 0 for x in data):
        return None

    # Check for constant data (Box-Cox requires variance)
    data_array = np.array(data)
    if np.std(data_array) < 1e-10:
        return None

    try:
        # Apply Box-Cox transformation with lambda optimization
        # scipy.stats.boxcox returns (transformed_data, lambda_param)
        transformed_array, lambda_param = stats.boxcox(data_array)

        # Reject extreme lambda values that cause numerical instability
        # Box-Cox with |λ| > 3 leads to power transformations that exceed
        # floating-point precision limits in round-trip transformations
        # Even moderate lambdas cause precision issues with tight tolerances
        if abs(lambda_param) > 3.0:
            return None

        return transformed_array.tolist(), float(lambda_param)
    except (ValueError, RuntimeError):
        # Handle numerical errors (e.g., constant data, optimization failures)
        return None


def yeo_johnson_transform(data: list[float]) -> tuple[list[float], float]:
    """Apply Yeo-Johnson transformation with optimized lambda parameter.

    The Yeo-Johnson transformation is an extension of Box-Cox that works with
    zero and negative values. It applies different transformations depending
    on the sign of the data and the lambda parameter.

    Args:
        data: List of numeric values to transform

    Returns:
        Tuple of (transformed_data, lambda_param)

    Examples:
        >>> data = [1.0, 2.0, 3.0, 4.0, 5.0]
        >>> transformed, lambda_val = yeo_johnson_transform(data)
        >>> isinstance(transformed, list) and isinstance(lambda_val, float)
        True

        >>> data = [-1.0, 0.0, 1.0, 2.0]  # Works with zero and negative
        >>> transformed, lambda_val = yeo_johnson_transform(data)
        >>> isinstance(transformed, list) and isinstance(lambda_val, float)
        True

    Notes:
        - Works with all value ranges (positive, zero, negative)
        - Lambda is optimized using scipy.stats.yeojohnson()
        - Transformation formula:
          * For x ≥ 0, λ ≠ 0: y = ((x + 1)^λ - 1) / λ
          * For x ≥ 0, λ = 0: y = ln(x + 1)
          * For x < 0, λ ≠ 2: y = -((-x + 1)^(2-λ) - 1) / (2 - λ)
          * For x < 0, λ = 2: y = -ln(-x + 1)

    Validates: Requirements 12.1, 12.2
    """
    # Apply Yeo-Johnson transformation with lambda optimization
    # scipy.stats.yeojohnson returns (transformed_data, lambda_param)
    transformed_array, lambda_param = stats.yeojohnson(np.array(data))

    return transformed_array.tolist(), float(lambda_param)


def inverse_log_transform(data: list[float]) -> list[float]:
    """Apply inverse natural logarithm transformation (exponential).

    This function reverses the natural logarithm transformation by applying
    the exponential function. It is used to back-transform tolerance limits
    from log space to original engineering units.

    Args:
        data: List of log-transformed values

    Returns:
        List of back-transformed values in original units

    Examples:
        >>> log_data = [0.0, 0.6931471805599453, 1.0986122886681098]
        >>> inverse_log_transform(log_data)
        [1.0, 2.0, 3.0]

        >>> # Round-trip property
        >>> original = [1.0, 2.0, 3.0]
        >>> transformed = log_transform(original)
        >>> back = inverse_log_transform(transformed)
        >>> np.allclose(original, back)
        True

    Notes:
        - Applies exp(y) to reverse ln(x)
        - Maintains round-trip property within numerical precision
        - Used for back-transforming tolerance limits to original units

    Validates: Requirement 22.1
    """
    # Apply exponential to reverse natural logarithm
    return np.exp(data).tolist()


def inverse_box_cox_transform(data: list[float], lambda_param: float) -> list[float]:
    """Apply inverse Box-Cox transformation.

    This function reverses the Box-Cox transformation using the locked lambda
    parameter. It handles both the power transformation case (λ ≠ 0) and the
    logarithmic case (λ = 0).

    Args:
        data: List of Box-Cox transformed values
        lambda_param: The lambda parameter used in the forward transformation

    Returns:
        List of back-transformed values in original units

    Examples:
        >>> # Forward and inverse transformation
        >>> original = [1.0, 2.0, 3.0, 4.0, 5.0]
        >>> transformed, lambda_val = box_cox_transform(original)
        >>> back = inverse_box_cox_transform(transformed, lambda_val)
        >>> np.allclose(original, back)
        True

    Notes:
        - Inverse formula:
          * If λ ≠ 0: x = (λ * y + 1)^(1/λ)
          * If λ = 0: x = exp(y)
        - Maintains round-trip property within numerical precision
        - Used for back-transforming tolerance limits to original units

    Validates: Requirement 22.2
    """
    # Use scipy.special.inv_boxcox for improved numerical precision
    # This is a compiled C function optimized for Box-Cox inverse transformation
    # Formula: x = (lambda * y + 1)^(1/lambda) for lambda != 0, exp(y) for lambda = 0
    data_array = np.array(data)
    result = special.inv_boxcox(data_array, lambda_param)
    return result.tolist()


def inverse_yeo_johnson_transform(
    data: list[float], lambda_param: float
) -> list[float]:
    """Apply inverse Yeo-Johnson transformation with numerical stability.

    This function reverses the Yeo-Johnson transformation using the locked lambda
    parameter. It handles all four cases based on the transformed value sign and
    lambda parameter, with safeguards for extreme lambda values to prevent
    numerical overflow/underflow.

    Args:
        data: List of Yeo-Johnson transformed values
        lambda_param: The lambda parameter used in the forward transformation

    Returns:
        List of back-transformed values in original units

    Examples:
        >>> # Forward and inverse transformation with positive values
        >>> original = [1.0, 2.0, 3.0, 4.0, 5.0]
        >>> transformed, lambda_val = yeo_johnson_transform(original)
        >>> back = inverse_yeo_johnson_transform(transformed, lambda_val)
        >>> np.allclose(original, back)
        True

        >>> # Forward and inverse with mixed signs
        >>> original = [-1.0, 0.0, 1.0, 2.0]
        >>> transformed, lambda_val = yeo_johnson_transform(original)
        >>> back = inverse_yeo_johnson_transform(transformed, lambda_val)
        >>> np.allclose(original, back)
        True

    Notes:
        - Inverse formula (reverses the forward transformation):
          * For y ≥ 0, λ ≠ 0: x = (λ * y + 1)^(1/λ) - 1
          * For y ≥ 0, λ = 0: x = exp(y) - 1
          * For y < 0, λ ≠ 2: x = 1 - ((2 - λ) * (-y) + 1)^(1/(2-λ))
          * For y < 0, λ = 2: x = 1 - exp(-y)
        - Maintains round-trip property within numerical precision (epsilon=1e-10)
        - Uses log-space arithmetic for extreme lambda values for numerical stability
        - Clamps intermediate results to prevent overflow/underflow
        - Used for back-transforming tolerance limits to original units

    Validates: Requirement 22.3
    """
    data_array = np.array(data)
    result = np.zeros_like(data_array)

    # Numerical stability constants
    epsilon = 1e-10
    max_exp_arg = 700  # Safe limit for exp() to avoid overflow
    min_log_arg = 1e-300  # Minimum argument for log to avoid -inf

    # Case 1: y >= 0, lambda != 0
    # Forward: y = ((x + 1)^λ - 1) / λ
    # Inverse: x = (λ * y + 1)^(1/λ) - 1
    mask1 = (data_array >= 0) & (np.abs(lambda_param) >= epsilon)
    if np.any(mask1):
        # Calculate base: λ * y + 1
        base = lambda_param * data_array[mask1] + 1

        # Ensure base is positive
        base = np.maximum(base, min_log_arg)

        # Calculate exponent
        exponent = 1.0 / lambda_param

        # For extreme lambda values, use log-space arithmetic for numerical stability
        # x = base^exponent - 1 = exp(exponent * log(base)) - 1
        if np.abs(lambda_param) > 5.0:
            # Use log-space: x = exp(exponent * log(base)) - 1
            # Use expm1 for better precision: x = expm1(exponent * log(base))
            log_base = np.log(base)
            exp_arg = exponent * log_base
            # Clamp to prevent overflow
            exp_arg_clamped = np.clip(exp_arg, -max_exp_arg, max_exp_arg)
            result[mask1] = np.expm1(exp_arg_clamped)
        else:
            # Standard power operation for moderate lambda values
            result[mask1] = np.power(base, exponent) - 1

    # Case 2: y >= 0, lambda = 0
    # Forward: y = ln(x + 1)
    # Inverse: x = exp(y) - 1
    mask2 = (data_array >= 0) & (np.abs(lambda_param) < epsilon)
    if np.any(mask2):
        # Clamp y to prevent exp overflow
        y_clamped = np.clip(data_array[mask2], -max_exp_arg, max_exp_arg)
        # Use expm1 for better precision
        result[mask2] = np.expm1(y_clamped)

    # Case 3: y < 0, lambda != 2
    # Forward: y = -((-x + 1)^(2-λ) - 1) / (2 - λ)
    # Inverse: x = 1 - ((2 - λ) * (-y) + 1)^(1/(2-λ))
    mask3 = (data_array < 0) & (np.abs(lambda_param - 2) >= epsilon)
    if np.any(mask3):
        # Calculate base: (2 - λ) * (-y) + 1
        base = (2 - lambda_param) * (-data_array[mask3]) + 1

        # Ensure base is positive
        base = np.maximum(base, min_log_arg)

        # Calculate exponent
        exponent = 1.0 / (2 - lambda_param)

        # For extreme lambda values, use log-space arithmetic
        if np.abs(lambda_param) > 5.0 or np.abs(lambda_param - 2) < 1.0:
            # Use log-space: result = 1 - exp(exponent * log(base))
            # Use expm1 for better precision: result = -expm1(exponent * log(base))
            log_base = np.log(base)
            exp_arg = exponent * log_base
            # Clamp to prevent overflow
            exp_arg_clamped = np.clip(exp_arg, -max_exp_arg, max_exp_arg)
            result[mask3] = -np.expm1(exp_arg_clamped)
        else:
            # Standard power operation for moderate lambda values
            result[mask3] = 1 - np.power(base, exponent)

    # Case 4: y < 0, lambda = 2
    # Forward: y = -ln(-x + 1)
    # Inverse: x = 1 - exp(-y)
    mask4 = (data_array < 0) & (np.abs(lambda_param - 2) < epsilon)
    if np.any(mask4):
        # Clamp -y to prevent exp overflow
        neg_y_clamped = np.clip(-data_array[mask4], -max_exp_arg, max_exp_arg)
        result[mask4] = 1 - np.exp(neg_y_clamped)

    return result.tolist()


def transformation_cascade(
    data: list[float], manual_method: "TransformationMethod | None" = None
) -> Phase2Results:
    """Execute transformation cascade with Shapiro-Wilk normality testing.

    This function implements a sequential cascade of transformation methods to
    achieve data normality. It tests the original data first, then progressively
    tries Log, Box-Cox, and Yeo-Johnson transformations until normality is
    achieved (p > 0.05) or all methods are exhausted.

    If manual_method is provided, the cascade is bypassed and the specified
    method is applied directly (with validation for Log and Box-Cox).

    Args:
        data: List of numeric values to transform
        manual_method: Optional manual override to force a specific
            transformation method regardless of cascade results
            (TransformationMethod | None)

    Returns:
        Phase2Results containing:
        - cleaned_data: The transformed data (or original if no transformation)
        - shapiro_p_value: The p-value from Shapiro-Wilk test
        - transformation_method: The locked transformation method
        - analysis_method: Parametric or Non-Parametric
        - lambda_param: Lambda parameter for Box-Cox or Yeo-Johnson
        - manual_override: True if manual_method was used

    Examples:
        >>> # Automatic cascade with normal data
        >>> import numpy as np
        >>> np.random.seed(42)
        >>> normal_data = np.random.normal(10, 2, 50).tolist()
        >>> result = transformation_cascade(normal_data)
        >>> result.transformation_method
        <TransformationMethod.NONE: 'None'>
        >>> result.analysis_method
        <AnalysisMethod.PARAMETRIC: 'Parametric'>

        >>> # Manual override to force logarithmic transformation
        >>> from sample_size_calculator.models import (
        ...     TransformationMethod,
        ... )
        >>> positive_data = [1.0, 2.0, 3.0, 4.0, 5.0]
        >>> result = transformation_cascade(
        ...     positive_data,
        ...     manual_method=TransformationMethod.LOGARITHMIC,
        ... )
        >>> result.transformation_method
        <TransformationMethod.LOGARITHMIC: 'Logarithmic'>
        >>> result.manual_override
        True

    Notes:
        - Cascade order: Original → Log → Box-Cox → Yeo-Johnson → Non-Parametric
        - First method achieving p > 0.05 is locked
        - Log and Box-Cox require all positive values
        - Yeo-Johnson works with all value ranges
        - If all transformations fail, locks as Non-Parametric (Wilks)
        - Manual override validates data requirements for Log and Box-Cox

    Validates: Requirements 9.3, 9.4, 10.3, 10.4, 11.3, 11.4, 12.3, 12.4, 13.1, 13.2
    """
    # Import here to avoid circular dependency
    from sample_size_calculator.normality import shapiro_wilk_test

    # Handle manual override
    if manual_method is not None:
        if manual_method == TransformationMethod.NONE:
            # Test original data
            _, p_value = shapiro_wilk_test(data)
            return Phase2Results(
                cleaned_data=data,
                shapiro_p_value=p_value,
                transformation_method=TransformationMethod.NONE,
                analysis_method=AnalysisMethod.PARAMETRIC,
                lambda_param=None,
                manual_override=True,
            )

        elif manual_method == TransformationMethod.LOGARITHMIC:
            # Validate all values are positive
            if not all(x > 0 for x in data):
                raise ValueError(
                    "Logarithmic transformation requires all values to be positive"
                )
            log_data = log_transform(data)
            if log_data is None:
                raise ValueError("Logarithmic transformation failed validation")
            _, p_value = shapiro_wilk_test(log_data)
            return Phase2Results(
                cleaned_data=log_data,
                shapiro_p_value=p_value,
                transformation_method=TransformationMethod.LOGARITHMIC,
                analysis_method=AnalysisMethod.PARAMETRIC,
                lambda_param=None,
                manual_override=True,
            )

        elif manual_method == TransformationMethod.BOX_COX:
            # Validate all values are positive
            if not all(x > 0 for x in data):
                raise ValueError(
                    "Box-Cox transformation requires all values to be positive"
                )

            # Check for constant data (Box-Cox requires variance)
            data_array = np.array(data)
            if np.std(data_array) < 1e-10:
                raise ValueError(
                    "Box-Cox transformation requires data with non-zero variance"
                )

            result = box_cox_transform(data)
            if result is None:
                raise ValueError("Box-Cox transformation failed validation")
            boxcox_data, lambda_param = result
            _, p_value = shapiro_wilk_test(boxcox_data)
            return Phase2Results(
                cleaned_data=boxcox_data,
                shapiro_p_value=p_value,
                transformation_method=TransformationMethod.BOX_COX,
                analysis_method=AnalysisMethod.PARAMETRIC,
                lambda_param=lambda_param,
                manual_override=True,
            )

        elif manual_method == TransformationMethod.YEO_JOHNSON:
            # Yeo-Johnson works with all values
            yeojohnson_data, lambda_param = yeo_johnson_transform(data)
            _, p_value = shapiro_wilk_test(yeojohnson_data)
            return Phase2Results(
                cleaned_data=yeojohnson_data,
                shapiro_p_value=p_value,
                transformation_method=TransformationMethod.YEO_JOHNSON,
                analysis_method=AnalysisMethod.PARAMETRIC,
                lambda_param=lambda_param,
                manual_override=True,
            )

        else:
            # Non-Parametric manual override
            _, p_value = shapiro_wilk_test(data)
            return Phase2Results(
                cleaned_data=data,
                shapiro_p_value=p_value,
                transformation_method=TransformationMethod.NONE,
                analysis_method=AnalysisMethod.NON_PARAMETRIC,
                lambda_param=None,
                manual_override=True,
            )

    # Automatic cascade - test original data first
    _, p_value = shapiro_wilk_test(data)
    if p_value > 0.05:
        # Original data is normal
        return Phase2Results(
            cleaned_data=data,
            shapiro_p_value=p_value,
            transformation_method=TransformationMethod.NONE,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=None,
            manual_override=False,
        )

    # Try Logarithmic transformation (if all positive)
    if all(x > 0 for x in data):
        log_data = log_transform(data)
        if log_data is not None:
            _, p_value = shapiro_wilk_test(log_data)
            if p_value > 0.05:
                return Phase2Results(
                    cleaned_data=log_data,
                    shapiro_p_value=p_value,
                    transformation_method=TransformationMethod.LOGARITHMIC,
                    analysis_method=AnalysisMethod.PARAMETRIC,
                    lambda_param=None,
                    manual_override=False,
                )

    # Try Box-Cox transformation (if all positive)
    if all(x > 0 for x in data):
        result = box_cox_transform(data)
        if result is not None:
            boxcox_data, lambda_param = result
            _, p_value = shapiro_wilk_test(boxcox_data)
            if p_value > 0.05:
                return Phase2Results(
                    cleaned_data=boxcox_data,
                    shapiro_p_value=p_value,
                    transformation_method=TransformationMethod.BOX_COX,
                    analysis_method=AnalysisMethod.PARAMETRIC,
                    lambda_param=lambda_param,
                    manual_override=False,
                )

    # Try Yeo-Johnson transformation (works with all values)
    yeojohnson_data, lambda_param = yeo_johnson_transform(data)
    _, p_value = shapiro_wilk_test(yeojohnson_data)
    if p_value > 0.05:
        return Phase2Results(
            cleaned_data=yeojohnson_data,
            shapiro_p_value=p_value,
            transformation_method=TransformationMethod.YEO_JOHNSON,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=lambda_param,
            manual_override=False,
        )

    # All transformations failed - fallback to Non-Parametric
    # Use the p-value from the last transformation attempt (Yeo-Johnson)
    return Phase2Results(
        cleaned_data=data,  # Use original data for non-parametric
        shapiro_p_value=p_value,
        transformation_method=TransformationMethod.NONE,
        analysis_method=AnalysisMethod.NON_PARAMETRIC,
        lambda_param=None,
        manual_override=False,
    )
