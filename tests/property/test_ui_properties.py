"""Property-based tests for UI workflow and session isolation.

This module tests universal properties of the UI controller including:
- Property 6: Specification Validation
- Property 7: Workflow State Invalidation
- Property 33: Session Isolation
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from sample_size_calculator.models import (
    AnalysisMethod,
    Phase1Results,
    Phase2Results,
    Phase3Results,
    SpecificationLimits,
    SpecificationType,
    TransformationMethod,
)
from sample_size_calculator.ui_controller import ModuleVState


# Property 6: Specification Validation
@settings(max_examples=100)
@given(
    spec_type=st.sampled_from([SpecificationType.ONE_SIDED, SpecificationType.TWO_SIDED]),
    lsl=st.one_of(st.none(), st.floats(min_value=-1000, max_value=1000)),
    usl=st.one_of(st.none(), st.floats(min_value=-1000, max_value=1000)),
)
def test_property_6_specification_validation(
    spec_type: SpecificationType, lsl: float | None, usl: float | None
) -> None:
    """
    Feature: sample-size-calculator, Property 6: Specification Validation

    GIVEN any specification type (One-Sided or Two-Sided)
    AND any combination of LSL and USL values
    WHEN creating a SpecificationLimits object
    THEN the validation rules must be enforced:
      - One-Sided requires either LSL or USL (not both None)
      - Two-Sided requires both LSL and USL (neither None)

    This property validates Requirements 5.2, 5.3.
    """
    try:
        spec_limits = SpecificationLimits(spec_type=spec_type, lsl=lsl, usl=usl)

        # If creation succeeded, verify the constraints are met
        if spec_type == SpecificationType.ONE_SIDED:
            # One-sided must have at least one limit defined
            assert lsl is not None or usl is not None, (
                "One-sided spec should require at least one limit"
            )
        elif spec_type == SpecificationType.TWO_SIDED:
            # Two-sided must have both limits defined
            assert lsl is not None and usl is not None, (
                "Two-sided spec should require both limits"
            )

        # Verify the values are stored correctly
        assert spec_limits.spec_type == spec_type
        assert spec_limits.lsl == lsl
        assert spec_limits.usl == usl

    except ValueError as e:
        # If validation failed, verify it failed for the right reason
        error_msg = str(e)

        if spec_type == SpecificationType.ONE_SIDED:
            # Should only fail if both limits are None
            assert lsl is None and usl is None, (
                f"One-sided validation should only fail when both limits are None, "
                f"but got lsl={lsl}, usl={usl}, error={error_msg}"
            )
        elif spec_type == SpecificationType.TWO_SIDED:
            # Should fail if either limit is None
            assert lsl is None or usl is None, (
                f"Two-sided validation should fail when any limit is None, "
                f"but got lsl={lsl}, usl={usl}, error={error_msg}"
            )


# Property 7: Workflow State Invalidation
@settings(max_examples=100)
@given(
    pilot_data=st.lists(
        st.floats(min_value=0.1, max_value=100.0), min_size=3, max_size=50
    ),
    shapiro_p=st.floats(min_value=0.0, max_value=1.0),
    k_margin=st.floats(min_value=0.1, max_value=10.0),
    required_n=st.integers(min_value=3, max_value=100),
)
def test_property_7_workflow_state_invalidation(
    pilot_data: list[float],
    shapiro_p: float,
    k_margin: float,
    required_n: int,
) -> None:
    """
    Feature: sample-size-calculator, Property 7: Workflow State Invalidation

    GIVEN a Module V workflow state with completed phases
    WHEN an upstream phase is modified or re-executed
    THEN all downstream phase results must be cleared
    AND downstream phases must be disabled until re-completed

    This property validates Requirements 5.5, 24.5.

    Workflow invalidation rules:
    - Modifying Phase 1 clears Phases 2, 3, 4
    - Modifying Phase 2 clears Phases 3, 4
    - Modifying Phase 3 clears Phase 4
    """
    state = ModuleVState()

    # Create mock results for all phases
    phase1_results = Phase1Results(
        pilot_data=pilot_data, outliers=[], q1=10.0, q3=20.0, iqr=10.0
    )

    phase2_results = Phase2Results(
        cleaned_data=pilot_data,
        shapiro_p_value=shapiro_p,
        transformation_method=TransformationMethod.NONE,
        analysis_method=AnalysisMethod.PARAMETRIC,
        lambda_param=None,
        manual_override=False,
    )

    phase3_results = Phase3Results(
        required_sample_size=required_n,
        k_margin=k_margin,
        k_factor=2.5,
        specification_type=SpecificationType.TWO_SIDED,
    )

    # Complete all phases
    state.complete_phase1(phase1_results)
    assert state.phase1_complete
    assert state.phase1_results is not None

    state.complete_phase2(phase2_results)
    assert state.phase2_complete
    assert state.phase2_results is not None

    state.complete_phase3(phase3_results)
    assert state.phase3_complete
    assert state.phase3_results is not None

    # Test 1: Re-completing Phase 1 should clear Phases 2, 3, 4
    state.complete_phase1(phase1_results)
    assert state.phase1_complete, "Phase 1 should remain complete"
    assert not state.phase2_complete, "Phase 2 should be cleared"
    assert not state.phase3_complete, "Phase 3 should be cleared"
    assert not state.phase4_complete, "Phase 4 should be cleared"
    assert state.phase2_results is None, "Phase 2 results should be cleared"
    assert state.phase3_results is None, "Phase 3 results should be cleared"
    assert state.phase4_results is None, "Phase 4 results should be cleared"

    # Re-complete phases 2 and 3
    state.complete_phase2(phase2_results)
    state.complete_phase3(phase3_results)

    # Test 2: Re-completing Phase 2 should clear Phases 3, 4
    state.complete_phase2(phase2_results)
    assert state.phase1_complete, "Phase 1 should remain complete"
    assert state.phase2_complete, "Phase 2 should remain complete"
    assert not state.phase3_complete, "Phase 3 should be cleared"
    assert not state.phase4_complete, "Phase 4 should be cleared"
    assert state.phase3_results is None, "Phase 3 results should be cleared"
    assert state.phase4_results is None, "Phase 4 results should be cleared"

    # Re-complete phase 3
    state.complete_phase3(phase3_results)

    # Test 3: Re-completing Phase 3 should clear Phase 4 only
    state.complete_phase3(phase3_results)
    assert state.phase1_complete, "Phase 1 should remain complete"
    assert state.phase2_complete, "Phase 2 should remain complete"
    assert state.phase3_complete, "Phase 3 should remain complete"
    assert not state.phase4_complete, "Phase 4 should be cleared"
    assert state.phase4_results is None, "Phase 4 results should be cleared"

    # Test 4: Verify phase enablement follows completion status
    assert state.is_phase_enabled(1), "Phase 1 should always be enabled"
    assert state.is_phase_enabled(2), "Phase 2 should be enabled after Phase 1"
    assert state.is_phase_enabled(3), "Phase 3 should be enabled after Phase 2"
    assert state.is_phase_enabled(4), "Phase 4 should be enabled after Phase 3"

    # Test 5: Clearing Phase 1 should disable all downstream phases
    state.phase1_complete = False
    assert not state.is_phase_enabled(2), "Phase 2 should be disabled"
    assert not state.is_phase_enabled(3), "Phase 3 should be disabled"
    assert not state.is_phase_enabled(4), "Phase 4 should be disabled"


# Property 33: Session Isolation
@settings(max_examples=50)
@given(
    num_sessions=st.integers(min_value=2, max_value=10),
)
def test_property_33_session_isolation(num_sessions: int) -> None:
    """
    Feature: sample-size-calculator, Property 33: Session Isolation

    GIVEN multiple concurrent user sessions
    WHEN each session has its own ModuleVState instance
    THEN state changes in one session must not affect other sessions
    AND each session must have a unique session identifier

    This property validates Requirement 36.5.

    Session isolation ensures:
    - Each user has independent workflow state
    - Calculations in one session don't interfere with others
    - Session IDs are unique across all sessions
    """
    from sample_size_calculator.ui_controller import UIController

    # Create multiple UI controller instances (simulating concurrent sessions)
    controllers = [UIController() for _ in range(num_sessions)]

    # Verify all session IDs are unique
    session_ids = [controller.session_id for controller in controllers]
    assert len(session_ids) == len(set(session_ids)), (
        "All session IDs must be unique"
    )

    # Verify each session has independent state
    for controller in controllers:
        assert controller.module_v_state is not None
        assert not controller.module_v_state.phase1_complete
        assert controller.module_v_state.phase1_results is None

    # Modify state in first session
    pilot_data = [10.0, 12.0, 11.0, 13.0, 12.5]
    phase1_results = Phase1Results(
        pilot_data=pilot_data, outliers=[], q1=10.0, q3=13.0, iqr=3.0
    )
    controllers[0].module_v_state.complete_phase1(phase1_results)

    # Verify first session is modified
    assert controllers[0].module_v_state.phase1_complete
    assert controllers[0].module_v_state.phase1_results is not None

    # Verify other sessions are unaffected
    for i in range(1, num_sessions):
        assert not controllers[i].module_v_state.phase1_complete, (
            f"Session {i} should not be affected by session 0"
        )
        assert controllers[i].module_v_state.phase1_results is None, (
            f"Session {i} should have no phase 1 results"
        )

    # Modify state in another session
    if num_sessions > 1:
        phase2_results = Phase2Results(
            cleaned_data=pilot_data,
            shapiro_p_value=0.8,
            transformation_method=TransformationMethod.LOGARITHMIC,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=None,
            manual_override=False,
        )
        controllers[1].module_v_state.complete_phase1(phase1_results)
        controllers[1].module_v_state.complete_phase2(phase2_results)

        # Verify session 1 has both phases complete
        assert controllers[1].module_v_state.phase1_complete
        assert controllers[1].module_v_state.phase2_complete

        # Verify session 0 only has phase 1 complete
        assert controllers[0].module_v_state.phase1_complete
        assert not controllers[0].module_v_state.phase2_complete

        # Verify other sessions are still unaffected
        for i in range(2, num_sessions):
            assert not controllers[i].module_v_state.phase1_complete
            assert not controllers[i].module_v_state.phase2_complete

    # Verify session IDs remain unique and unchanged
    final_session_ids = [controller.session_id for controller in controllers]
    assert session_ids == final_session_ids, "Session IDs should not change"
    assert len(set(final_session_ids)) == num_sessions, (
        "All session IDs must remain unique"
    )
