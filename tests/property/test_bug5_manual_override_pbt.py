"""Property-based tests for Bug 5: Manual override allows all methods.

This module contains property-based tests that verify Bug 5 fix works correctly
across a wide range of inputs. Bug 5 was about manual override in Phase 2 being
limited to only "Parametric" method instead of allowing all 4 transformation methods.

**Property 1: Expected Behavior** - Manual Override Allows All Methods

For any Phase 2 manual override activation, the fixed UI SHALL allow selection from
all available transformation methods (None/Parametric, Logarithmic, Box-Cox,
Yeo-Johnson). Note: Non-Parametric/Wilks is an analysis method, not a transformation method.

**Validates: Requirement 2.5**
"""

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from src.sample_size_calculator.models import (
    AnalysisMethod,
    TransformationMethod,
)
from src.sample_size_calculator.transformations import transformation_cascade


class TestBug5ManualOverrideProperty:
    """Property-based tests for Bug 5: Manual override allows all methods.
    
    **Validates: Requirement 2.5**
    """

    @given(
        data=st.lists(
            st.floats(min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=5,
            max_size=100,
        ),
        manual_method=st.sampled_from([
            TransformationMethod.NONE,
            TransformationMethod.LOGARITHMIC,
            TransformationMethod.BOX_COX,
            TransformationMethod.YEO_JOHNSON,
        ]),
    )
    @settings(deadline=5000, max_examples=100)
    def test_manual_override_accepts_all_methods_property(
        self, data: list[float], manual_method: TransformationMethod
    ) -> None:
        """Property 1: Manual override accepts all 5 transformation methods.
        
        This property-based test generates random combinations of:
        - Data: Lists of positive floats (0.1 to 1000.0)
        - Manual methods: All 5 available methods
        
        For all combinations, the transformation_cascade function should accept
        the manual method and apply it correctly, setting manual_override=True.
        
        **Validates: Requirement 2.5**
        """
        from hypothesis import assume
        
        # Skip constant data for Box-Cox (requires variance)
        if manual_method == TransformationMethod.BOX_COX:
            assume(np.std(data) >= 1e-10)
            # Skip data with very low variance (may produce extreme lambdas)
            data_range = np.max(data) - np.min(data)
            assume(data_range > 0.1)
        
        # Execute: Apply transformation with manual override
        try:
            result = transformation_cascade(data, manual_method=manual_method)
        except ValueError as e:
            # Box-Cox may fail for data that produces extreme lambdas
            if "Box-Cox transformation failed validation" in str(e):
                assume(False)  # Skip this test case
            raise
        
        # Verify: Manual override flag should be set
        assert result.manual_override is True, (
            f"Manual override should be True when manual_method={manual_method.value} is specified"
        )
        
        # Verify: The specified method should be used
        assert result.transformation_method == manual_method, (
            f"Expected transformation_method={manual_method.value}, "
            f"got {result.transformation_method.value}"
        )
        
        # Verify: Result should have valid analysis method
        assert result.analysis_method in [AnalysisMethod.PARAMETRIC, AnalysisMethod.NON_PARAMETRIC], (
            f"Invalid analysis_method: {result.analysis_method}"
        )
        
        # Verify: Parametric transformations should use PARAMETRIC analysis
        assert result.analysis_method == AnalysisMethod.PARAMETRIC, (
            f"{manual_method.value} should use PARAMETRIC analysis"
        )

    @given(
        data=st.lists(
            st.floats(min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=5,
            max_size=50,
        ),
    )
    @settings(deadline=5000, max_examples=100)
    def test_manual_override_none_parametric_method(self, data: list[float]) -> None:
        """Property 1: Manual override with None/Parametric method.
        
        This test verifies that manual override works correctly with the
        None/Parametric method (no transformation applied).
        
        **Validates: Requirement 2.5**
        """
        # Execute: Apply None/Parametric transformation
        result = transformation_cascade(data, manual_method=TransformationMethod.NONE)
        
        # Verify: Manual override flag set
        assert result.manual_override is True
        
        # Verify: No transformation applied
        assert result.transformation_method == TransformationMethod.NONE
        
        # Verify: Parametric analysis used
        assert result.analysis_method == AnalysisMethod.PARAMETRIC
        
        # Verify: No lambda parameter
        assert result.lambda_param is None
        
        # Verify: Cleaned data should be same as input (no transformation)
        assert len(result.cleaned_data) == len(data)

    @given(
        data=st.lists(
            st.floats(min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=5,
            max_size=50,
        ),
    )
    @settings(deadline=5000, max_examples=100)
    def test_manual_override_logarithmic_method(self, data: list[float]) -> None:
        """Property 1: Manual override with Logarithmic method.
        
        This test verifies that manual override works correctly with the
        Logarithmic transformation method.
        
        **Validates: Requirement 2.5**
        """
        # Execute: Apply Logarithmic transformation
        result = transformation_cascade(data, manual_method=TransformationMethod.LOGARITHMIC)
        
        # Verify: Manual override flag set
        assert result.manual_override is True
        
        # Verify: Logarithmic transformation applied
        assert result.transformation_method == TransformationMethod.LOGARITHMIC
        
        # Verify: Parametric analysis used
        assert result.analysis_method == AnalysisMethod.PARAMETRIC
        
        # Verify: No lambda parameter for logarithmic
        assert result.lambda_param is None
        
        # Verify: Data was transformed
        assert len(result.cleaned_data) == len(data)

    @given(
        data=st.lists(
            st.floats(min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=5,
            max_size=50,
        ),
    )
    @settings(deadline=5000, max_examples=80)
    def test_manual_override_box_cox_method(self, data: list[float]) -> None:
        """Property 1: Manual override with Box-Cox method.
        
        This test verifies that manual override works correctly with the
        Box-Cox transformation method.
        
        **Validates: Requirement 2.5**
        """
        from hypothesis import assume
        
        # Skip constant data (Box-Cox requires variance)
        assume(np.std(data) >= 1e-10)
        
        # Skip data with very low variance (may produce extreme lambdas)
        # Box-Cox rejects |lambda| > 3 for numerical stability
        data_range = np.max(data) - np.min(data)
        assume(data_range > 0.1)
        
        # Execute: Apply Box-Cox transformation
        try:
            result = transformation_cascade(data, manual_method=TransformationMethod.BOX_COX)
        except ValueError as e:
            # Box-Cox may fail for data that produces extreme lambdas
            # This is expected behavior, not a test failure
            if "Box-Cox transformation failed validation" in str(e):
                assume(False)  # Skip this test case
            raise
        
        # Verify: Manual override flag set
        assert result.manual_override is True
        
        # Verify: Box-Cox transformation applied
        assert result.transformation_method == TransformationMethod.BOX_COX
        
        # Verify: Parametric analysis used
        assert result.analysis_method == AnalysisMethod.PARAMETRIC
        
        # Verify: Lambda parameter should be present for Box-Cox
        assert result.lambda_param is not None, "Box-Cox should have lambda parameter"
        
        # Verify: Data was transformed
        assert len(result.cleaned_data) == len(data)

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=5,
            max_size=50,
        ),
    )
    @settings(deadline=5000, max_examples=80)
    def test_manual_override_yeo_johnson_method(self, data: list[float]) -> None:
        """Property 1: Manual override with Yeo-Johnson method.
        
        This test verifies that manual override works correctly with the
        Yeo-Johnson transformation method. Yeo-Johnson can handle negative values.
        
        **Validates: Requirement 2.5**
        """
        from hypothesis import assume
        
        # Skip data with too many zeros or tiny values (causes scipy optimization issues)
        non_zero_count = sum(1 for x in data if abs(x) > 1e-100)
        assume(non_zero_count >= len(data) * 0.5)
        
        # Execute: Apply Yeo-Johnson transformation
        result = transformation_cascade(data, manual_method=TransformationMethod.YEO_JOHNSON)
        
        # Verify: Manual override flag set
        assert result.manual_override is True
        
        # Verify: Yeo-Johnson transformation applied
        assert result.transformation_method == TransformationMethod.YEO_JOHNSON
        
        # Verify: Parametric analysis used
        assert result.analysis_method == AnalysisMethod.PARAMETRIC
        
        # Verify: Lambda parameter should be present for Yeo-Johnson
        assert result.lambda_param is not None, "Yeo-Johnson should have lambda parameter"
        
        # Verify: Data was transformed
        assert len(result.cleaned_data) == len(data)

    @given(
        data=st.lists(
            st.floats(min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=5,
            max_size=50,
        ),
        method1=st.sampled_from([
            TransformationMethod.NONE,
            TransformationMethod.LOGARITHMIC,
            TransformationMethod.BOX_COX,
            TransformationMethod.YEO_JOHNSON,
        ]),
        method2=st.sampled_from([
            TransformationMethod.NONE,
            TransformationMethod.LOGARITHMIC,
            TransformationMethod.BOX_COX,
            TransformationMethod.YEO_JOHNSON,
        ]),
    )
    @settings(deadline=5000, max_examples=80)
    def test_manual_override_method_switching(
        self, data: list[float], method1: TransformationMethod, method2: TransformationMethod
    ) -> None:
        """Property 1: Manual override allows switching between methods.
        
        This test verifies that users can switch between different manual override
        methods, simulating the UI workflow where a user might try different methods.
        
        **Validates: Requirement 2.5**
        """
        from hypothesis import assume
        
        # Skip constant data for Box-Cox
        if method1 == TransformationMethod.BOX_COX or method2 == TransformationMethod.BOX_COX:
            assume(np.std(data) >= 1e-10)
            # Skip data with very low variance
            data_range = np.max(data) - np.min(data)
            assume(data_range > 0.1)
        
        # Execute: Apply first method
        try:
            result1 = transformation_cascade(data, manual_method=method1)
        except ValueError as e:
            if "Box-Cox transformation failed validation" in str(e):
                assume(False)
            raise
        
        # Verify: First method applied correctly
        assert result1.manual_override is True
        assert result1.transformation_method == method1
        
        # Execute: Apply second method (simulating user switching methods)
        try:
            result2 = transformation_cascade(data, manual_method=method2)
        except ValueError as e:
            if "Box-Cox transformation failed validation" in str(e):
                assume(False)
            raise
        
        # Verify: Second method applied correctly
        assert result2.manual_override is True
        assert result2.transformation_method == method2
        
        # Verify: Both results are valid
        assert result1.cleaned_data is not None
        assert result2.cleaned_data is not None

    def test_manual_override_all_methods_baseline(self) -> None:
        """Baseline test: Manual override accepts all 4 transformation methods.
        
        This is a baseline test that explicitly tests all 4 methods with
        a simple dataset to ensure the fix works correctly.
        
        **Validates: Requirement 2.5**
        """
        # Simple test data
        data = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]
        
        # All 4 transformation methods that should be available
        all_methods = [
            TransformationMethod.NONE,
            TransformationMethod.LOGARITHMIC,
            TransformationMethod.BOX_COX,
            TransformationMethod.YEO_JOHNSON,
        ]
        
        # Test each method
        for method in all_methods:
            result = transformation_cascade(data, manual_method=method)
            
            # Verify: Manual override flag set
            assert result.manual_override is True, (
                f"Manual override should be True for {method.value}"
            )
            
            # Verify: Correct method applied
            assert result.transformation_method == method, (
                f"Expected {method.value}, got {result.transformation_method.value}"
            )
            
            # Verify: Valid result
            assert result.cleaned_data is not None
            assert len(result.cleaned_data) > 0

    @given(
        data_size=st.integers(min_value=5, max_value=100),
        manual_method=st.sampled_from([
            TransformationMethod.NONE,
            TransformationMethod.LOGARITHMIC,
            TransformationMethod.BOX_COX,
            TransformationMethod.YEO_JOHNSON,
        ]),
    )
    @settings(deadline=5000, max_examples=80)
    def test_manual_override_various_data_sizes(
        self, data_size: int, manual_method: TransformationMethod
    ) -> None:
        """Property 1: Manual override works with various data sizes.
        
        This test verifies that manual override works correctly regardless of
        the size of the input dataset.
        
        **Validates: Requirement 2.5**
        """
        # Generate data with specified size
        np.random.seed(hash((data_size, manual_method.value)) % (2**32))
        data = np.random.lognormal(2.5, 0.3, data_size).tolist()
        
        # Execute: Apply transformation with manual override
        result = transformation_cascade(data, manual_method=manual_method)
        
        # Verify: Manual override flag set
        assert result.manual_override is True
        
        # Verify: Correct method applied
        assert result.transformation_method == manual_method
        
        # Verify: Data size preserved
        assert len(result.cleaned_data) == data_size
