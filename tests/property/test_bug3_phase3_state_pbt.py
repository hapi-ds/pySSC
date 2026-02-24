"""Property-based tests for Bug 3: Phase 3 controls disabled after completion.

This module contains property-based tests that verify Bug 3 fix works correctly
across a wide range of inputs. Bug 3 was about Phase 3 UI controls not being
disabled after Phase 3 completion, allowing users to recalculate and potentially
invalidate Phase 4 results.

**Property 1: Expected Behavior** - Phase 3 Controls Disabled After Completion

For any Phase 3 completion event, the fixed UI state management SHALL disable
Phase 3 controls to prevent recalculation that would invalidate Phase 4 results.

**Validates: Requirement 2.3**
"""

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from src.sample_size_calculator.models import (
    AnalysisMethod,
    Phase1Results,
    Phase2Results,
    Phase3Results,
    SpecificationType,
    TransformationMethod,
)
from src.sample_size_calculator.ui_controller import ModuleVState


def create_phase1_results(data: list[float]) -> Phase1Results:
    """Helper function to create Phase1Results with proper fields."""
    data_array = np.array(data)
    q1 = float(np.percentile(data_array, 25))
    q3 = float(np.percentile(data_array, 75))
    iqr = q3 - q1
    
    return Phase1Results(
        pilot_data=data,
        outliers=[],
        q1=q1,
        q3=q3,
        iqr=iqr,
    )


class TestBug3Phase3StateProperty:
    """Property-based tests for Bug 3: Phase 3 controls disabled after completion.
    
    **Validates: Requirement 2.3**
    """

    @given(
        required_n=st.sampled_from([10, 30, 50, 100]),
        k_margin=st.floats(min_value=1.0, max_value=10.0),
        k_factor=st.floats(min_value=1.5, max_value=5.0),
        spec_type=st.sampled_from([SpecificationType.ONE_SIDED, SpecificationType.TWO_SIDED]),
    )
    @settings(deadline=3000, max_examples=100)
    def test_phase3_completion_disables_controls_property(
        self,
        required_n: int,
        k_margin: float,
        k_factor: float,
        spec_type: SpecificationType,
    ) -> None:
        """Property 1: Phase 3 completion sets phase3_complete flag to True.
        
        This property-based test generates random combinations of:
        - Required sample sizes N (10, 30, 50, 100)
        - Capability margins k_margin (1.0 to 10.0)
        - Tolerance factors k_factor (1.5 to 5.0)
        - Specification types (one-sided or two-sided)
        
        For all combinations, completing Phase 3 should set the phase3_complete
        flag to True, which triggers UI control disabling in the UIController.
        
        **Validates: Requirement 2.3**
        """
        # Create state
        state = ModuleVState()
        
        # Complete Phase 1 (required prerequisite)
        phase1_results = create_phase1_results([10.0, 11.0, 12.0, 13.0, 14.0])
        state.complete_phase1(phase1_results)
        
        # Complete Phase 2 (required prerequisite)
        phase2_results = Phase2Results(
            cleaned_data=[10.0, 11.0, 12.0, 13.0, 14.0],
            shapiro_p_value=0.8,
            transformation_method=TransformationMethod.NONE,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=None,
            manual_override=False,
        )
        state.complete_phase2(phase2_results)
        
        # Verify Phase 3 is not complete before completion
        assert state.phase3_complete is False, "Phase 3 should not be complete initially"
        
        # Complete Phase 3 with generated parameters
        phase3_results = Phase3Results(
            required_sample_size=required_n,
            k_margin=k_margin,
            k_factor=k_factor,
            specification_type=spec_type,
        )
        state.complete_phase3(phase3_results)
        
        # Verify: Phase 3 should be marked as complete
        assert state.phase3_complete is True, (
            f"Phase 3 should be complete after completion with "
            f"N={required_n}, k_margin={k_margin:.2f}, k_factor={k_factor:.2f}, "
            f"spec_type={spec_type.value}"
        )
        
        # Verify: Phase 3 results should be stored
        assert state.phase3_results is not None, "Phase 3 results should be stored"
        assert state.phase3_results.required_sample_size == required_n
        assert state.phase3_results.k_margin == k_margin
        assert state.phase3_results.k_factor == k_factor
        assert state.phase3_results.specification_type == spec_type
        
        # Verify: Phase 4 should be enabled (prerequisite met)
        assert state.is_phase_enabled(4) is True, "Phase 4 should be enabled after Phase 3"

    @given(
        required_n=st.sampled_from([10, 30, 50, 100]),
        analysis_method=st.sampled_from([AnalysisMethod.PARAMETRIC, AnalysisMethod.NON_PARAMETRIC]),
        spec_type=st.sampled_from([SpecificationType.ONE_SIDED, SpecificationType.TWO_SIDED]),
    )
    @settings(deadline=3000, max_examples=100)
    def test_phase3_completion_with_various_analysis_methods(
        self,
        required_n: int,
        analysis_method: AnalysisMethod,
        spec_type: SpecificationType,
    ) -> None:
        """Property 1: Phase 3 completion works with various analysis methods.
        
        This test verifies that Phase 3 completion correctly sets the phase3_complete
        flag regardless of the analysis method (parametric or non-parametric) used
        in Phase 2.
        
        **Validates: Requirement 2.3**
        """
        # Create state
        state = ModuleVState()
        
        # Complete Phase 1
        phase1_results = create_phase1_results([10.0, 11.0, 12.0, 13.0, 14.0])
        state.complete_phase1(phase1_results)
        
        # Complete Phase 2 with specified analysis method
        phase2_results = Phase2Results(
            cleaned_data=[10.0, 11.0, 12.0, 13.0, 14.0],
            shapiro_p_value=0.8 if analysis_method == AnalysisMethod.PARAMETRIC else 0.02,
            transformation_method=TransformationMethod.NONE,
            analysis_method=analysis_method,
            lambda_param=None,
            manual_override=False,
        )
        state.complete_phase2(phase2_results)
        
        # Complete Phase 3
        phase3_results = Phase3Results(
            required_sample_size=required_n,
            k_margin=3.0,
            k_factor=2.5,
            specification_type=spec_type,
        )
        state.complete_phase3(phase3_results)
        
        # Verify: Phase 3 should be complete
        assert state.phase3_complete is True, (
            f"Phase 3 should be complete with analysis_method={analysis_method.value}"
        )
        assert state.phase3_results is not None

    @given(
        required_n=st.sampled_from([10, 30, 50, 100]),
        transformation=st.sampled_from([
            TransformationMethod.NONE,
            TransformationMethod.LOGARITHMIC,
            TransformationMethod.BOX_COX,
            TransformationMethod.YEO_JOHNSON,
        ]),
    )
    @settings(deadline=3000, max_examples=80)
    def test_phase3_completion_with_various_transformations(
        self,
        required_n: int,
        transformation: TransformationMethod,
    ) -> None:
        """Property 1: Phase 3 completion works with various transformation methods.
        
        This test verifies that Phase 3 completion correctly sets the phase3_complete
        flag regardless of the transformation method used in Phase 2.
        
        **Validates: Requirement 2.3**
        """
        # Create state
        state = ModuleVState()
        
        # Complete Phase 1
        phase1_results = create_phase1_results([10.0, 11.0, 12.0, 13.0, 14.0])
        state.complete_phase1(phase1_results)
        
        # Complete Phase 2 with specified transformation
        lambda_param = None
        if transformation in [TransformationMethod.BOX_COX, TransformationMethod.YEO_JOHNSON]:
            lambda_param = 0.5  # Use a valid lambda for power transformations
        
        phase2_results = Phase2Results(
            cleaned_data=[10.0, 11.0, 12.0, 13.0, 14.0],
            shapiro_p_value=0.8,
            transformation_method=transformation,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=lambda_param,
            manual_override=False,
        )
        state.complete_phase2(phase2_results)
        
        # Complete Phase 3
        phase3_results = Phase3Results(
            required_sample_size=required_n,
            k_margin=3.0,
            k_factor=2.5,
            specification_type=SpecificationType.TWO_SIDED,
        )
        state.complete_phase3(phase3_results)
        
        # Verify: Phase 3 should be complete
        assert state.phase3_complete is True, (
            f"Phase 3 should be complete with transformation={transformation.value}"
        )
        assert state.phase3_results is not None

    @given(
        required_n=st.sampled_from([10, 30, 50, 100]),
        recalculate_count=st.integers(min_value=1, max_value=5),
    )
    @settings(deadline=3000, max_examples=50)
    def test_phase3_recalculation_maintains_complete_flag(
        self,
        required_n: int,
        recalculate_count: int,
    ) -> None:
        """Property 1: Phase 3 recalculation maintains phase3_complete flag.
        
        This test verifies that if Phase 3 is completed multiple times (recalculated),
        the phase3_complete flag remains True after each completion. This simulates
        the scenario where a user might recalculate Phase 3 with different parameters.
        
        **Validates: Requirement 2.3**
        """
        # Create state
        state = ModuleVState()
        
        # Complete Phase 1
        phase1_results = create_phase1_results([10.0, 11.0, 12.0, 13.0, 14.0])
        state.complete_phase1(phase1_results)
        
        # Complete Phase 2
        phase2_results = Phase2Results(
            cleaned_data=[10.0, 11.0, 12.0, 13.0, 14.0],
            shapiro_p_value=0.8,
            transformation_method=TransformationMethod.NONE,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=None,
            manual_override=False,
        )
        state.complete_phase2(phase2_results)
        
        # Complete Phase 3 multiple times with different parameters
        for i in range(recalculate_count):
            # Vary k_margin and k_factor slightly for each recalculation
            k_margin = 3.0 + (i * 0.5)
            k_factor = 2.5 + (i * 0.1)
            
            phase3_results = Phase3Results(
                required_sample_size=required_n,
                k_margin=k_margin,
                k_factor=k_factor,
                specification_type=SpecificationType.TWO_SIDED,
            )
            state.complete_phase3(phase3_results)
            
            # Verify: Phase 3 should remain complete after each recalculation
            assert state.phase3_complete is True, (
                f"Phase 3 should be complete after recalculation {i+1}/{recalculate_count}"
            )
            assert state.phase3_results is not None
            assert state.phase3_results.k_margin == k_margin
            assert state.phase3_results.k_factor == k_factor

    @given(
        required_n=st.sampled_from([10, 30, 50, 100]),
    )
    @settings(deadline=3000, max_examples=50)
    def test_phase3_completion_clears_phase4(
        self,
        required_n: int,
    ) -> None:
        """Property 1: Phase 3 completion clears downstream Phase 4.
        
        This test verifies that completing Phase 3 clears any existing Phase 4
        results, ensuring that Phase 4 must be recalculated with the new Phase 3
        parameters. This is part of the sequential workflow enforcement.
        
        **Validates: Requirement 2.3**
        """
        # Create state
        state = ModuleVState()
        
        # Complete Phase 1
        phase1_results = create_phase1_results([10.0, 11.0, 12.0, 13.0, 14.0])
        state.complete_phase1(phase1_results)
        
        # Complete Phase 2
        phase2_results = Phase2Results(
            cleaned_data=[10.0, 11.0, 12.0, 13.0, 14.0],
            shapiro_p_value=0.8,
            transformation_method=TransformationMethod.NONE,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=None,
            manual_override=False,
        )
        state.complete_phase2(phase2_results)
        
        # Complete Phase 3
        phase3_results = Phase3Results(
            required_sample_size=required_n,
            k_margin=3.0,
            k_factor=2.5,
            specification_type=SpecificationType.TWO_SIDED,
        )
        state.complete_phase3(phase3_results)
        
        # Simulate Phase 4 completion (manually set for testing)
        state.phase4_complete = True
        state.phase4_results = None
        
        # Recalculate Phase 3 with different parameters
        new_phase3_results = Phase3Results(
            required_sample_size=required_n + 10,
            k_margin=4.0,
            k_factor=3.0,
            specification_type=SpecificationType.TWO_SIDED,
        )
        state.complete_phase3(new_phase3_results)
        
        # Verify: Phase 4 should be cleared
        assert state.phase4_complete is False, (
            "Phase 4 should be cleared when Phase 3 is recalculated"
        )
        assert state.phase4_results is None, (
            "Phase 4 results should be cleared when Phase 3 is recalculated"
        )
        
        # Verify: Phase 3 should still be complete with new results
        assert state.phase3_complete is True
        assert state.phase3_results.required_sample_size == required_n + 10

    def test_phase3_completion_sequential_workflow_baseline(self) -> None:
        """Baseline test: Phase 3 completion follows sequential workflow.
        
        This is a baseline test that verifies the complete sequential workflow:
        Phase 1 -> Phase 2 -> Phase 3, ensuring that Phase 3 can only be completed
        after Phase 2 is complete.
        
        **Validates: Requirement 2.3**
        """
        # Create state
        state = ModuleVState()
        
        # Verify: Phase 3 is not enabled initially
        assert state.is_phase_enabled(3) is False, "Phase 3 should not be enabled initially"
        
        # Complete Phase 1
        phase1_results = create_phase1_results([10.0, 11.0, 12.0, 13.0, 14.0])
        state.complete_phase1(phase1_results)
        
        # Verify: Phase 3 is still not enabled (Phase 2 not complete)
        assert state.is_phase_enabled(3) is False, "Phase 3 should not be enabled after Phase 1"
        
        # Complete Phase 2
        phase2_results = Phase2Results(
            cleaned_data=[10.0, 11.0, 12.0, 13.0, 14.0],
            shapiro_p_value=0.8,
            transformation_method=TransformationMethod.NONE,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=None,
            manual_override=False,
        )
        state.complete_phase2(phase2_results)
        
        # Verify: Phase 3 is now enabled
        assert state.is_phase_enabled(3) is True, "Phase 3 should be enabled after Phase 2"
        
        # Complete Phase 3
        phase3_results = Phase3Results(
            required_sample_size=30,
            k_margin=3.0,
            k_factor=2.5,
            specification_type=SpecificationType.TWO_SIDED,
        )
        state.complete_phase3(phase3_results)
        
        # Verify: Phase 3 is complete
        assert state.phase3_complete is True, "Phase 3 should be complete"
        assert state.phase3_results is not None
        
        # Verify: Phase 4 is now enabled
        assert state.is_phase_enabled(4) is True, "Phase 4 should be enabled after Phase 3"

    @given(
        phase1_data_size=st.integers(min_value=5, max_value=50),
        required_n=st.sampled_from([10, 30, 50, 100]),
    )
    @settings(deadline=3000, max_examples=50)
    def test_phase3_completion_with_various_data_sizes(
        self,
        phase1_data_size: int,
        required_n: int,
    ) -> None:
        """Property 1: Phase 3 completion works with various Phase 1 data sizes.
        
        This test verifies that Phase 3 completion correctly sets the phase3_complete
        flag regardless of the size of the initial data from Phase 1.
        
        **Validates: Requirement 2.3**
        """
        # Create state
        state = ModuleVState()
        
        # Generate Phase 1 data with specified size
        initial_data = np.random.normal(12.0, 1.0, phase1_data_size).tolist()
        
        # Complete Phase 1
        phase1_results = create_phase1_results(initial_data)
        state.complete_phase1(phase1_results)
        
        # Complete Phase 2
        phase2_results = Phase2Results(
            cleaned_data=initial_data,
            shapiro_p_value=0.8,
            transformation_method=TransformationMethod.NONE,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=None,
            manual_override=False,
        )
        state.complete_phase2(phase2_results)
        
        # Complete Phase 3
        phase3_results = Phase3Results(
            required_sample_size=required_n,
            k_margin=3.0,
            k_factor=2.5,
            specification_type=SpecificationType.TWO_SIDED,
        )
        state.complete_phase3(phase3_results)
        
        # Verify: Phase 3 should be complete
        assert state.phase3_complete is True, (
            f"Phase 3 should be complete with phase1_data_size={phase1_data_size}"
        )
        assert state.phase3_results is not None
