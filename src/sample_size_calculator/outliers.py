"""Outlier detection and exclusion using the IQR (Interquartile Range) method.

This module implements outlier detection for pilot data analysis in Module V.
It uses the standard IQR method to identify outliers and provides functionality
to exclude outliers with engineering rationale.

References:
    - IQR Method: Tukey, J. W. (1977). Exploratory Data Analysis.
    - ISO/TR 80002-2: Medical device software validation guidance
"""

import numpy as np

from sample_size_calculator.models import OutlierInfo, Phase1Results


def detect_outliers(data: list[float]) -> Phase1Results:
    """Detect outliers in pilot data using the IQR method.

    The IQR (Interquartile Range) method identifies outliers as values that fall
    outside the range [Q1 - 1.5*IQR, Q3 + 1.5*IQR], where:
    - Q1 is the 25th percentile (first quartile)
    - Q3 is the 75th percentile (third quartile)
    - IQR = Q3 - Q1

    This method is idempotent: applying it multiple times to the same dataset
    will always identify the same outliers.

    Args:
        data: List of numeric pilot data values (minimum 3 values required)

    Returns:
        Phase1Results containing:
            - pilot_data: Original input data
            - outliers: List of OutlierInfo objects for detected outliers
            - q1: First quartile (25th percentile)
            - q3: Third quartile (75th percentile)
            - iqr: Interquartile range (Q3 - Q1)

    Raises:
        ValueError: If data contains fewer than 3 values

    Example:
        >>> data = [1.0, 2.0, 3.0, 4.0, 5.0, 100.0]  # 100.0 is an outlier
        >>> results = detect_outliers(data)
        >>> len(results.outliers)
        1
        >>> results.outliers[0].value
        100.0
    """
    if len(data) < 3:
        raise ValueError("Pilot dataset must contain at least 3 data points")

    # Calculate quartiles using numpy
    # Using linear interpolation (default) for consistency
    q1 = float(np.percentile(data, 25))
    q3 = float(np.percentile(data, 75))
    iqr = q3 - q1

    # Calculate outlier bounds
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    # Identify outliers
    outliers: list[OutlierInfo] = []
    for value in data:
        if value < lower_bound or value > upper_bound:
            outliers.append(OutlierInfo(value=value, is_excluded=False, rationale=None))

    return Phase1Results(pilot_data=data, outliers=outliers, q1=q1, q3=q3, iqr=iqr)


def apply_exclusions(
    phase1_results: Phase1Results, exclusions: list[OutlierInfo]
) -> list[float]:
    """Apply user-specified outlier exclusions to create a cleaned dataset.

    This function removes excluded outliers from the pilot data and validates
    that each exclusion has a non-empty engineering rationale. This ensures
    traceability and compliance with QMS requirements.

    Args:
        phase1_results: Results from Phase 1 outlier detection
        exclusions: List of OutlierInfo objects marked for exclusion
                   (is_excluded=True with non-empty rationale)

    Returns:
        Cleaned dataset with excluded outliers removed

    Raises:
        ValueError: If any excluded outlier lacks a non-empty rationale

    Example:
        >>> phase1 = detect_outliers([1.0, 2.0, 3.0, 100.0])
        >>> outlier = phase1.outliers[0]
        >>> outlier.is_excluded = True
        >>> outlier.rationale = "Measurement error - sensor malfunction"
        >>> cleaned = apply_exclusions(phase1, [outlier])
        >>> cleaned
        [1.0, 2.0, 3.0]
    """
    # Validate that all exclusions have non-empty rationales
    for exclusion in exclusions:
        if exclusion.is_excluded:
            if not exclusion.rationale or exclusion.rationale.strip() == "":
                raise ValueError(
                    f"Outlier exclusion requires non-empty rationale. "
                    f"Outlier value: {exclusion.value}"
                )

    # Create set of excluded values for efficient lookup
    excluded_values = {
        exclusion.value for exclusion in exclusions if exclusion.is_excluded
    }

    # Filter out excluded outliers from pilot data
    cleaned_data = [
        value for value in phase1_results.pilot_data if value not in excluded_values
    ]

    return cleaned_data
