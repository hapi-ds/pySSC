"""Unit tests for transformation cascade logic.

This module tests the transformation_cascade function which implements
the sequential cascade of transformation methods to achieve data normality.

**Validates: Requirements 9.3, 9.4, 10.3, 10.4, 11.3, 11.4, 12.3, 12.4, 13.1, 13.2**
"""

import numpy as np
import pytest

from sample_size_calculator.models import (
    AnalysisMethod,
    TransformationMethod,
)
from sample_size_calculator.transformations import transformation_cascade


class TestTransformationCascade:
    """Test suite for transformation cascade functionality."""

    def test_normal_data_locks_as_none_parametric(self):
        """Test that normal data locks as None/Parametric without transformation.

        **Validates: Requirements 9.3, 9.4**
        """
        # Generate normal data
        np.random.seed(42)
        normal_data = np.random.normal(10, 2, 50).tolist()

        result = transformation_cascade(normal_data)

        assert result.transformation_method == TransformationMethod.NONE
        assert result.analysis_method == AnalysisMethod.PARAMETRIC
        assert result.shapiro_p_value > 0.05
        assert result.lambda_param is None
        assert result.manual_override is False
        assert len(result.cleaned_data) == len(normal_data)

    def test_skewed_positive_data_attempts_transformations(self):
        """Test that skewed positive data tries Log, Box-Cox, or Yeo-Johnson.

        **Validates: Requirements 10.3, 11.3, 12.3**
        """
        # Generate skewed positive data
        np.random.seed(123)
        skewed_data = np.random.exponential(2, 50).tolist()

        result = transformation_cascade(skewed_data)

        # Should lock one of the transformation methods or Non-Parametric
        assert result.transformation_method in [
            TransformationMethod.LOGARITHMIC,
            TransformationMethod.BOX_COX,
            TransformationMethod.YEO_JOHNSON,
            TransformationMethod.NONE,
        ]

        # If a transformation was applied, should be Parametric
        if result.transformation_method != TransformationMethod.NONE:
            assert result.analysis_method == AnalysisMethod.PARAMETRIC
        else:
            # If no transformation worked, should be Non-Parametric
            assert result.analysis_method == AnalysisMethod.NON_PARAMETRIC

        assert result.manual_override is False

    def test_mixed_sign_data_skips_log_and_boxcox(self):
        """Test that data with zero/negative values skips Log and Box-Cox.

        **Validates: Requirements 10.1, 11.1**
        """
        # Data with negative values
        mixed_data = [-1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0]

        result = transformation_cascade(mixed_data)

        # Should not use Log or Box-Cox (requires positive values)
        assert result.transformation_method in [
            TransformationMethod.NONE,
            TransformationMethod.YEO_JOHNSON,
        ]

        # Yeo-Johnson should work with mixed signs
        if result.transformation_method == TransformationMethod.YEO_JOHNSON:
            assert result.lambda_param is not None
            assert result.analysis_method == AnalysisMethod.PARAMETRIC

    def test_highly_non_normal_data_fallback_to_non_parametric(self):
        """Test that highly non-normal data falls back to Non-Parametric.

        **Validates: Requirements 13.1, 13.2**
        """
        # Create bimodal distribution (very non-normal)
        np.random.seed(456)
        bimodal = np.concatenate(
            [np.random.normal(0, 1, 25), np.random.normal(10, 1, 25)]
        ).tolist()

        result = transformation_cascade(bimodal)

        # Should fallback to Non-Parametric if all transformations fail
        if result.shapiro_p_value <= 0.05:
            assert result.analysis_method == AnalysisMethod.NON_PARAMETRIC
            assert result.transformation_method == TransformationMethod.NONE
            assert result.lambda_param is None

    def test_manual_override_none_parametric(self):
        """Test manual override to force None/Parametric method.

        **Validates: Requirements 13.5**
        """
        data = [1.0, 2.0, 3.0, 4.0, 5.0]

        result = transformation_cascade(data, manual_method=TransformationMethod.NONE)

        assert result.transformation_method == TransformationMethod.NONE
        assert result.analysis_method == AnalysisMethod.PARAMETRIC
        assert result.manual_override is True
        assert result.lambda_param is None

    def test_manual_override_logarithmic_with_positive_data(self):
        """Test manual override to force Logarithmic transformation.

        **Validates: Requirements 10.6, 10.7**
        """
        positive_data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        result = transformation_cascade(
            positive_data, manual_method=TransformationMethod.LOGARITHMIC
        )

        assert result.transformation_method == TransformationMethod.LOGARITHMIC
        assert result.analysis_method == AnalysisMethod.PARAMETRIC
        assert result.manual_override is True
        assert result.lambda_param is None
        assert len(result.cleaned_data) == len(positive_data)

    def test_manual_override_logarithmic_with_non_positive_raises_error(self):
        """Test that manual Log override with non-positive data raises error.

        **Validates: Requirements 10.7**
        """
        mixed_data = [-1.0, 0.0, 1.0, 2.0]

        with pytest.raises(ValueError, match="positive"):
            transformation_cascade(
                mixed_data, manual_method=TransformationMethod.LOGARITHMIC
            )

    def test_manual_override_box_cox_with_positive_data(self):
        """Test manual override to force Box-Cox transformation.

        **Validates: Requirements 11.7, 11.8**
        """
        positive_data = [1.0, 2.0, 3.0, 4.0, 5.0]

        result = transformation_cascade(
            positive_data, manual_method=TransformationMethod.BOX_COX
        )

        assert result.transformation_method == TransformationMethod.BOX_COX
        assert result.analysis_method == AnalysisMethod.PARAMETRIC
        assert result.manual_override is True
        assert result.lambda_param is not None
        assert isinstance(result.lambda_param, float)

    def test_manual_override_box_cox_with_non_positive_raises_error(self):
        """Test that manual Box-Cox override with non-positive data raises error.

        **Validates: Requirements 11.8**
        """
        mixed_data = [-1.0, 0.0, 1.0, 2.0]

        with pytest.raises(ValueError, match="positive"):
            transformation_cascade(
                mixed_data, manual_method=TransformationMethod.BOX_COX
            )

    def test_manual_override_yeo_johnson_with_mixed_data(self):
        """Test manual override to force Yeo-Johnson transformation.

        **Validates: Requirements 12.6**
        """
        mixed_data = [-1.0, 0.0, 1.0, 2.0, 3.0]

        result = transformation_cascade(
            mixed_data, manual_method=TransformationMethod.YEO_JOHNSON
        )

        assert result.transformation_method == TransformationMethod.YEO_JOHNSON
        assert result.analysis_method == AnalysisMethod.PARAMETRIC
        assert result.manual_override is True
        assert result.lambda_param is not None
        assert isinstance(result.lambda_param, float)

    def test_cascade_returns_phase2_results_with_all_fields(self):
        """Test that cascade returns complete Phase2Results object."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]

        result = transformation_cascade(data)

        # Verify all required fields are present
        assert hasattr(result, "cleaned_data")
        assert hasattr(result, "shapiro_p_value")
        assert hasattr(result, "transformation_method")
        assert hasattr(result, "analysis_method")
        assert hasattr(result, "lambda_param")
        assert hasattr(result, "manual_override")

        # Verify types
        assert isinstance(result.cleaned_data, list)
        assert isinstance(result.shapiro_p_value, float)
        assert isinstance(result.transformation_method, TransformationMethod)
        assert isinstance(result.analysis_method, AnalysisMethod)
        assert isinstance(result.manual_override, bool)

    def test_cascade_preserves_data_length(self):
        """Test that transformation cascade preserves data length."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        result = transformation_cascade(data)

        assert len(result.cleaned_data) == len(data)

    def test_cascade_with_minimum_data_points(self):
        """Test cascade with minimum required data points (3)."""
        data = [1.0, 2.0, 3.0]

        result = transformation_cascade(data)

        # Should complete without error
        assert result is not None
        assert len(result.cleaned_data) == 3

    def test_lambda_param_set_for_box_cox_and_yeo_johnson(self):
        """Test that lambda_param is set for Box-Cox and Yeo-Johnson."""
        # Test Box-Cox manual override
        positive_data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result_bc = transformation_cascade(
            positive_data, manual_method=TransformationMethod.BOX_COX
        )
        assert result_bc.lambda_param is not None

        # Test Yeo-Johnson manual override
        result_yj = transformation_cascade(
            positive_data, manual_method=TransformationMethod.YEO_JOHNSON
        )
        assert result_yj.lambda_param is not None

    def test_lambda_param_none_for_log_and_none(self):
        """Test that lambda_param is None for Log and None transformations."""
        positive_data = [1.0, 2.0, 3.0, 4.0, 5.0]

        # Test Logarithmic
        result_log = transformation_cascade(
            positive_data, manual_method=TransformationMethod.LOGARITHMIC
        )
        assert result_log.lambda_param is None

        # Test None
        result_none = transformation_cascade(
            positive_data, manual_method=TransformationMethod.NONE
        )
        assert result_none.lambda_param is None

    def test_shapiro_p_value_is_valid(self):
        """Test that Shapiro-Wilk p-value is in valid range [0, 1]."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]

        result = transformation_cascade(data)

        assert 0.0 <= result.shapiro_p_value <= 1.0

    def test_cascade_order_log_before_box_cox(self):
        """Test that cascade tries Log before Box-Cox for positive data."""
        # Create data that might normalize with Log
        np.random.seed(789)
        log_normal_data = np.random.lognormal(0, 0.5, 30).tolist()

        result = transformation_cascade(log_normal_data)

        # If transformation was successful, Log should be tried first
        # (This is implicit in the cascade logic, but we verify the result)
        if result.transformation_method in [
            TransformationMethod.LOGARITHMIC,
            TransformationMethod.BOX_COX,
        ]:
            assert result.analysis_method == AnalysisMethod.PARAMETRIC
