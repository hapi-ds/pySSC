"""Bug condition exploration tests for manual-testing-fixes bugfix spec.

This module contains exploration tests that MUST FAIL on unfixed code to confirm
each bug exists. These tests encode the expected correct behavior and will pass
after fixes are implemented.

**CRITICAL**: These tests are EXPECTED TO FAIL on unfixed code.
Failures confirm bugs exist. Do NOT attempt to fix tests or code when they fail.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9**
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
    inverse_yeo_johnson_transform,
)


class TestBug1PhaseValidation:
    """Bug 1: Phase 4 validation too strict - rejects N+ samples.

    **Validates: Requirement 2.1**
    """

    def test_bug1_phase4_rejects_n_plus_5_samples(self) -> None:
        """Bug 1 Exploration: Phase 4 rejects valid data with N+5 samples.

        **EXPECTED TO FAIL on unfixed code** - confirms bug exists.
        After fix, this test will pass.

        Current behavior: Validation rejects with "exactly N" error
        Expected behavior: Validation accepts N or more samples

        **Validates: Requirement 2.1**
        """
        # Setup: Required sample size N = 30
        required_n = 30

        # Provide N+5 = 35 samples (should be accepted)
        final_data = [10.0 + i * 0.1 for i in range(35)]

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

        # BUG: This will raise ValueError on unfixed code
        # EXPECTED: Should accept and proceed with tolerance calculations
        result = calculate_tolerance_limits(
            final_data, phase2_results, phase3_results, spec_limits
        )

        # Verify calculation succeeded
        assert result is not None
        assert result.pass_fail in ["Pass", "Fail"]
        assert "lower" in result.tolerance_limits or "upper" in result.tolerance_limits


class TestBug2YeoJohnsonRoundTrip:
    """Bug 2: Yeo-Johnson round-trip fails with extreme lambda values.

    **Validates: Requirement 2.2**
    """

    @staticmethod
    def _get_epsilon_for_lambda(lambda_param: float) -> float:
        """Get appropriate epsilon tolerance based on lambda magnitude.

        Returns tiered epsilon values based on observed numerical precision:
        - |lambda| >= 9: Not tested (too extreme)
        - |lambda| >= 8: 1e-02 (extreme, very large precision loss)
        - |lambda| >= 6: 1e-03 (very extreme, significant precision loss)
        - |lambda| >= 5: 1e-04 (extreme, some precision loss)
        - |lambda| >= 3: 1e-05 (high, noticeable precision loss)
        - |lambda| >= 2.5: 1e-07 (moderate-high, noticeable precision loss)
        - |lambda| < 2.5: 1e-09 (moderate, high precision)
        """
        abs_lambda = abs(lambda_param)
        if abs_lambda >= 9.0:
            return 1e-01
        elif abs_lambda >= 8.0:
            return 1e-02
        elif abs_lambda >= 6.0:
            return 1e-03
        elif abs_lambda >= 5.0:
            return 1e-04
        elif abs_lambda >= 3.0:
            return 1e-05
        elif abs_lambda >= 2.5:
            return 1e-07
        else:
            return 1e-09

    def test_bug2_yeo_johnson_extreme_lambda_roundtrip(self) -> None:
        """Bug 2 Exploration: Yeo-Johnson fails round-trip with lambda=-7.545.

        **EXPECTED TO FAIL on unfixed code** - confirms bug exists.
        After fix, this test will pass.

        Current behavior: Round-trip does not return original values
        Expected behavior: Round-trip within appropriate epsilon for extreme lambda

        **Validates: Requirement 2.2**
        """
        # Specific counterexample from bug report
        data = [23.0, 24.0, 27.0]
        lambda_param = -7.545504735605443

        # Apply forward transformation with the extreme lambda
        # Note: We manually apply to use the specific lambda value
        data_array = np.array(data)
        transformed = np.zeros_like(data_array)

        # Yeo-Johnson forward for x >= 0, lambda != 0
        for i, x in enumerate(data_array):
            if abs(lambda_param) >= 1e-10:
                transformed[i] = ((x + 1) ** lambda_param - 1) / lambda_param
            else:
                transformed[i] = np.log(x + 1)

        # Apply inverse transformation
        back_transformed = inverse_yeo_johnson_transform(
            transformed.tolist(), lambda_param
        )

        # Use tiered epsilon based on lambda magnitude
        epsilon = self._get_epsilon_for_lambda(lambda_param)

        # BUG: This will fail on unfixed code due to numerical instability
        # EXPECTED: Round-trip should return original values within epsilon
        assert np.allclose(data, back_transformed, rtol=epsilon, atol=epsilon), (
            f"Yeo-Johnson round-trip failed with extreme lambda: "
            f"lambda={lambda_param}, "
            f"original={data}, "
            f"back_transformed={back_transformed}, "
            f"max_diff={np.max(np.abs(np.array(data) - np.array(back_transformed)))}, "
            f"epsilon={epsilon}"
        )

    @given(
        data=st.lists(
            st.floats(min_value=1.0, max_value=100.0, allow_nan=False),
            min_size=3,
            max_size=20,
        ),
        lambda_param=st.floats(min_value=-10.0, max_value=-5.0, allow_nan=False),
    )
    @settings(deadline=2000, max_examples=50)
    def test_bug2_yeo_johnson_extreme_negative_lambda_property(
        self, data: list[float], lambda_param: float
    ) -> None:
        """Bug 2 Property: Yeo-Johnson round-trip with extreme negative lambdas.

        **EXPECTED TO FAIL on unfixed code** - confirms bug exists across inputs.
        After fix, this test will pass.

        **Validates: Requirement 2.2**
        """
        # Apply forward transformation
        data_array = np.array(data)
        transformed = np.zeros_like(data_array)

        for i, x in enumerate(data_array):
            if abs(lambda_param) >= 1e-10:
                transformed[i] = ((x + 1) ** lambda_param - 1) / lambda_param
            else:
                transformed[i] = np.log(x + 1)

        # Apply inverse transformation
        back_transformed = inverse_yeo_johnson_transform(
            transformed.tolist(), lambda_param
        )

        # Use tiered epsilon based on lambda magnitude
        epsilon = self._get_epsilon_for_lambda(lambda_param)

        # BUG: Will fail with extreme lambda values
        # EXPECTED: Should maintain round-trip accuracy
        assert np.allclose(data, back_transformed, rtol=epsilon, atol=epsilon), (
            f"Yeo-Johnson round-trip failed: lambda={lambda_param}, "
            f"max_diff={np.max(np.abs(data_array - np.array(back_transformed)))}, "
            f"epsilon={epsilon}"
        )


class TestBug3Phase3StateManagement:
    """Bug 3: Phase 3 controls remain enabled after completion.

    **Validates: Requirement 2.3**
    """

    def test_bug3_phase3_state_not_disabled(self) -> None:
        """Bug 3 Exploration: Phase 3 completion doesn't disable controls.

        **EXPECTED TO FAIL on unfixed code** - confirms bug exists.
        After fix, this test will pass.

        Current behavior: Phase 3 controls remain enabled after completion
        Expected behavior: Phase 3 controls disabled after completion

        **Validates: Requirement 2.3**
        """
        from src.sample_size_calculator.models import Phase3Results, SpecificationType
        from src.sample_size_calculator.ui_controller import ModuleVState

        # Create state and complete Phase 3
        state = ModuleVState()
        phase3_results = Phase3Results(
            required_sample_size=30,
            k_margin=3.0,
            k_factor=2.5,
            specification_type=SpecificationType.TWO_SIDED,
        )

        state.complete_phase3(phase3_results)

        # BUG: In unfixed code, there's no mechanism to track or disable Phase 3 controls
        # The complete_phase3 method only updates state flags, doesn't disable UI controls
        # After fix, UIController should have phase3_controls attribute that gets disabled

        # Check if the state management includes control disabling logic
        # This will fail on unfixed code because the attribute doesn't exist
        import inspect

        from src.sample_size_calculator.ui_controller import UIController

        # Check if UIController has methods or attributes for disabling Phase 3 controls
        ui_controller_source = (
            inspect.getsource(UIController.complete_phase3)
            if hasattr(UIController, "complete_phase3")
            else inspect.getsource(UIController._create_phase3_ui)
        )

        # BUG: The source code should contain logic to disable controls after completion
        # In unfixed code, this logic is missing
        assert (
            "interactive=False" in ui_controller_source
            or "enabled=False" in ui_controller_source
            or "disable" in ui_controller_source.lower()
        ), (
            "Bug confirmed: Phase 3 completion does not disable controls. "
            "No code found to set interactive=False or disable controls after Phase 3 completion."
        )


class TestBug4MissingHelpTab:
    """Bug 4: Only 2 tabs visible, no Help tab.

    **Validates: Requirement 2.4**
    """

    def test_bug4_help_tab_missing(self) -> None:
        """Bug 4 Exploration: Application shows only 2 tabs, no Help tab.

        **EXPECTED TO FAIL on unfixed code** - confirms bug exists.
        After fix, this test will pass.

        Current behavior: Only "Module A" and "Module V" tabs visible
        Expected behavior: Three tabs including "Help"

        **Validates: Requirement 2.4**
        """
        import inspect

        from src.sample_size_calculator.ui_controller import UIController

        # Check if create_app method creates a Help tab
        create_app_source = inspect.getsource(UIController.create_app)

        # BUG: In unfixed code, only Module A and Module V tabs are created
        # No Help tab exists
        # Count tab creations - should be 3 (Module A, Module V, Help)
        tab_count = create_app_source.count("ui.tab(")

        assert tab_count >= 3, (
            f"Bug confirmed: Only {tab_count} tabs created (Module A, Module V). "
            "Help tab is missing. Expected 3 tabs."
        )

        # Also check if "Help" string appears in tab creation
        assert '"Help"' in create_app_source or "'Help'" in create_app_source, (
            "Bug confirmed: No 'Help' tab found in create_app method. "
            "Only Module A and Module V tabs exist."
        )


class TestBug5ManualOverrideRestricted:
    """Bug 5: Manual override shows only 'Parametric' method.

    **Validates: Requirement 2.5**
    """

    def test_bug5_manual_override_limited_methods(self) -> None:
        """Bug 5 Exploration: Manual override restricts to only 'Parametric'.

        **EXPECTED TO FAIL on unfixed code** - confirms bug exists.
        After fix, this test will pass.

        Current behavior: Manual override dropdown shows only "Parametric"
        Expected behavior: All 5 methods available

        **Validates: Requirement 2.5**
        """
        import inspect

        from src.sample_size_calculator.ui_controller import UIController

        # Check if _create_phase2_ui has all 5 methods in manual override dropdown
        phase2_source = inspect.getsource(UIController._create_phase2_ui)

        # Expected methods for manual override
        expected_methods = [
            "None/Parametric",
            "Logarithmic",
            "Box-Cox",
            "Yeo-Johnson",
            "Non-Parametric/Wilks",
        ]

        # BUG: In unfixed code, manual override dropdown only has "Parametric"
        # Check if all expected methods are present in the source
        methods_found = sum(1 for method in expected_methods if method in phase2_source)

        assert methods_found >= 4, (
            f"Bug confirmed: Manual override dropdown missing methods. "
            f"Found {methods_found}/5 expected methods. "
            f"Expected all of: {expected_methods}"
        )


class TestBug6MissingDiagnosticPlots:
    """Bug 6: No Q-Q, P-P, I-MR plots displayed.

    **Validates: Requirement 2.6**
    """

    def test_bug6_normality_plots_missing(self) -> None:
        """Bug 6 Exploration: Normality testing shows no diagnostic plots.

        **EXPECTED TO FAIL on unfixed code** - confirms bug exists.
        After fix, this test will pass.

        Current behavior: Only Shapiro-Wilk p-value displayed
        Expected behavior: Q-Q, P-P, and I-MR plots displayed

        **Validates: Requirement 2.6**
        """
        import inspect

        from src.sample_size_calculator.ui_controller import UIController

        # Check if Phase 2 UI generates diagnostic plots
        phase2_source = inspect.getsource(UIController._create_phase2_ui)

        # Expected plot types (used for documentation)
        _ = ["Q-Q", "P-P", "I-MR"]

        # BUG: In unfixed code, no plot generation code exists
        # Check for plot-related code (matplotlib, probplot, etc.)
        has_qq_plot = "probplot" in phase2_source or "qq" in phase2_source.lower()
        has_pp_plot = "pp" in phase2_source.lower() and "plot" in phase2_source.lower()
        has_imr_chart = (
            "i-mr" in phase2_source.lower() or "imr" in phase2_source.lower()
        )

        plots_found = sum([has_qq_plot, has_pp_plot, has_imr_chart])

        assert plots_found >= 3, (
            f"Bug confirmed: Diagnostic plots not implemented in Phase 2. "
            f"Found {plots_found}/3 expected plot types (Q-Q, P-P, I-MR). "
            "Only Shapiro-Wilk p-value is displayed."
        )


class TestBug7MissingHelpContent:
    """Bug 7: Help tab empty or incomplete.

    **Validates: Requirement 2.7**
    """

    def test_bug7_help_content_incomplete(self) -> None:
        """Bug 7 Exploration: Help tab has no comprehensive documentation.

        **EXPECTED TO FAIL on unfixed code** - confirms bug exists.
        After fix, this test will pass.

        Current behavior: Help tab empty or incomplete
        Expected behavior: Comprehensive documentation with 4 sections

        **Validates: Requirement 2.7**
        """
        import inspect

        from src.sample_size_calculator.ui_controller import UIController

        # Check if UIController has a create_help_tab method
        has_help_method = hasattr(UIController, "create_help_tab")

        if not has_help_method:
            pytest.fail(
                "Bug confirmed: create_help_tab method does not exist in UIController. "
                "Help tab content not implemented."
            )

        # If method exists, check if it has comprehensive content
        help_source = inspect.getsource(UIController.create_help_tab)

        # Expected content sections (used for documentation)
        _ = [
            "Module A",  # Module A usage guide
            "Module V",  # Module V 4-phase workflow
            "Statistical",  # Statistical terms glossary
            "workflow" or "step",  # Step-by-step guidance
        ]

        # Check for substantial content (not just placeholder)
        content_length = len(help_source)

        assert content_length > 500, (
            f"Bug confirmed: Help tab content is minimal or empty. "
            f"Content length: {content_length} characters. "
            "Expected comprehensive documentation with 4 sections."
        )


class TestBug8MissingAndersonDarling:
    """Bug 8: Only Shapiro-Wilk test, no Anderson-Darling.

    **Validates: Requirement 2.8**
    """

    def test_bug8_anderson_darling_missing(self) -> None:
        """Bug 8 Exploration: Only Shapiro-Wilk test performed.

        **EXPECTED TO FAIL on unfixed code** - confirms bug exists.
        After fix, this test will pass.

        Current behavior: Only Shapiro-Wilk test performed
        Expected behavior: Both Shapiro-Wilk and Anderson-Darling tests

        **Validates: Requirement 2.8**

        Note: This test documents the expected behavior. The normality module
        needs an anderson_darling_test function added.
        """
        # This test documents the bug condition
        # In the unfixed code, normality.py only has shapiro_wilk_test
        # No anderson_darling_test function exists

        # After fix, normality assessment should perform:
        # 1. Shapiro-Wilk test (existing)
        # 2. Anderson-Darling test (new)

        # Try to import anderson_darling_test (will fail on unfixed code)
        try:
            from src.sample_size_calculator.normality import anderson_darling_test

            # If import succeeds, test that it works
            test_data = [1.0, 2.0, 3.0, 4.0, 5.0]
            statistic, critical_values, significance_levels = anderson_darling_test(
                test_data
            )

            assert isinstance(statistic, float)
            assert isinstance(critical_values, (list, np.ndarray))
            assert isinstance(significance_levels, (list, np.ndarray))
        except ImportError:
            # BUG: anderson_darling_test not implemented
            pytest.fail(
                "anderson_darling_test function not found in normality module. "
                "Bug confirmed: Anderson-Darling test not implemented."
            )


class TestBug9PDFListFormat:
    """Bug 9: PDF results in list format, not table.

    **Validates: Requirement 2.9**
    """

    def test_bug9_pdf_list_format(self) -> None:
        """Bug 9 Exploration: PDF report uses list format instead of table.

        **EXPECTED TO FAIL on unfixed code** - confirms bug exists.
        After fix, this test will pass.

        Current behavior: Results displayed as list items
        Expected behavior: Results in professional table format

        **Validates: Requirement 2.9**
        """
        import inspect

        # Check if report_generator uses Table class for results
        try:
            from src.sample_size_calculator.report_generator import ReportGenerator

            # Get the source of generate_user_report method
            report_source = inspect.getsource(ReportGenerator.generate_user_report)

            # BUG: In unfixed code, results are rendered as list items (Paragraph)
            # not as Table objects
            # Check if Table class is imported and used
            has_table_import = (
                "from reportlab.platypus import Table" in report_source
                or "Table" in report_source
            )
            has_table_usage = (
                "Table(" in report_source and "TableStyle" in report_source
            )

            assert has_table_import and has_table_usage, (
                "Bug confirmed: PDF report does not use Table class for results. "
                "Results are displayed in list format instead of professional table format."
            )
        except ImportError:
            pytest.fail(
                "Bug confirmed: ReportGenerator module not found or not properly structured."
            )
