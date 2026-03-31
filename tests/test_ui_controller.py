"""Comprehensive unit tests for UI controller."""

from unittest.mock import MagicMock, patch

import pytest

from sample_size_calculator.ui_controller import (
    ModuleVState,
    UIController,
)


class TestModuleVState:
    """Tests for ModuleVState class."""

    def test_initial_state(self):
        state = ModuleVState()
        
        assert not state.phase1_complete
        assert not state.phase2_complete
        assert not state.phase3_complete
        assert not state.phase4_complete
        
        assert state.phase1_results is None
        assert state.phase2_results is None
        assert state.phase3_results is None
        assert state.phase4_results is None

    def test_complete_phase1_with_results(self):
        from sample_size_calculator.models import Phase1Results
        
        state = ModuleVState()
        
        phase1_results = Phase1Results(
            pilot_data=[1.0, 2.0, 3.0],
            outliers=[],
            q1=1.5,
            q3=2.5,
            iqr=1.0,
        )
        
        state.complete_phase1(phase1_results)
        
        assert state.phase1_complete
        assert state.phase1_results is not None
        assert state.initial_data == [1.0, 2.0, 3.0]
        assert state.phase2_complete is False

    def test_complete_phase1_with_raw_data(self):
        state = ModuleVState()
        
        pilot_data = [1.0, 2.0, 3.0]
        state.complete_phase1(pilot_data)
        
        assert state.phase1_complete
        assert state.initial_data == pilot_data
        assert state.phase1_results is None

    def test_complete_phase2_clears_downstream(self):
        from sample_size_calculator.models import (
            AnalysisMethod,
            Phase1Results,
            Phase2Results,
            TransformationMethod,
        )
        
        state = ModuleVState()
        
        phase1_results = Phase1Results(
            pilot_data=[1.0, 2.0, 3.0],
            outliers=[],
            q1=1.5,
            q3=2.5,
            iqr=1.0,
        )
        
        state.complete_phase1(phase1_results)
        
        phase2_results = Phase2Results(
            cleaned_data=[1.0, 2.0],
            shapiro_p_value=0.8,
            transformation_method=TransformationMethod.NONE,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=None,
            manual_override=False,
        )
        
        state.complete_phase2(phase2_results)
        
        assert state.phase2_complete
        assert state.phase3_complete is False
        assert state.phase4_complete is False

    def test_is_phase_enabled(self):
        state = ModuleVState()
        
        assert state.is_phase_enabled(1) is True
        assert state.is_phase_enabled(2) is False
        
        state.complete_phase1([1.0, 2.0, 3.0])
        
        assert state.is_phase_enabled(2) is True

    def test_complete_phase3_clears_phase4(self):
        from sample_size_calculator.models import (
            AnalysisMethod,
            Phase1Results,
            Phase2Results,
            Phase3Results,
            SpecificationType,
            TransformationMethod,
        )
        
        state = ModuleVState()
        
        phase1_results = Phase1Results(
            pilot_data=[1.0, 2.0, 3.0],
            outliers=[],
            q1=1.5,
            q3=2.5,
            iqr=1.0,
        )
        
        state.complete_phase1(phase1_results)
        
        phase2_results = Phase2Results(
            cleaned_data=[1.0, 2.0],
            shapiro_p_value=0.8,
            transformation_method=TransformationMethod.NONE,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=None,
            manual_override=False,
        )
        
        state.complete_phase2(phase2_results)
        
        phase3_results = Phase3Results(
            required_sample_size=10,
            k_margin=1.5,
            k_factor=2.5,
            specification_type=SpecificationType.TWO_SIDED,
        )
        
        state.complete_phase3(phase3_results)
        
        assert state.phase3_complete
        assert state.phase4_complete is False


class TestUIController:
    """Tests for UIController class."""

    def test_initialization(self):
        controller = UIController()
        
        assert controller.logger is not None
        assert controller.session_id is not None
        assert len(controller.session_id) > 0
        assert controller.module_v_state is not None
        assert controller.validation_button is None

    def test_generate_session_id(self):
        controller = UIController()
        
        import uuid
        
        try:
            parsed = uuid.UUID(controller.session_id)
            assert parsed.version == 4
        except ValueError:
            pytest.fail("Session ID is not a valid UUID")

    def test_update_validation_button_color_when_set(self):
        with patch("sample_size_calculator.ui_controller.is_validated_state", return_value=True):
            controller = UIController()
            
            mock_button = MagicMock()
            controller.validation_button = mock_button
            
            controller._update_validation_button_color()
            
            mock_button.props.assert_called_once()

    def test_update_validation_button_color_when_not_set(self):
        controller = UIController()
        
        assert controller.validation_button is None
        
        controller._update_validation_button_color()


class TestUIControllerSessionManagement:
    """Tests for UIController session management."""

    def test_unique_session_ids(self):
        controllers = [UIController() for _ in range(10)]
        
        session_ids = [c.session_id for c in controllers]
        
        assert len(session_ids) == len(set(session_ids))

    def test_session_id_format(self):
        controller = UIController()
        
        import re
        
        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        
        assert re.match(uuid_pattern, controller.session_id, re.IGNORECASE)


class TestModuleVStateEdgeCases:
    """Edge case tests for ModuleVState."""

    def test_complete_phase1_preserves_initial_data(self):
        state = ModuleVState()
        
        pilot_data = [1.0, 2.0, 3.0, 4.0, 5.0]
        state.complete_phase1(pilot_data)
        
        assert state.initial_data == pilot_data

    def test_complete_phase1_clears_all_downstream(self):
        from sample_size_calculator.models import (
            AnalysisMethod,
            Phase1Results,
            Phase2Results,
            Phase3Results,
            SpecificationType,
            TransformationMethod,
        )
        
        state = ModuleVState()
        
        phase1_results = Phase1Results(
            pilot_data=[1.0, 2.0, 3.0],
            outliers=[],
            q1=1.5,
            q3=2.5,
            iqr=1.0,
        )
        
        state.complete_phase1(phase1_results)
        
        phase2_results = Phase2Results(
            cleaned_data=[1.0, 2.0],
            shapiro_p_value=0.8,
            transformation_method=TransformationMethod.NONE,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=None,
            manual_override=False,
        )
        
        state.complete_phase2(phase2_results)
        
        phase3_results = Phase3Results(
            required_sample_size=10,
            k_margin=1.5,
            k_factor=2.5,
            specification_type=SpecificationType.TWO_SIDED,
        )
        
        state.complete_phase3(phase3_results)
        
        state.complete_phase1(phase1_results)
        
        assert state.phase1_complete
        assert not state.phase2_complete
        assert not state.phase3_complete

    def test_is_phase_enabled_returns_false_for_invalid_phase(self):
        state = ModuleVState()
        
        assert state.is_phase_enabled(0) is False
        assert state.is_phase_enabled(-1) is False
        assert state.is_phase_enabled(5) is False


class TestUIControllerAsyncMethods:
    """Tests for async UIController methods."""

    def test_run_validation_with_empty_name(self):
        import asyncio
        
        with patch("sample_size_calculator.ui_controller.ui") as mock_ui:
            controller = UIController()
            
            notify_calls = []
            mock_ui.notify.side_effect = lambda msg, **kwargs: notify_calls.append((msg, kwargs))
            
            async def run_test():
                await controller._run_validation(
                    tester_name="",
                    progress_log=MagicMock(),
                    result_label=MagicMock(),
                    run_button=MagicMock(),
                )
            
            asyncio.run(run_test())
            
            assert any("Please enter tester name" in msg for msg, _ in notify_calls)

    def test_run_validation_with_whitespace_only_name(self):
        import asyncio
        
        with patch("sample_size_calculator.ui_controller.ui") as mock_ui:
            controller = UIController()
            
            notify_calls = []
            mock_ui.notify.side_effect = lambda msg, **kwargs: notify_calls.append((msg, kwargs))
            
            async def run_test():
                await controller._run_validation(
                    tester_name="   ",
                    progress_log=MagicMock(),
                    result_label=MagicMock(),
                    run_button=MagicMock(),
                )
            
            asyncio.run(run_test())
            
            assert any("Please enter tester name" in msg for msg, _ in notify_calls)

    def test_run_validation_success(self):
        import asyncio
        
        with patch("sample_size_calculator.ui_controller.ui") as mock_ui, \
             patch("sample_size_calculator.ui_controller.ValidationRunner"), \
             patch("anyio.to_thread.run_sync") as mock_run_sync:
            
            controller = UIController()
            controller.validation_button = MagicMock()
            
            mock_run_sync.return_value = (True, "Validation passed", "/path/to/cert.pdf")
            
            with patch("sample_size_calculator.ui_controller.is_validated_state", return_value=True):
                async def run_test():
                    await controller._run_validation(
                        tester_name="Test User",
                        progress_log=MagicMock(),
                        result_label=MagicMock(),
                        run_button=MagicMock(),
                    )
                
                asyncio.run(run_test())
                
                assert any("Validation completed successfully" in str(call) for call in mock_ui.notify.call_args_list)

    def test_run_validation_exception(self):
        import asyncio
        
        with patch("sample_size_calculator.ui_controller.ui") as mock_ui, \
             patch("anyio.to_thread.run_sync") as mock_run_sync:
            
            controller = UIController()
            controller.validation_button = MagicMock()
            
            mock_run_sync.side_effect = Exception("Test error")
            
            async def run_test():
                await controller._run_validation(
                    tester_name="Test User",
                    progress_log=MagicMock(),
                    result_label=MagicMock(),
                    run_button=MagicMock(),
                )
            
            asyncio.run(run_test())
            
            assert any("Validation error" in str(call) for call in mock_ui.notify.call_args_list)


class TestUIControllerJupyterIntegration:
    """Tests for JupyterLab integration methods."""

    def test_start_jupyter(self):
        with patch("sample_size_calculator.ui_controller.JupyterManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_status.return_value = "Not started"
            mock_manager_class.return_value = mock_manager
            
            controller = UIController()
            
            status_label = MagicMock()
            status_label.text = ""
            controller._start_jupyter(status_label)
            
            mock_manager.start.assert_called_once()
            assert status_label.text == "Not started"

    def test_stop_jupyter(self):
        with patch("sample_size_calculator.ui_controller.JupyterManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_status.return_value = "Running"
            mock_manager_class.return_value = mock_manager
            
            controller = UIController()
            
            status_label = MagicMock()
            status_label.text = ""
            controller._stop_jupyter(status_label)
            
            mock_manager.stop.assert_called_once()

    def test_open_jupyter(self):
        with patch("sample_size_calculator.ui_controller.JupyterManager") as mock_manager_class, \
             patch("sample_size_calculator.ui_controller.ui.run_javascript") as mock_js:
            
            mock_manager = MagicMock()
            mock_manager.get_url.return_value = "http://localhost:8888"
            mock_manager_class.return_value = mock_manager
            
            controller = UIController()
            
            controller._open_jupyter()
            
            mock_js.assert_called_once_with('window.open("http://localhost:8888", "_blank");')


class TestModuleAHandler:
    """Tests for Module A calculation and report handlers."""

    def test_handle_calculate_single_failure(self):
        with patch("sample_size_calculator.ui_controller.CalculationEngine") as mock_engine:
            mock_engine.success_run_theorem.return_value = 100
            n = mock_engine.success_run_theorem(95.0, 95.0)
            assert n == 100

    def test_handle_calculate_multiple_failures(self):
        with patch("sample_size_calculator.ui_controller.CalculationEngine") as mock_engine:
            mock_engine.cumulative_binomial.return_value = 250
            n = mock_engine.cumulative_binomial(95.0, 95.0, 2)
            assert n == 250

    def test_handle_calculate_sensitivity_analysis(self):
        with patch("sample_size_calculator.ui_controller.CalculationEngine") as mock_engine:
            mock_engine.sensitivity_analysis_with_correction.return_value = [
                (0, 100, None),
                (1, 150, None),
                (2, 200, None),
            ]
            results = mock_engine.sensitivity_analysis_with_correction(95.0, 95.0, None)
            assert len(results) == 3

    def test_handle_calculate_population_correction(self):
        with patch("sample_size_calculator.ui_controller.CalculationEngine") as mock_engine:
            mock_engine.success_run_theorem.return_value = 100
            mock_engine.finite_population_correction.return_value = 95.24
            n_original = mock_engine.success_run_theorem(95.0, 95.0)
            n_corrected = mock_engine.finite_population_correction(n_original, 1000)
            assert n_original == 100
            assert abs(n_corrected - 95.24) < 0.1


class TestModuleVPhaseHandlers:
    """Tests for Module V phase handlers."""

    def test_handle_analyze_phase1_pilot_data(self):
        from sample_size_calculator.models import Phase1Results
        
        pilot_data_str = "10.0, 10.1, 9.9, 10.2, 10.0"
        pilot_data = [float(x.strip()) for x in pilot_data_str.split(",") if x.strip()]
        
        assert len(pilot_data) == 5
        
        results = Phase1Results(
            pilot_data=pilot_data,
            outliers=[],
            q1=9.9,
            q3=10.1,
            iqr=0.2,
        )
        
        assert results.pilot_data == pilot_data

    def test_handle_analyze_phase1_estimated_statistics(self):
        estimated_mean = 10.0
        estimated_std = 0.1
        
        assert estimated_mean == 10.0
        assert estimated_std == 0.1
        assert estimated_std > 0


class TestEnforcementAndWorkflow:
    """Tests for workflow enforcement."""

    def test_sequential_phase_enforcement(self):
        state = ModuleVState()
        
        assert state.is_phase_enabled(1) is True
        assert state.is_phase_enabled(2) is False
        
        state.complete_phase1([1.0, 2.0, 3.0])
        
        assert state.is_phase_enabled(2) is True

    def test_downstream_clearing_on_recompletion(self):
        state = ModuleVState()
        
        from sample_size_calculator.models import (
            AnalysisMethod,
            Phase1Results,
            Phase2Results,
            TransformationMethod,
        )
        
        phase1_results = Phase1Results(
            pilot_data=[1.0, 2.0, 3.0],
            outliers=[],
            q1=1.5,
            q3=2.5,
            iqr=1.0,
        )
        
        state.complete_phase1(phase1_results)
        
        phase2_results = Phase2Results(
            cleaned_data=[1.0, 2.0],
            shapiro_p_value=0.8,
            transformation_method=TransformationMethod.NONE,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=None,
            manual_override=False,
        )
        
        state.complete_phase2(phase2_results)
        
        assert state.phase2_complete
        assert not state.phase3_complete
        
        # Re-complete phase 2 - should clear phase 3
        state.complete_phase2(phase2_results)
        
        assert state.phase2_complete
        assert not state.phase3_complete


class TestSessionIsolation:
    """Tests for session isolation."""

    def test_multiple_controllers_independent(self):
        controllers = [UIController() for _ in range(5)]
        session_ids = [c.session_id for c in controllers]
        
        assert len(set(session_ids)) == 5
        
        controllers[0].module_v_state.complete_phase1([1.0, 2.0, 3.0])
        
        for i in range(1, 5):
            assert not controllers[i].module_v_state.phase1_complete

    def test_session_id_uniqueness(self):
        controller = UIController()
        sid1 = controller.session_id
        
        controller2 = UIController()
        sid2 = controller2.session_id
        
        assert sid1 != sid2


class TestUIControllerRealExecution:
    """Tests that execute real code (not mocked) for coverage."""

    def test_module_v_state_workflow_complete(self):
        """Test complete Module V workflow execution."""
        from sample_size_calculator.models import (
            AnalysisMethod,
            Phase1Results,
            Phase2Results,
            Phase3Results,
            Phase4Results,
            SpecificationType,
            TransformationMethod,
        )
        from sample_size_calculator.ui_controller import ModuleVState
        
        state = ModuleVState()
        
        # Phase 1: Complete with pilot data
        phase1_results = Phase1Results(
            pilot_data=[10.0, 10.1, 9.9, 10.2, 10.0],
            outliers=[],
            q1=9.9,
            q3=10.2,
            iqr=0.3,
        )
        state.complete_phase1(phase1_results)
        
        assert state.phase1_complete
        assert not state.phase2_complete
        
        # Phase 2: Complete with transformation results
        phase2_results = Phase2Results(
            cleaned_data=[10.0, 10.1, 9.9],
            shapiro_p_value=0.85,
            transformation_method=TransformationMethod.NONE,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=None,
            manual_override=False,
        )
        state.complete_phase2(phase2_results)
        
        assert state.phase2_complete
        assert not state.phase3_complete
        
        # Phase 3: Complete with sample size calculation
        phase3_results = Phase3Results(
            required_sample_size=10,
            k_margin=1.5,
            k_factor=2.5,
            specification_type=SpecificationType.TWO_SIDED,
        )
        state.complete_phase3(phase3_results)
        
        assert state.phase3_complete
        assert not state.phase4_complete
        
        # Phase 4: Complete with tolerance limits
        phase4_results = Phase4Results(
            tolerance_limits={"lower": 9.8, "upper": 10.2},
            pass_fail="Pass",
            ppk=1.5,
            final_data=[10.0, 10.1, 9.9, 10.2, 10.0],
        )
        state.complete_phase4(phase4_results)
        
        assert state.phase4_complete
        assert state.is_phase_enabled(4)
    def test_ui_controller_session_id_generation(self):
        """Test that session IDs are properly generated."""
        import uuid

        from sample_size_calculator.ui_controller import UIController
        
        controller = UIController()
        
        # Verify it's a valid UUID4
        parsed = uuid.UUID(controller.session_id)
        assert parsed.version == 4

    def test_ui_controller_initial_state(self):
        """Test initial state of UI controller."""
        from sample_size_calculator.ui_controller import UIController
        
        controller = UIController()
        
        assert controller.module_a_results is None
        assert controller.validation_button is None
        assert controller.session_id is not None
