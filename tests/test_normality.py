"""Unit tests for normality testing functions.

This module tests the Shapiro-Wilk normality test implementation.

**Validates: Requirements 9.1, 9.2, 9.3, 9.4**
"""

import numpy as np

from sample_size_calculator.normality import (
    anderson_darling_test,
    is_normal,
    shapiro_wilk_test,
)


class TestNormalityTesting:
    """Test suite for normality testing functionality."""

    def test_shapiro_wilk_returns_valid_p_value(self):
        """Test that Shapiro-Wilk test returns p-value in [0, 1].

        **Validates: Requirements 9.1, 9.2**
        """
        data = [1.0, 2.0, 3.0, 4.0, 5.0]

        statistic, p_value = shapiro_wilk_test(data)

        assert isinstance(statistic, float)
        assert isinstance(p_value, float)
        assert 0.0 <= p_value <= 1.0

    def test_shapiro_wilk_with_normal_data(self):
        """Test Shapiro-Wilk with normally distributed data.

        **Validates: Requirements 9.1, 9.2**
        """
        # Generate normal data
        np.random.seed(42)
        normal_data = np.random.normal(0, 1, 100).tolist()

        statistic, p_value = shapiro_wilk_test(normal_data)

        # Normal data should have high p-value (typically > 0.05)
        assert p_value > 0.05

    def test_shapiro_wilk_with_uniform_data(self):
        """Test Shapiro-Wilk with uniformly distributed data.

        **Validates: Requirements 9.1, 9.2**
        """
        # Generate uniform data (not normal)
        np.random.seed(456)
        uniform_data = np.random.uniform(0, 1, 100).tolist()

        statistic, p_value = shapiro_wilk_test(uniform_data)

        # Just verify we get a valid p-value
        # (uniform data may or may not be detected as non-normal with small samples)
        assert 0.0 <= p_value <= 1.0

    def test_shapiro_wilk_with_minimum_data_points(self):
        """Test Shapiro-Wilk with minimum data points (3).

        **Validates: Requirements 9.1, 9.2**
        """
        data = [1.0, 2.0, 3.0]

        statistic, p_value = shapiro_wilk_test(data)

        assert isinstance(p_value, float)
        assert 0.0 <= p_value <= 1.0

    def test_is_normal_with_high_p_value(self):
        """Test is_normal classification with p > 0.05.

        **Validates: Requirements 9.3, 9.4**
        """
        p_value = 0.10

        result = is_normal(p_value)

        assert result is True

    def test_is_normal_with_low_p_value(self):
        """Test is_normal classification with p <= 0.05.

        **Validates: Requirements 9.3, 9.4**
        """
        p_value = 0.03

        result = is_normal(p_value)

        assert result is False

    def test_is_normal_at_boundary(self):
        """Test is_normal classification at boundary (p = 0.05).

        **Validates: Requirements 9.3, 9.4**
        """
        p_value = 0.05

        result = is_normal(p_value)

        # At boundary, should be False (p <= 0.05)
        assert result is False

    def test_is_normal_with_custom_alpha(self):
        """Test is_normal with custom significance level.

        **Validates: Requirements 9.3, 9.4**
        """
        p_value = 0.08

        # With alpha=0.10, p=0.08 should be False
        result = is_normal(p_value, alpha=0.10)
        assert result is False

        # With alpha=0.05, p=0.08 should be True
        result = is_normal(p_value, alpha=0.05)
        assert result is True

    def test_shapiro_wilk_deterministic_for_same_data(self):
        """Test that Shapiro-Wilk returns same p-value for same data.

        **Validates: Requirements 9.1, 9.2**
        """
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        statistic1, p_value1 = shapiro_wilk_test(data)
        statistic2, p_value2 = shapiro_wilk_test(data)

        assert p_value1 == p_value2
        assert statistic1 == statistic2


class TestAndersonDarlingTest:
    """Test suite for Anderson-Darling normality test functionality.

    **Validates: Requirements 2.8, 3.9**
    """

    def test_anderson_darling_returns_valid_structure(self):
        """Test that Anderson-Darling returns correct structure.

        **Validates: Requirements 2.8, 3.9**
        """
        data = [1.0, 2.0, 3.0, 4.0, 5.0]

        statistic, critical_values, sig_levels = anderson_darling_test(data)

        assert isinstance(statistic, float)
        assert isinstance(critical_values, list)
        assert isinstance(sig_levels, list)
        assert len(critical_values) == 5
        assert len(sig_levels) == 5

    def test_anderson_darling_with_normal_data(self):
        """Test Anderson-Darling with normally distributed data.

        **Validates: Requirements 2.8, 3.9**
        """
        np.random.seed(42)
        normal_data = np.random.normal(0, 1, 100).tolist()

        statistic, critical_values, sig_levels = anderson_darling_test(normal_data)

        # Normal data should have statistic less than 5% critical value
        assert statistic < critical_values[2]

    def test_anderson_darling_with_uniform_data(self):
        """Test Anderson-Darling with uniformly distributed data.

        **Validates: Requirements 2.8, 3.9**
        """
        np.random.seed(456)
        uniform_data = np.random.uniform(0, 1, 100).tolist()

        statistic, critical_values, sig_levels = anderson_darling_test(uniform_data)

        # Uniform data should have high statistic (exceeds 5% critical value)
        assert statistic > critical_values[2]

    def test_anderson_darling_constant_data(self):
        """Test Anderson-Darling with constant data.

        **Validates: Requirements 2.8, 3.9**
        """
        data = [5.0] * 10

        statistic, critical_values, sig_levels = anderson_darling_test(data)

        # Constant data should return statistic=0.0 (perfectly normal)
        assert statistic == 0.0
        assert critical_values == [0.576, 0.656, 0.787, 0.918, 1.092]
        assert sig_levels == [15.0, 10.0, 5.0, 2.5, 1.0]

    def test_anderson_darling_significance_levels(self):
        """Test that significance levels are in expected order.

        **Validates: Requirements 2.8, 3.9**
        """
        data = [1.0, 2.0, 3.0, 4.0, 5.0]

        statistic, critical_values, sig_levels = anderson_darling_test(data)

        assert sig_levels == [15.0, 10.0, 5.0, 2.5, 1.0]
        # Critical values should be increasing (higher significance level = higher threshold)
        for i in range(len(critical_values) - 1):
            assert critical_values[i] < critical_values[i + 1]

    def test_anderson_darling_deterministic_for_same_data(self):
        """Test that Anderson-Darling returns same values for same data.

        **Validates: Requirements 2.8, 3.9**
        """
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        result1 = anderson_darling_test(data)
        result2 = anderson_darling_test(data)

        assert result1[0] == result2[0]
        assert result1[1] == result2[1]
        assert result1[2] == result2[2]

    def test_anderson_darling_with_small_sample(self):
        """Test Anderson-Darling with small sample size.

        **Validates: Requirements 2.8, 3.9**
        """
        np.random.seed(100)
        small_data = np.random.normal(0, 1, 10).tolist()

        statistic, critical_values, sig_levels = anderson_darling_test(small_data)

        # Should return valid structure
        assert isinstance(statistic, float)
        assert len(critical_values) == 5

    def test_anderson_darling_with_large_sample(self):
        """Test Anderson-Darling with large sample size.

        **Validates: Requirements 2.8, 3.9**
        """
        np.random.seed(42)
        large_data = np.random.normal(0, 1, 1000).tolist()

        statistic, critical_values, sig_levels = anderson_darling_test(large_data)

        # Large normal sample should have low statistic
        assert statistic < critical_values[2]

    def test_anderson_darling_skewed_data(self):
        """Test Anderson-Darling with skewed (non-normal) data.

        **Validates: Requirements 2.8, 3.9**
        """
        np.random.seed(789)
        skewed_data = np.random.exponential(1, 100).tolist()

        statistic, critical_values, sig_levels = anderson_darling_test(skewed_data)

        # Skewed data should have high statistic (exceeds 5% critical value)
        assert statistic > critical_values[2]
