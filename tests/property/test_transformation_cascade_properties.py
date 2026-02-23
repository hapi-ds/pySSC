"""Property-based tests for transformation cascade logic.

This module contains property-based tests using Hypothesis to verify
the transformation cascade logic and manual override functionality.
"""

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.sample_size_calculator.models import (
    AnalysisMethod,
    TransformationMethod,
)
from src.sample_size_calculator.transformations import transformation_cascade


class TestTransformationCascadeProperties:
    """Property-based tests for transformation cascade logic."""

    @given(
        data=st.lists(
            st.floats(
                min_value=-1000.0,
                max_value=1000.0,
                allow_nan=False,
                allow_subnormal=False,
            ),
            min_size=3,
            max_size=50,
            unique=True,
        ).filter(lambda x: max(x) - min(x) > 0.01)
    )
    @settings(deadline=2000)
    def test_property_14a_cascade_returns_valid_phase2_results(
        self, data: list[float]
    ) -> None:
        """Property 14a: Transformation Cascade Always Returns Valid Phase2Results.

        **Validates: Requirements 10.1-10.5, 11.1-11.6, 12.1-12.4, 13.1**

        For all valid datasets, the transformation cascade should always return
        a valid Phase2Results object with all required fields populated.
        """
        result = transformation_cascade(data)

        # Verify result structure
        assert result is not None, "Cascade should always return a result"
        assert hasattr(result, "cleaned_data"), "Result should have cleaned_data"
        assert hasattr(result, "shapiro_p_value"), "Result should have shapiro_p_value"
        assert hasattr(result, "transformation_method"), (
            "Result should have transformation_method"
        )
        assert hasattr(result, "analysis_method"), "Result should have analysis_method"
        assert hasattr(result, "lambda_param"), "Result should have lambda_param"
        assert hasattr(result, "manual_override"), "Result should have manual_override"

        # Verify data integrity
        assert len(result.cleaned_data) > 0, "Cleaned data should not be empty"
        assert isinstance(result.shapiro_p_value, float), "P-value should be a float"
        assert 0.0 <= result.shapiro_p_value <= 1.0, (
            f"P-value should be in [0, 1], got {result.shapiro_p_value}"
        )

        # Verify transformation method is valid
        assert result.transformation_method in TransformationMethod, (
            f"Transformation method should be a valid TransformationMethod, "
            f"got {result.transformation_method}"
        )

        # Verify analysis method is valid
        assert result.analysis_method in AnalysisMethod, (
            f"Analysis method should be a valid AnalysisMethod, "
            f"got {result.analysis_method}"
        )

        # Verify manual_override is False for automatic cascade
        assert result.manual_override is False, (
            "Manual override should be False for automatic cascade"
        )

    @given(
        data=st.lists(
            st.floats(
                min_value=-1000.0,
                max_value=1000.0,
                allow_nan=False,
                allow_subnormal=False,
            ),
            min_size=3,
            max_size=50,
            unique=True,
        ).filter(lambda x: max(x) - min(x) > 0.01)
    )
    @settings(deadline=2000)
    def test_property_14b_transformation_method_matches_analysis_method(
        self, data: list[float]
    ) -> None:
        """Property 14b: Transformation Method Matches Analysis Method.

        **Validates: Requirements 10.1-10.5, 11.1-11.6, 12.1-12.4, 13.1**

        For all datasets, if a transformation is applied (Log, Box-Cox, Yeo-Johnson),
        the analysis method should be Parametric. If no transformation achieves
        normality, the analysis method should be Non-Parametric.
        """
        result = transformation_cascade(data)

        if result.transformation_method in [
            TransformationMethod.LOGARITHMIC,
            TransformationMethod.BOX_COX,
            TransformationMethod.YEO_JOHNSON,
        ]:
            # If a transformation was applied, method should be Parametric
            assert result.analysis_method == AnalysisMethod.PARAMETRIC, (
                f"Transformation {result.transformation_method} should use "
                f"Parametric method, got {result.analysis_method}"
            )
        elif result.transformation_method == TransformationMethod.NONE:
            # If no transformation, could be either Parametric (original data normal)
            # or Non-Parametric (all transformations failed)
            if result.shapiro_p_value > 0.05:
                assert result.analysis_method == AnalysisMethod.PARAMETRIC, (
                    "Normal original data should use Parametric method"
                )
            else:
                assert result.analysis_method == AnalysisMethod.NON_PARAMETRIC, (
                    "Non-normal data with no transformation should use Non-Parametric method"
                )

    @given(
        data=st.lists(
            st.floats(
                min_value=-1000.0,
                max_value=1000.0,
                allow_nan=False,
                allow_subnormal=False,
            ),
            min_size=3,
            max_size=50,
            unique=True,
        ).filter(lambda x: max(x) - min(x) > 0.01)
    )
    @settings(deadline=2000)
    def test_property_14c_lambda_param_set_correctly(self, data: list[float]) -> None:
        """Property 14c: Lambda Parameter Set Correctly for Box-Cox and Yeo-Johnson.

        **Validates: Requirements 11.2, 11.5, 12.2, 12.4**

        For all datasets, if Box-Cox or Yeo-Johnson transformation is applied,
        the lambda_param should be set to a valid float value. For other
        transformations, lambda_param should be None.
        """
        result = transformation_cascade(data)

        if result.transformation_method == TransformationMethod.BOX_COX:
            assert result.lambda_param is not None, (
                "Box-Cox transformation should have lambda_param set"
            )
            assert isinstance(result.lambda_param, float), (
                "Lambda param should be a float"
            )
        elif result.transformation_method == TransformationMethod.YEO_JOHNSON:
            assert result.lambda_param is not None, (
                "Yeo-Johnson transformation should have lambda_param set"
            )
            assert isinstance(result.lambda_param, float), (
                "Lambda param should be a float"
            )
        else:
            # Log or None transformation should not have lambda_param
            assert result.lambda_param is None, (
                f"Transformation {result.transformation_method} should not have "
                f"lambda_param, got {result.lambda_param}"
            )

    @given(
        data=st.lists(
            st.floats(
                min_value=-1000.0,
                max_value=1000.0,
                allow_nan=False,
                allow_subnormal=False,
            ),
            min_size=3,
            max_size=50,
            unique=True,
        ).filter(lambda x: max(x) - min(x) > 0.01)
    )
    @settings(deadline=2000)
    def test_property_14d_data_length_preserved(self, data: list[float]) -> None:
        """Property 14d: Data Length is Preserved Through Transformation.

        **Validates: Requirements 10.1-10.5, 11.1-11.6, 12.1-12.4**

        For all datasets, the transformation cascade should preserve the number
        of data points (no data loss).
        """
        result = transformation_cascade(data)

        assert len(result.cleaned_data) == len(data), (
            f"Data length should be preserved: original={len(data)}, "
            f"transformed={len(result.cleaned_data)}"
        )

    @given(
        data=st.lists(
            st.floats(min_value=0.01, max_value=1000.0, allow_nan=False),
            min_size=3,
            max_size=50,
            unique=True,
        ).filter(lambda x: max(x) - min(x) > 0.01)
    )
    @settings(deadline=2000)
    def test_property_14e_log_and_boxcox_only_with_positive_data(
        self, data: list[float]
    ) -> None:
        """Property 14e: Log and Box-Cox Only Used with Positive Data.

        **Validates: Requirements 10.1, 10.2, 10.5, 11.1, 11.2, 11.6**

        For all positive datasets, Log and Box-Cox transformations can be
        attempted. The cascade should skip these for non-positive data.
        """
        # Test with positive data - Log and Box-Cox are possible
        result_positive = transformation_cascade(data)

        # If Log or Box-Cox was selected, all data must be positive
        if result_positive.transformation_method in [
            TransformationMethod.LOGARITHMIC,
            TransformationMethod.BOX_COX,
        ]:
            assert all(x > 0 for x in data), (
                f"Transformation {result_positive.transformation_method} requires "
                f"positive data, but data contains non-positive values"
            )

        # Test with data containing zero or negative values
        data_with_zero = [0.0] + data[1:]
        result_with_zero = transformation_cascade(data_with_zero)

        # Log and Box-Cox should be skipped
        assert result_with_zero.transformation_method not in [
            TransformationMethod.LOGARITHMIC,
            TransformationMethod.BOX_COX,
        ], (
            f"Log and Box-Cox should be skipped for non-positive data, "
            f"got {result_with_zero.transformation_method}"
        )

        # Should use Yeo-Johnson or Non-Parametric
        assert result_with_zero.transformation_method in [
            TransformationMethod.YEO_JOHNSON,
            TransformationMethod.NONE,
        ], (
            f"Should use Yeo-Johnson or None for non-positive data, "
            f"got {result_with_zero.transformation_method}"
        )

    @given(
        data=st.lists(
            st.floats(
                min_value=-1000.0,
                max_value=1000.0,
                allow_nan=False,
                allow_subnormal=False,
            ),
            min_size=3,
            max_size=50,
            unique=True,
        ).filter(lambda x: max(x) - min(x) > 0.01)
    )
    @settings(deadline=2000)
    def test_property_14f_yeo_johnson_works_with_all_data_ranges(
        self, data: list[float]
    ) -> None:
        """Property 14f: Yeo-Johnson Works with All Data Ranges.

        **Validates: Requirements 12.1, 12.2, 12.5**

        For all datasets (positive, zero, negative), Yeo-Johnson transformation
        should always be applicable and should not raise errors.
        """
        result = transformation_cascade(data)

        # Yeo-Johnson should never fail due to data range
        # If it was selected, it should have succeeded
        if result.transformation_method == TransformationMethod.YEO_JOHNSON:
            assert result.lambda_param is not None, (
                "Yeo-Johnson should have lambda_param"
            )
            assert len(result.cleaned_data) == len(data), (
                "Yeo-Johnson should preserve data length"
            )

        # Test with explicitly negative data
        negative_data = [-abs(x) for x in data]
        result_negative = transformation_cascade(negative_data)

        # Should not crash and should return valid result
        assert result_negative is not None, "Cascade should handle negative data"
        assert len(result_negative.cleaned_data) == len(negative_data), (
            "Data length should be preserved for negative data"
        )


class TestManualOverrideProperties:
    """Property-based tests for manual override functionality."""

    @given(
        data=st.lists(
            st.floats(min_value=0.01, max_value=1000.0, allow_nan=False),
            min_size=3,
            max_size=50,
            unique=True,
        ).filter(lambda x: max(x) - min(x) > 0.01)
    )
    @settings(deadline=2000)
    def test_property_15a_manual_override_sets_flag(self, data: list[float]) -> None:
        """Property 15a: Manual Override Sets manual_override=True.

        **Validates: Requirements 10.6, 11.7, 12.6, 13.5**

        For all datasets, when a manual transformation method is specified,
        the result should have manual_override=True.
        """
        # Test each manual override option
        manual_methods = [
            TransformationMethod.NONE,
            TransformationMethod.LOGARITHMIC,
            TransformationMethod.BOX_COX,
            TransformationMethod.YEO_JOHNSON,
        ]

        for method in manual_methods:
            result = transformation_cascade(data, manual_method=method)

            assert result.manual_override is True, (
                f"Manual override with {method} should set manual_override=True"
            )
            assert result.transformation_method == method, (
                f"Manual override should use specified method {method}, "
                f"got {result.transformation_method}"
            )

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=-0.01, allow_nan=False),
            min_size=3,
            max_size=50,
            unique=True,
        ).filter(lambda x: max(x) - min(x) > 0.01)
    )
    @settings(deadline=2000)
    def test_property_15b_manual_log_boxcox_raises_error_with_non_positive(
        self, data: list[float]
    ) -> None:
        """Property 15b: Manual Log/Box-Cox Raises Error with Non-Positive Data.

        **Validates: Requirements 10.7, 11.8**

        For all non-positive datasets, manually selecting Log or Box-Cox
        transformation should raise a ValueError.
        """
        # Test manual Log with non-positive data
        with pytest.raises(ValueError, match="Logarithmic transformation requires"):
            transformation_cascade(data, manual_method=TransformationMethod.LOGARITHMIC)

        # Test manual Box-Cox with non-positive data
        with pytest.raises(ValueError, match="Box-Cox transformation requires"):
            transformation_cascade(data, manual_method=TransformationMethod.BOX_COX)

    @given(
        data=st.lists(
            st.floats(
                min_value=-1000.0,
                max_value=1000.0,
                allow_nan=False,
                allow_subnormal=False,
            ),
            min_size=3,
            max_size=50,
            unique=True,
        ).filter(lambda x: max(x) - min(x) > 0.01)
    )
    @settings(deadline=2000)
    def test_property_15c_manual_yeo_johnson_works_with_all_data(
        self, data: list[float]
    ) -> None:
        """Property 15c: Manual Yeo-Johnson Works with All Data.

        **Validates: Requirements 12.6**

        For all datasets (positive, zero, negative), manually selecting
        Yeo-Johnson transformation should succeed without errors.
        """
        result = transformation_cascade(
            data, manual_method=TransformationMethod.YEO_JOHNSON
        )

        assert result.manual_override is True, "Should have manual_override=True"
        assert result.transformation_method == TransformationMethod.YEO_JOHNSON, (
            "Should use Yeo-Johnson transformation"
        )
        assert result.lambda_param is not None, "Should have lambda_param"
        assert len(result.cleaned_data) == len(data), "Should preserve data length"

        # Test with explicitly negative data
        negative_data = [-abs(x) for x in data]
        result_negative = transformation_cascade(
            negative_data, manual_method=TransformationMethod.YEO_JOHNSON
        )

        assert result_negative.manual_override is True
        assert result_negative.transformation_method == TransformationMethod.YEO_JOHNSON
        assert len(result_negative.cleaned_data) == len(negative_data)

    @given(
        data=st.lists(
            st.floats(min_value=0.01, max_value=1000.0, allow_nan=False),
            min_size=3,
            max_size=50,
            unique=True,
        ).filter(lambda x: max(x) - min(x) > 0.01)
    )
    @settings(deadline=2000)
    def test_property_15d_manual_override_bypasses_cascade_logic(
        self, data: list[float]
    ) -> None:
        """Property 15d: Manual Override Bypasses Cascade Logic.

        **Validates: Requirements 10.6, 11.7, 12.6, 13.5**

        For all datasets, manual override should apply the specified method
        regardless of whether the data is normal or whether other transformations
        would achieve better normality.
        """
        # Get automatic cascade result
        auto_result = transformation_cascade(data)

        # Force a different method manually
        if auto_result.transformation_method != TransformationMethod.LOGARITHMIC:
            manual_result = transformation_cascade(
                data, manual_method=TransformationMethod.LOGARITHMIC
            )

            assert (
                manual_result.transformation_method == TransformationMethod.LOGARITHMIC
            ), "Manual override should force Logarithmic transformation"
            assert manual_result.manual_override is True
            # The p-value might be different from automatic cascade
            # because we're forcing a specific method

        # Force Box-Cox
        if auto_result.transformation_method != TransformationMethod.BOX_COX:
            manual_result_bc = transformation_cascade(
                data, manual_method=TransformationMethod.BOX_COX
            )

            assert (
                manual_result_bc.transformation_method == TransformationMethod.BOX_COX
            ), "Manual override should force Box-Cox transformation"
            assert manual_result_bc.manual_override is True

        # Force Yeo-Johnson
        if auto_result.transformation_method != TransformationMethod.YEO_JOHNSON:
            manual_result_yj = transformation_cascade(
                data, manual_method=TransformationMethod.YEO_JOHNSON
            )

            assert (
                manual_result_yj.transformation_method
                == TransformationMethod.YEO_JOHNSON
            ), "Manual override should force Yeo-Johnson transformation"
            assert manual_result_yj.manual_override is True

    @given(
        data=st.lists(
            st.floats(min_value=0.01, max_value=1000.0, allow_nan=False),
            min_size=3,
            max_size=50,
            unique=True,
        ).filter(lambda x: max(x) - min(x) > 0.01)
    )
    @settings(deadline=2000)
    def test_property_15e_manual_none_uses_original_data(
        self, data: list[float]
    ) -> None:
        """Property 15e: Manual NONE Uses Original Data.

        **Validates: Requirements 10.6, 13.5**

        For all datasets, manually selecting NONE transformation should use
        the original data without any transformation, regardless of normality.
        """
        result = transformation_cascade(data, manual_method=TransformationMethod.NONE)

        assert result.manual_override is True, "Should have manual_override=True"
        assert result.transformation_method == TransformationMethod.NONE, (
            "Should use NONE transformation"
        )
        assert result.lambda_param is None, "Should not have lambda_param"
        assert result.analysis_method == AnalysisMethod.PARAMETRIC, (
            "Manual NONE should use Parametric method"
        )
        # Data should be unchanged
        assert np.allclose(result.cleaned_data, data), (
            "Manual NONE should preserve original data"
        )
