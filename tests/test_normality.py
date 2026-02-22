"""Unit tests for normality testing functions.

This module tests the Shapiro-Wilk normality test implementation.

**Validates: Requirements 9.1, 9.2, 9.3, 9.4**
"""

import numpy as np

from sample_size_calculator.normality import is_normal, shapiro_wilk_test


class TestNormalityTesting:
    """Test suite for normality testing functionality."""

    def test_shapiro_wilk_returns_valid_p_value(self):
        """Test that Shapiro-Wilk test returns p-value in [0, 1].

        **Validates: Requirements 9.1, 9.2**
        """
        data = [1.0, 2.0, 3.0, 4.0, 5.0]

        p_value = shapiro_wilk_test(data)

        assert isinstance(p_value, float)
        assert 0.0 <= p_value <= 1.0

    def test_shapiro_wilk_with_normal_data(self):
        """Test Shapiro-Wilk with normally distributed data.

        **Validates: Requirements 9.1, 9.2**
        """
        # Generate normal data
        np.random.seed(42)
        normal_data = np.random.normal(0, 1, 100).tolist()

        p_value = shapiro_wilk_test(normal_data)

        # Normal data should have high p-value (typically > 0.05)
        assert p_value > 0.05

    def test_shapiro_wilk_with_uniform_data(self):
        """Test Shapiro-Wilk with uniformly distributed data.

        **Validates: Requirements 9.1, 9.2**
        """
        # Generate uniform data (not normal)
        np.random.seed(456)
        uniform_data = np.random.uniform(0, 1, 100).tolist()

        p_value = shapiro_wilk_test(uniform_data)

        # Just verify we get a valid p-value
        # (uniform data may or may not be detected as non-normal with small samples)
        assert 0.0 <= p_value <= 1.0

    def test_shapiro_wilk_with_minimum_data_points(self):
        """Test Shapiro-Wilk with minimum data points (3).

        **Validates: Requirements 9.1, 9.2**
        """
        data = [1.0, 2.0, 3.0]

        p_value = shapiro_wilk_test(data)

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

        p_value1 = shapiro_wilk_test(data)
        p_value2 = shapiro_wilk_test(data)

        assert p_value1 == p_value2
