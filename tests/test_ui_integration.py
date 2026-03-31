"""Integration tests for UI controller."""



class TestModuleVStateWorkflow:
    def test_complete_workflow_state_transitions(self):
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
        
        phase3_results = Phase3Results(
            required_sample_size=10,
            k_margin=1.5,
            k_factor=2.5,
            specification_type=SpecificationType.TWO_SIDED,
        )
        state.complete_phase3(phase3_results)
        
        assert state.phase3_complete
        assert not state.phase4_complete
        
        phase4_results = Phase4Results(
            tolerance_limits={"lower": 9.8, "upper": 10.2},
            pass_fail="Pass",
            ppk=1.5,
            final_data=[10.0, 10.1, 9.9, 10.2, 10.0],
        )
        state.complete_phase4(phase4_results)
        
        assert state.phase4_complete

    def test_workflow_reset_after_recompletion(self):
        from sample_size_calculator.models import (
            AnalysisMethod,
            Phase1Results,
            Phase2Results,
            Phase3Results,
            SpecificationType,
            TransformationMethod,
        )
        from sample_size_calculator.ui_controller import ModuleVState

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
        
        state.complete_phase2(phase2_results)
        
        assert state.phase1_complete
        assert state.phase2_complete
        assert not state.phase3_complete
        assert not state.phase4_complete


class TestUIControllerSessionManagement:
    def test_session_id_is_unique_uuid(self):
        import uuid

        from sample_size_calculator.ui_controller import UIController

        controllers = [UIController() for _ in range(10)]
        
        session_ids = [c.session_id for c in controllers]
        
        assert len(set(session_ids)) == 10
        
        for sid in session_ids:
            parsed = uuid.UUID(sid)
            assert parsed.version == 4


class TestModuleACalculationLogic:
    def test_success_run_theorem_calculation(self):
        from sample_size_calculator.calculations import CalculationEngine

        n = CalculationEngine.success_run_theorem(95.0, 95.0)

        assert isinstance(n, int)
        assert n > 0

    def test_cumulative_binomial_calculation(self):
        from sample_size_calculator.calculations import CalculationEngine

        n = CalculationEngine.cumulative_binomial(95.0, 95.0, 2)

        assert isinstance(n, int)
        assert n > 0


class TestModuleVPhase1Logic:
    def test_pilot_data_parsing(self):
        pilot_data_str = "10.0, 10.1, 9.9, 10.2, 10.0"
        pilot_data = [float(x.strip()) for x in pilot_data_str.split(",") if x.strip()]

        assert len(pilot_data) == 5


class TestModuleVPhase2Logic:
    def test_normality_test_values(self):
        from sample_size_calculator.normality import shapiro_wilk_test

        data = [10.0, 10.1, 9.9, 10.2, 10.0, 9.8, 10.3]

        stat, p_value = shapiro_wilk_test(data)

        assert 0 <= stat <= 1
        assert 0 <= p_value <= 1


class TestModuleVPhase3Logic:
    def test_capability_margin_calculation(self):
        from sample_size_calculator.models import (
            SpecificationLimits,
            SpecificationType,
            TransformationMethod,
        )
        from sample_size_calculator.tolerance import calculate_capability_margin

        data = [10.0, 10.1, 9.9, 10.2, 10.0]
        spec_limits = SpecificationLimits(
            spec_type=SpecificationType.TWO_SIDED,
            lsl=9.5,
            usl=10.5,
        )

        k_margin = calculate_capability_margin(data, spec_limits, TransformationMethod.NONE)

        assert k_margin > 0


class TestModuleVPhase4Logic:
    def test_tolerance_limit_calculation(self):
        from sample_size_calculator.models import (
            AnalysisMethod,
            Phase2Results,
            Phase3Results,
            SpecificationLimits,
            SpecificationType,
            TransformationMethod,
        )
        from sample_size_calculator.tolerance import calculate_tolerance_limits

        phase2_results = Phase2Results(
            cleaned_data=[10.0, 10.1, 9.9, 10.2, 10.0],
            shapiro_p_value=0.85,
            transformation_method=TransformationMethod.NONE,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=None,
            manual_override=False,
        )

        phase3_results = Phase3Results(
            required_sample_size=5,
            k_margin=1.5,
            k_factor=2.5,
            specification_type=SpecificationType.TWO_SIDED,
        )

        spec_limits = SpecificationLimits(
            spec_type=SpecificationType.TWO_SIDED,
            lsl=9.5,
            usl=10.5,
        )

        phase4_results = calculate_tolerance_limits(
            [10.0, 10.1, 9.9, 10.2, 10.0], phase2_results, phase3_results, spec_limits
        )

        assert "lower" in phase4_results.tolerance_limits
        assert "upper" in phase4_results.tolerance_limits


class TestAuditLoggerIntegration:
    def test_ui_controller_has_logger(self):
        from sample_size_calculator.ui_controller import UIController

        controller = UIController()

        assert hasattr(controller, "logger")
        assert controller.logger is not None


class TestValidationButtonLogic:
    def test_validation_button_initial_state(self):
        from sample_size_calculator.ui_controller import UIController

        controller = UIController()

        assert controller.validation_button is None
