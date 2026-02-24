"""Normality testing functions using Shapiro-Wilk test.

This module provides statistical tests for assessing whether data follows
a normal distribution. The Shapiro-Wilk test is used as the primary method
for normality testing in the transformation cascade.

References:
- Shapiro, S. S., & Wilk, M. B. (1965). An analysis of variance test for
  normality (complete samples). Biometrika, 52(3/4), 591-611.
"""

from scipy import stats


def shapiro_wilk_test(data: list[float]) -> tuple[float, float]:
    """Perform Shapiro-Wilk test for normality.

    The Shapiro-Wilk test is a statistical test that assesses whether a sample
    comes from a normally distributed population. It is considered one of the
    most powerful normality tests, especially for small to medium sample sizes.

    Args:
        data: List of numeric values to test for normality

    Returns:
        tuple: (statistic, p_value)
            - statistic: The Shapiro-Wilk test statistic
            - p_value: The p-value from the test. A p-value > 0.05 suggests the data
              is consistent with a normal distribution at the 5% significance level.

    Examples:
        >>> # Normal data should have high p-value
        >>> import numpy as np
        >>> np.random.seed(42)
        >>> normal_data = np.random.normal(0, 1, 100).tolist()
        >>> statistic, p_value = shapiro_wilk_test(normal_data)
        >>> p_value > 0.05
        True

        >>> # Uniform data should have low p-value
        >>> uniform_data = np.random.uniform(0, 1, 100).tolist()
        >>> statistic, p_value = shapiro_wilk_test(uniform_data)
        >>> p_value < 0.05
        True

    Notes:
        - Uses scipy.stats.shapiro() for computation
        - Returns both test statistic and p-value
        - Interpretation:
          * p > 0.05: Data is consistent with normal distribution
          * p ≤ 0.05: Data significantly deviates from normality
        - Most effective for sample sizes between 3 and 5000

    Validates: Requirements 9.1, 9.2, 3.9
    """
    # Perform Shapiro-Wilk test using scipy
    # Returns (statistic, p_value)
    statistic, p_value = stats.shapiro(data)

    return float(statistic), float(p_value)


def is_normal(p_value: float, alpha: float = 0.05) -> bool:
    """Determine if data is normal based on Shapiro-Wilk p-value.

    This function classifies data as normal or non-normal based on the
    p-value from a Shapiro-Wilk test and a significance level (alpha).

    Args:
        p_value: The p-value from a Shapiro-Wilk test
        alpha: Significance level for the test (default: 0.05)

    Returns:
        True if data is classified as normal (p > alpha), False otherwise

    Examples:
        >>> is_normal(0.10)  # p > 0.05
        True

        >>> is_normal(0.03)  # p < 0.05
        False

        >>> is_normal(0.08, alpha=0.10)  # p < 0.10
        False

    Notes:
        - Default alpha = 0.05 corresponds to 95% confidence level
        - Returns True when p_value > alpha (fail to reject normality)
        - Returns False when p_value ≤ alpha (reject normality)

    Validates: Requirements 9.3, 9.4
    """
    return p_value > alpha


def anderson_darling_test(data: list[float]) -> tuple[float, list[float], list[float]]:
    """Perform Anderson-Darling test for normality.

    The Anderson-Darling test is a statistical test that assesses whether a sample
    comes from a normally distributed population. It is particularly sensitive to
    deviations in the tails of the distribution, making it complementary to the
    Shapiro-Wilk test.

    Args:
        data: List of numeric values to test for normality

    Returns:
        tuple: (statistic, critical_values, significance_levels)
            - statistic: The Anderson-Darling test statistic
            - critical_values: Critical values at different significance levels
            - significance_levels: Significance levels (typically [15%, 10%, 5%, 2.5%, 1%])

    Examples:
        >>> # Normal data should have low statistic
        >>> import numpy as np
        >>> np.random.seed(42)
        >>> normal_data = np.random.normal(0, 1, 100).tolist()
        >>> statistic, critical_values, sig_levels = anderson_darling_test(normal_data)
        >>> statistic < critical_values[2]  # Should be less than 5% critical value
        True

        >>> # Uniform data should have high statistic
        >>> uniform_data = np.random.uniform(0, 1, 100).tolist()
        >>> statistic, critical_values, sig_levels = anderson_darling_test(uniform_data)
        >>> statistic > critical_values[2]  # Should exceed 5% critical value
        True

    Notes:
        - Uses scipy.stats.anderson() for computation
        - Returns statistic and critical values at multiple significance levels
        - Interpretation:
          * If statistic < critical_value: Data is consistent with normal distribution
          * If statistic ≥ critical_value: Data significantly deviates from normality
        - More sensitive to tail deviations than Shapiro-Wilk
        - Effective for sample sizes > 7
        - For constant data (zero variance), returns statistic=0.0 (perfectly normal)

    Validates: Requirements 2.8, 3.9
    """
    import numpy as np

    # Check for constant data (zero variance)
    # Anderson-Darling test requires variance, constant data is degenerate
    data_array = np.array(data)
    if np.std(data_array) < 1e-10:
        # Constant data is technically a degenerate normal distribution
        # Return statistic=0.0 (perfectly normal) with standard critical values
        return (
            0.0,
            [0.576, 0.656, 0.787, 0.918, 1.092],  # Standard critical values
            [15.0, 10.0, 5.0, 2.5, 1.0],
        )

    # Perform Anderson-Darling test using scipy
    # Returns AndersonResult with statistic, critical_values, significance_level
    result = stats.anderson(data, dist="norm")

    # Handle NaN or invalid statistic
    statistic = float(result.statistic)
    if np.isnan(statistic) or np.isinf(statistic):
        # Return 0.0 for invalid statistics (treat as normal)
        statistic = 0.0

    return (
        statistic,
        result.critical_values.tolist(),
        result.significance_level.tolist(),
    )
