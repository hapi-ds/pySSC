"""Unit tests for inverse transformation functions.

This module tests the round-trip property of transformation functions:
forward transformation followed by inverse transformation should return
the original values within numerical precision.

Validates: Requirement 22.5 (round-trip property)
"""

import numpy as np

from src.sample_size_calculator.transformations import (
    box_cox_transform,
    inverse_box_cox_transform,
    inverse_log_transform,
    inverse_yeo_johnson_transform,
    log_transform,
    yeo_johnson_transform,
)


class TestInverseLogTransform:
    """Tests for inverse logarithmic transformation."""

    def test_inverse_log_basic(self):
        """Test inverse log transform with simple positive values."""
        original = [1.0, 2.0, 3.0, 4.0, 5.0]
        transformed = log_transform(original)
        assert transformed is not None, "Transform should succeed with positive values"
        back = inverse_log_transform(transformed)

        assert np.allclose(original, back, rtol=1e-10)

    def test_inverse_log_round_trip(self):
        """Test round-trip property: original -> log -> inverse_log -> original."""
        original = [0.5, 1.0, 2.5, 10.0, 100.0]
        transformed = log_transform(original)
        assert transformed is not None, "Transform should succeed with positive values"
        back = inverse_log_transform(transformed)

        assert np.allclose(original, back, rtol=1e-10)

    def test_inverse_log_single_value(self):
        """Test inverse log transform with single value."""
        original = [2.718281828459045]  # e
        transformed = log_transform(original)
        assert transformed is not None, "Transform should succeed with positive values"
        back = inverse_log_transform(transformed)

        assert np.allclose(original, back, rtol=1e-10)


class TestInverseBoxCoxTransform:
    """Tests for inverse Box-Cox transformation."""

    def test_inverse_box_cox_basic(self):
        """Test inverse Box-Cox transform with simple positive values."""
        original = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = box_cox_transform(original)
        assert result is not None, "Transform should succeed with positive values"
        transformed, lambda_param = result
        back = inverse_box_cox_transform(transformed, lambda_param)

        assert np.allclose(original, back, rtol=1e-10)

    def test_inverse_box_cox_round_trip(self):
        """Test round-trip property: original -> box_cox -> inverse_box_cox -> original."""
        original = [0.5, 1.0, 2.5, 10.0, 100.0]
        result = box_cox_transform(original)
        assert result is not None, "Transform should succeed with positive values"
        transformed, lambda_param = result
        back = inverse_box_cox_transform(transformed, lambda_param)

        assert np.allclose(original, back, rtol=1e-10)

    def test_inverse_box_cox_lambda_zero(self):
        """Test inverse Box-Cox when lambda is close to zero (log case)."""
        # Create data that will result in lambda close to 0
        original = [1.0, 1.1, 1.2, 1.3, 1.4]
        result = box_cox_transform(original)
        assert result is not None, "Transform should succeed with positive values"
        transformed, lambda_param = result
        back = inverse_box_cox_transform(transformed, lambda_param)

        assert np.allclose(original, back, rtol=1e-10)

    def test_inverse_box_cox_various_lambdas(self):
        """Test inverse Box-Cox with different data patterns."""
        test_cases = [
            [1.0, 2.0, 3.0, 4.0, 5.0],
            [0.1, 0.5, 1.0, 5.0, 10.0],
            [10.0, 20.0, 30.0, 40.0, 50.0],
        ]

        for original in test_cases:
            result = box_cox_transform(original)
            assert result is not None, "Transform should succeed with positive values"
            transformed, lambda_param = result
            back = inverse_box_cox_transform(transformed, lambda_param)
            assert np.allclose(original, back, rtol=1e-10)


class TestInverseYeoJohnsonTransform:
    """Tests for inverse Yeo-Johnson transformation."""

    def test_inverse_yeo_johnson_positive(self):
        """Test inverse Yeo-Johnson with positive values."""
        original = [1.0, 2.0, 3.0, 4.0, 5.0]
        transformed, lambda_param = yeo_johnson_transform(original)
        back = inverse_yeo_johnson_transform(transformed, lambda_param)

        assert np.allclose(original, back, rtol=1e-10)

    def test_inverse_yeo_johnson_mixed_signs(self):
        """Test inverse Yeo-Johnson with mixed positive, zero, and negative values."""
        original = [-2.0, -1.0, 0.0, 1.0, 2.0]
        transformed, lambda_param = yeo_johnson_transform(original)
        back = inverse_yeo_johnson_transform(transformed, lambda_param)

        assert np.allclose(original, back, rtol=1e-10)

    def test_inverse_yeo_johnson_negative(self):
        """Test inverse Yeo-Johnson with negative values."""
        original = [-5.0, -4.0, -3.0, -2.0, -1.0]
        transformed, lambda_param = yeo_johnson_transform(original)
        back = inverse_yeo_johnson_transform(transformed, lambda_param)

        assert np.allclose(original, back, rtol=1e-10)

    def test_inverse_yeo_johnson_round_trip(self):
        """Test round-trip property: original -> yeo_johnson -> inverse_yeo_johnson -> original."""
        original = [-10.0, -1.0, 0.0, 1.0, 10.0]
        transformed, lambda_param = yeo_johnson_transform(original)
        back = inverse_yeo_johnson_transform(transformed, lambda_param)

        assert np.allclose(original, back, rtol=1e-10)

    def test_inverse_yeo_johnson_various_patterns(self):
        """Test inverse Yeo-Johnson with different data patterns."""
        test_cases = [
            [0.1, 0.5, 1.0, 5.0, 10.0],
            [-0.5, -0.1, 0.1, 0.5, 1.0],
            [-100.0, -10.0, 0.0, 10.0, 100.0],
        ]

        for original in test_cases:
            transformed, lambda_param = yeo_johnson_transform(original)
            back = inverse_yeo_johnson_transform(transformed, lambda_param)
            assert np.allclose(original, back, rtol=1e-10)

    def test_inverse_yeo_johnson_single_value(self):
        """Test inverse Yeo-Johnson with single value."""
        original = [3.14159]
        transformed, lambda_param = yeo_johnson_transform(original)
        back = inverse_yeo_johnson_transform(transformed, lambda_param)

        assert np.allclose(original, back, rtol=1e-10)


class TestRoundTripProperty:
    """Tests specifically for the round-trip property (Requirement 22.5)."""

    def test_log_round_trip_tolerance_limits(self):
        """Test round-trip property for log transformation with tolerance limit values."""
        # Simulate tolerance limits in transformed space
        tolerance_limits = [0.5, 1.0, 1.5, 2.0, 2.5]

        # Back-transform to original space
        original_limits = inverse_log_transform(tolerance_limits)

        # Forward-transform back to transformed space
        back_to_transformed = log_transform(original_limits)
        assert back_to_transformed is not None, (
            "Transform should succeed with positive values"
        )

        # Should match within numerical precision
        assert np.allclose(tolerance_limits, back_to_transformed, rtol=1e-10)

    def test_box_cox_round_trip_tolerance_limits(self):
        """Test round-trip property for Box-Cox transformation with tolerance limit values."""
        # Create sample data and transform it
        sample_data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = box_cox_transform(sample_data)
        assert result is not None, "Transform should succeed with positive values"
        transformed_data, lambda_param = result

        # Simulate tolerance limits calculated in transformed space
        # (e.g., mean ± k * std in transformed space)
        mean_t = np.mean(transformed_data)
        std_t = np.std(transformed_data, ddof=1)
        tolerance_limits: list[float] = [
            float(mean_t - 2 * std_t),
            float(mean_t + 2 * std_t),
        ]

        # Back-transform to original space
        original_limits = inverse_box_cox_transform(tolerance_limits, lambda_param)

        # Forward-transform back to transformed space using the same lambda
        # For Box-Cox, we need to manually apply the transformation with the locked lambda
        if np.abs(lambda_param) < 1e-10:
            back_to_transformed = np.log(original_limits).tolist()
        else:
            back_to_transformed = (
                (np.power(original_limits, lambda_param) - 1) / lambda_param
            ).tolist()

        # Should match within numerical precision
        assert np.allclose(tolerance_limits, back_to_transformed, rtol=1e-9)

    def test_yeo_johnson_round_trip_tolerance_limits(self):
        """Test round-trip property for Yeo-Johnson transformation with tolerance limit values."""
        # Create sample data and transform it
        sample_data = [-2.0, -1.0, 0.0, 1.0, 2.0]
        result = yeo_johnson_transform(sample_data)
        assert result is not None, "Transform should succeed"
        transformed_data, lambda_param = result

        # Simulate tolerance limits calculated in transformed space
        # (e.g., mean ± k * std in transformed space)
        mean_t = np.mean(transformed_data)
        std_t = np.std(transformed_data, ddof=1)
        tolerance_limits: list[float] = [
            float(mean_t - 2 * std_t),
            float(mean_t + 2 * std_t),
        ]

        # Back-transform to original space
        original_limits = inverse_yeo_johnson_transform(tolerance_limits, lambda_param)

        # Forward-transform back to transformed space using the same lambda
        # For Yeo-Johnson, we need to manually apply the transformation with the locked lambda
        def apply_yeo_johnson(x, lam):
            if x >= 0:
                if np.abs(lam) >= 1e-10:
                    return (np.power(x + 1, lam) - 1) / lam
                else:
                    return np.log(x + 1)
            else:
                if np.abs(lam - 2) >= 1e-10:
                    return -(np.power(-x + 1, 2 - lam) - 1) / (2 - lam)
                else:
                    return -np.log(-x + 1)

        back_to_transformed = [
            apply_yeo_johnson(x, lambda_param) for x in original_limits
        ]

        # Should match within numerical precision
        assert np.allclose(tolerance_limits, back_to_transformed, rtol=1e-9)
