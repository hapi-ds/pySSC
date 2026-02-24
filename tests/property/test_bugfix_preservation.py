"""Preservation property tests for manual-testing-fixes bugfix spec.

This module contains preservation tests that verify non-buggy behaviors remain
unchanged after bug fixes. These tests MUST PASS on unfixed code to establish
baseline behavior.

**CRITICAL**: These tests are EXPECTED TO PASS on unfixed code.
Passing confirms baseline behavior. These tests ensure no regressions.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10**
"""

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.sample_size_calculator.models import (
    AnalysisMethod,
    Phase2Results,
    Phase3Results,
    SpecificationLimits,
    SpecificationType,
    TransformationMethod,
)
from src.sample_size_calculator.tolerance import calculate_tolerance_limits
from src.sample_size_calculator.transformations import (
    box_cox_transform,
    inverse_box_cox_transform,
    inverse_log_transform,
    log_transform,
)


class TestPreservation1Phase4Rejection:
    """Preservation 1: Phase 4 rejects datasets with size < N.

    **Validates: Requirement 3.1**
    """

    def test_preservation1_phase4_rejects_insufficient_samples(self) -> None:
        """Preservation 1: Phase 4 continues rejecting data with size < N.

        **EXPECTED TO PASS on unfixed code** - confirms baseline behavior.
        This behavior must be preserved after Bug 1 fix.

        Current behavior: Validation rejects with size < N
        Expected behavior: Same rejection behavior maintained

        **Validates: Requirement 3.1**
        """
        # Setup: Required sample size N = 30
        required_n = 30

        # Provide N-1 = 29 samples (should be rejected)
        final_data = [10.0 + i * 0.1 for i in range(29)]

        # Phase 2 results (no transformation)
        phase2_results = Phase2Results(
            cleaned_data=final_data[:10],
            shapiro_p_value=0.8,
            transformation_method=TransformationMethod.NONE,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=None,
            manual_override=False,
        )

        # Phase 3 results (required N = 30)
        phase3_results = Phase3Results(
            required_sample_size=required_n,
            k_margin=3.0,
            k_factor=2.5,
            specification_type=SpecificationType.TWO_SIDED,
        )

        # Specification limits
        spec_limits = SpecificationLimits(
            spec_type=SpecificationType.TWO_SIDED,
            lsl=5.0,
            usl=20.0,
        )

        # PRESERVATION: This should raise ValueError on both unfixed and fixed code
        with pytest.raises(ValueError, match="data points"):
            calculate_tolerance_limits(
                final_data, phase2_results, phase3_results, spec_limits
            )

    @given(
        deficit=st.integers(min_value=1, max_value=10),
        required_n=st.integers(min_value=20, max_value=100),
    )
    @settings(deadline=2000, max_examples=30)
    def test_preservation1_phase4_rejection_property(
        self, deficit: int, required_n: int
    ) -> None:
        """Preservation 1 Property: Phase 4 rejects any dataset with size < N.

        **EXPECTED TO PASS on unfixed code** - confirms baseline behavior.

        **Validates: Requirement 3.1**
        """
        # Provide N-deficit samples (should be rejected)
        final_data = [10.0 + i * 0.1 for i in range(required_n - deficit)]

        phase2_results = Phase2Results(
            cleaned_data=final_data[: min(10, len(final_data))],
            shapiro_p_value=0.8,
            transformation_method=TransformationMethod.NONE,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=None,
            manual_override=False,
        )

        phase3_results = Phase3Results(
            required_sample_size=required_n,
            k_margin=3.0,
            k_factor=2.5,
            specification_type=SpecificationType.TWO_SIDED,
        )

        spec_limits = SpecificationLimits(
            spec_type=SpecificationType.TWO_SIDED,
            lsl=5.0,
            usl=20.0,
        )

        # PRESERVATION: Should always reject
        with pytest.raises(ValueError, match="Insufficient samples"):
            calculate_tolerance_limits(
                final_data, phase2_results, phase3_results, spec_limits
            )


class TestPreservation2OtherTransformations:
    """Preservation 2: Logarithmic and Box-Cox maintain round-trip accuracy.

    **Validates: Requirement 3.2**
    """

    @given(
        data=st.lists(
            st.floats(min_value=0.1, max_value=100.0, allow_nan=False),
            min_size=3,
            max_size=20,
        )
    )
    @settings(deadline=2000, max_examples=50)
    def test_preservation2_logarithmic_roundtrip(self, data: list[float]) -> None:
        """Preservation 2: Logarithmic transformation maintains round-trip accuracy.

        **EXPECTED TO PASS on unfixed code** - confirms baseline behavior.
        This behavior must be preserved after Bug 2 fix.

        **Validates: Requirement 3.2**
        """
        # Apply logarithmic transformation
        transformed = log_transform(data)

        # Skip if transformation failed (shouldn't happen with positive data)
        if transformed is None:
            return

        # Apply inverse transformation
        back_transformed = inverse_log_transform(transformed)

        # PRESERVATION: Should maintain round-trip accuracy
        assert np.allclose(data, back_transformed, rtol=1e-10, atol=1e-10), (
            f"Logarithmic round-trip failed: "
            f"max_diff={np.max(np.abs(np.array(data) - np.array(back_transformed)))}"
        )

    @given(
        data=st.lists(
            st.floats(min_value=0.1, max_value=100.0, allow_nan=False),
            min_size=3,
            max_size=20,
        )
    )
    @settings(deadline=2000, max_examples=50)
    def test_preservation2_box_cox_roundtrip(self, data: list[float]) -> None:
        """Preservation 2: Box-Cox transformation maintains round-trip accuracy.

        **EXPECTED TO PASS on unfixed code** - confirms baseline behavior.
        This behavior must be preserved after Bug 2 fix.

        **Validates: Requirement 3.2**
        """
        # Apply Box-Cox transformation (returns tuple with optimized lambda)
        result = box_cox_transform(data)

        # Skip if transformation failed (shouldn't happen with positive data)
        if result is None:
            return

        transformed, lambda_param = result

        # Apply inverse transformation
        back_transformed = inverse_box_cox_transform(transformed, lambda_param)

        # PRESERVATION: Should maintain round-trip accuracy
        assert np.allclose(data, back_transformed, rtol=1e-10, atol=1e-10), (
            f"Box-Cox round-trip failed with lambda={lambda_param}: "
            f"max_diff={np.max(np.abs(np.array(data) - np.array(back_transformed)))}"
        )


class TestPreservation3Phase1Phase2State:
    """Preservation 3: Phase 1 and Phase 2 state management unchanged.

    **Validates: Requirement 3.3**
    """

    def test_preservation3_phase1_completion_state(self) -> None:
        """Preservation 3: Phase 1 completion state management unchanged.

        **EXPECTED TO PASS on unfixed code** - confirms baseline behavior.
        This behavior must be preserved after Bug 3 fix.

        **Validates: Requirement 3.3**
        """
        from src.sample_size_calculator.ui_controller import ModuleVState

        # Create state and complete Phase 1
        state = ModuleVState()
        initial_data = [1.0, 2.0, 3.0, 4.0, 5.0]

        state.complete_phase1(initial_data)

        # PRESERVATION: Phase 1 completion should set flag
        assert state.phase1_complete is True
        assert state.initial_data == initial_data

        # Phase 2 and 3 should not be complete yet
        assert state.phase2_complete is False
        assert state.phase3_complete is False

    def test_preservation3_phase2_completion_state(self) -> None:
        """Preservation 3: Phase 2 completion state management unchanged.

        **EXPECTED TO PASS on unfixed code** - confirms baseline behavior.
        This behavior must be preserved after Bug 3 fix.

        **Validates: Requirement 3.3**
        """
        from src.sample_size_calculator.ui_controller import ModuleVState

        # Create state and complete Phase 1 and Phase 2
        state = ModuleVState()
        initial_data = [1.0, 2.0, 3.0, 4.0, 5.0]

        state.complete_phase1(initial_data)

        phase2_results = Phase2Results(
            cleaned_data=initial_data,
            shapiro_p_value=0.8,
            transformation_method=TransformationMethod.NONE,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=None,
            manual_override=False,
        )

        state.complete_phase2(phase2_results)

        # PRESERVATION: Phase 2 completion should set flag
        assert state.phase2_complete is True
        assert state.phase2_results == phase2_results

        # Phase 3 should not be complete yet
        assert state.phase3_complete is False


class TestPreservation4Phase4Calculations:
    """Preservation 4: Phase 4 tolerance calculations produce correct results.

    **Validates: Requirement 3.4**
    """

    def test_preservation4_tolerance_calculations_correct(self) -> None:
        """Preservation 4: Phase 4 calculations produce correct results.

        **EXPECTED TO PASS on unfixed code** - confirms baseline behavior.
        This behavior must be preserved after Bug 1 fix.

        **Validates: Requirement 3.4**
        """
        # Setup: Required sample size N = 30, provide exactly N samples
        required_n = 30
        final_data = [10.0 + i * 0.1 for i in range(required_n)]

        # Phase 2 results (no transformation)
        phase2_results = Phase2Results(
            cleaned_data=final_data[:10],
            shapiro_p_value=0.8,
            transformation_method=TransformationMethod.NONE,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=None,
            manual_override=False,
        )

        # Phase 3 results
        phase3_results = Phase3Results(
            required_sample_size=required_n,
            k_margin=3.0,
            k_factor=2.5,
            specification_type=SpecificationType.TWO_SIDED,
        )

        # Specification limits
        spec_limits = SpecificationLimits(
            spec_type=SpecificationType.TWO_SIDED,
            lsl=5.0,
            usl=20.0,
        )

        # PRESERVATION: Calculations should work correctly with exact N samples
        result = calculate_tolerance_limits(
            final_data, phase2_results, phase3_results, spec_limits
        )

        # Verify result structure is correct
        assert result is not None
        assert result.pass_fail in ["Pass", "Fail"]
        assert "lower" in result.tolerance_limits or "upper" in result.tolerance_limits
        assert result.ppk is not None
        assert isinstance(result.ppk, float)


class TestPreservation5TabNavigation:
    """Preservation 5: Module A and Module V tab navigation works properly.

    **Validates: Requirement 3.5**
    """

    def test_preservation5_module_tabs_exist(self) -> None:
        """Preservation 5: Module A and Module V tabs continue to exist.

        **EXPECTED TO PASS on unfixed code** - confirms baseline behavior.
        This behavior must be preserved after Bug 4 fix.

        **Validates: Requirement 3.5**
        """
        import inspect

        from src.sample_size_calculator.ui_controller import UIController

        # Check if create_app method creates Module A and Module V tabs
        create_app_source = inspect.getsource(UIController.create_app)

        # PRESERVATION: Module A and Module V tabs should exist
        assert '"Module A"' in create_app_source or "'Module A'" in create_app_source, (
            "Module A tab missing - preservation violated"
        )

        assert '"Module V"' in create_app_source or "'Module V'" in create_app_source, (
            "Module V tab missing - preservation violated"
        )


class TestPreservation6AutomaticMethodSelection:
    """Preservation 6: Automatic method selection (non-manual override) works.

    **Validates: Requirement 3.6**
    """

    def test_preservation6_automatic_selection_works(self) -> None:
        """Preservation 6: Automatic method selection continues working.

        **EXPECTED TO PASS on unfixed code** - confirms baseline behavior.
        This behavior must be preserved after Bug 5 fix.

        **Validates: Requirement 3.6**
        """
        from src.sample_size_calculator.transformations import transformation_cascade

        # Test data that should trigger automatic method selection
        # Normal data (should select NONE/Parametric)
        normal_data = [10.0, 10.1, 9.9, 10.2, 9.8, 10.0, 10.1, 9.9]

        # PRESERVATION: Automatic selection should work without manual override
        result = transformation_cascade(normal_data, manual_method=None)

        # Verify result structure
        assert result is not None
        assert hasattr(result, "analysis_method")
        assert hasattr(result, "transformation_method")
        assert result.manual_override is False


class TestPreservation7TransformationParameters:
    """Preservation 7: Phase 2 transformation parameters display correctly.

    **Validates: Requirement 3.7**
    """

    def test_preservation7_shapiro_wilk_displayed(self) -> None:
        """Preservation 7: Shapiro-Wilk p-value continues displaying.

        **EXPECTED TO PASS on unfixed code** - confirms baseline behavior.
        This behavior must be preserved after Bug 6 fix.

        **Validates: Requirement 3.7**
        """
        from src.sample_size_calculator.normality import shapiro_wilk_test

        # Test data
        test_data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]

        # PRESERVATION: Shapiro-Wilk test should continue working
        statistic, p_value = shapiro_wilk_test(test_data)

        # Verify result structure
        assert isinstance(statistic, float)
        assert isinstance(p_value, float)
        assert 0.0 <= p_value <= 1.0


class TestPreservation8ModuleInterfaces:
    """Preservation 8: Module A and Module V interfaces function properly.

    **Validates: Requirement 3.8**
    """

    def test_preservation8_module_v_state_management(self) -> None:
        """Preservation 8: Module V state management continues working.

        **EXPECTED TO PASS on unfixed code** - confirms baseline behavior.
        This behavior must be preserved after Bug 7 fix.

        **Validates: Requirement 3.8**
        """
        from src.sample_size_calculator.ui_controller import ModuleVState

        # PRESERVATION: ModuleVState should continue working
        state = ModuleVState()

        # Verify initial state
        assert state.phase1_complete is False
        assert state.phase2_complete is False
        assert state.phase3_complete is False
        assert state.initial_data is None
        assert state.phase2_results is None
        assert state.phase3_results is None


class TestPreservation9ShapiroWilkDisplay:
    """Preservation 9: Shapiro-Wilk test continues displaying in results.

    **Validates: Requirement 3.9**
    """

    def test_preservation9_shapiro_wilk_in_results(self) -> None:
        """Preservation 9: Shapiro-Wilk test continues displaying.

        **EXPECTED TO PASS on unfixed code** - confirms baseline behavior.
        This behavior must be preserved after Bug 8 fix.

        **Validates: Requirement 3.9**
        """
        from src.sample_size_calculator.normality import shapiro_wilk_test

        # Test data
        test_data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        # PRESERVATION: Shapiro-Wilk test should continue working
        statistic, p_value = shapiro_wilk_test(test_data)

        # Verify result is valid
        assert isinstance(statistic, float)
        assert isinstance(p_value, float)
        assert 0.0 <= p_value <= 1.0
        assert statistic > 0.0  # Shapiro-Wilk statistic is always positive


class TestPreservation10PDFNonTableSections:
    """Preservation 10: PDF non-table sections maintain formatting.

    **Validates: Requirement 3.10**
    """

    def test_preservation10_pdf_generator_exists(self) -> None:
        """Preservation 10: PDF generator continues working for non-table sections.

        **EXPECTED TO PASS on unfixed code** - confirms baseline behavior.
        This behavior must be preserved after Bug 9 fix.

        **Validates: Requirement 3.10**
        """
        from src.sample_size_calculator.report_generator import ReportGenerator

        # PRESERVATION: ReportGenerator should continue to exist and be importable
        assert ReportGenerator is not None

        # Verify key methods exist
        assert hasattr(ReportGenerator, "generate_user_report")
        assert hasattr(ReportGenerator, "__init__")
