"""Normality testing functions using Shapiro-Wilk test.

This module provides statistical tests for assessing whether data follows
a normal distribution. The Shapiro-Wilk test is used as the primary method
for normality testing in the transformation cascade.

References:
- Shapiro, S. S., & Wilk, M. B. (1965). An analysis of variance test for
  normality (complete samples). Biometrika, 52(3/4), 591-611.
"""

from scipy import stats


def shapiro_wilk_test(data: list[float]) -> float:
    """Perform Shapiro-Wilk test for normality.

    The Shapiro-Wilk test is a statistical test that assesses whether a sample
    comes from a normally distributed population. It is considered one of the
    most powerful normality tests, especially for small to medium sample sizes.

    Args:
        data: List of numeric values to test for normality

    Returns:
        p-value from the Shapiro-Wilk test. A p-value > 0.05 suggests the data
        is consistent with a normal distribution at the 5% significance level.

    Examples:
        >>> # Normal data should have high p-value
        >>> import numpy as np
        >>> np.random.seed(42)
        >>> normal_data = np.random.normal(0, 1, 100).tolist()
        >>> p_value = shapiro_wilk_test(normal_data)
        >>> p_value > 0.05
        True

        >>> # Uniform data should have low p-value
        >>> uniform_data = np.random.uniform(0, 1, 100).tolist()
        >>> p_value = shapiro_wilk_test(uniform_data)
        >>> p_value < 0.05
        True

    Notes:
        - Uses scipy.stats.shapiro() for computation
        - Returns only the p-value (not the test statistic)
        - Interpretation:
          * p > 0.05: Data is consistent with normal distribution
          * p ≤ 0.05: Data significantly deviates from normality
        - Most effective for sample sizes between 3 and 5000

    Validates: Requirements 9.1, 9.2
    """
    # Perform Shapiro-Wilk test using scipy
    # Returns (statistic, p_value)
    _, p_value = stats.shapiro(data)

    return float(p_value)


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
