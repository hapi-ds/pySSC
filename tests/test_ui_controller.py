"""Comprehensive unit tests for UI controller."""

import pytest
from unittest.mock import MagicMock, patch

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
            Phase1Results,
            Phase2Results,
            TransformationMethod,
            AnalysisMethod,
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
        
        from sample_size_calculator.models import Phase1Results
        state.complete_phase1([1.0, 2.0, 3.0])
        
        assert state.is_phase_enabled(2) is True

    def test_complete_phase3_clears_phase4(self):
        from sample_size_calculator.models import (
            Phase1Results,
            Phase2Results,
            Phase3Results,
            SpecificationType,
            TransformationMethod,
            AnalysisMethod,
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
            Phase1Results,
            Phase2Results,
            Phase3Results,
            SpecificationType,
            TransformationMethod,
            AnalysisMethod,
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
