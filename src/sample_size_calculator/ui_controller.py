"""NiceGUI-based web interface controller for the Sample Size Calculator.

This module provides the complete user interface for both Module A (attribute data)
and Module V (variable data) analysis, with session management, workflow enforcement,
and comprehensive audit logging.
"""

import uuid
from datetime import datetime
from typing import Any

from nicegui import ui

from sample_size_calculator.audit_logger import AuditLogger
from sample_size_calculator.calculations import CalculationEngine
from sample_size_calculator.hash_verifier import get_engine_hash, is_validated_state
from sample_size_calculator.models import (
    AnalysisMethod,
    AttributeInputs,
    CalculationReport,
    OutlierInfo,
    Phase1Results,
    Phase2Results,
    Phase3Results,
    Phase4Results,
    SpecificationLimits,
    SpecificationType,
    TransformationMethod,
)
from sample_size_calculator.outliers import apply_exclusions, detect_outliers
from sample_size_calculator.report_generator import ReportGenerator
from sample_size_calculator.tolerance import (
    calculate_capability_margin,
    calculate_required_sample_size,
    calculate_tolerance_limits,
)
from sample_size_calculator.transformations import transformation_cascade


class ModuleVState:
    """Manages Module V workflow state for sequential phase enforcement."""

    def __init__(self) -> None:
        """Initialize workflow state."""
        self.phase1_complete = False
        self.phase2_complete = False
        self.phase3_complete = False
        self.phase4_complete = False

        self.phase1_results: Phase1Results | None = None
        self.phase2_results: Phase2Results | None = None
        self.phase3_results: Phase3Results | None = None
        self.phase4_results: Phase4Results | None = None

        # Store user inputs for each phase
        self.spec_limits: SpecificationLimits | None = None
        self.confidence: float | None = None
        self.reliability: float | None = None
        self.pilot_data: list[float] | None = None

    def complete_phase1(self, results: Phase1Results) -> None:
        """Mark Phase 1 complete and enable Phase 2."""
        self.phase1_results = results
        self.phase1_complete = True
        # Clear downstream phases
        self.phase2_complete = False
        self.phase3_complete = False
        self.phase4_complete = False
        self.phase2_results = None
        self.phase3_results = None
        self.phase4_results = None

    def complete_phase2(self, results: Phase2Results) -> None:
        """Mark Phase 2 complete and enable Phase 3."""
        self.phase2_results = results
        self.phase2_complete = True
        # Clear downstream phases
        self.phase3_complete = False
        self.phase4_complete = False
        self.phase3_results = None
        self.phase4_results = None

    def complete_phase3(self, results: Phase3Results) -> None:
        """Mark Phase 3 complete and enable Phase 4."""
        self.phase3_results = results
        self.phase3_complete = True
        # Clear downstream phase
        self.phase4_complete = False
        self.phase4_results = None

    def complete_phase4(self, results: Phase4Results) -> None:
        """Mark Phase 4 complete."""
        self.phase4_results = results
        self.phase4_complete = True

    def is_phase_enabled(self, phase: int) -> bool:
        """Check if a phase is enabled."""
        if phase == 1:
            return True
        elif phase == 2:
            return self.phase1_complete
        elif phase == 3:
            return self.phase2_complete
        elif phase == 4:
            return self.phase3_complete
        return False


class UIController:
    """Manages NiceGUI web interface for Sample Size Calculator."""

    def __init__(self) -> None:
        """Initialize UI controller with session management."""
        self.logger = AuditLogger()
        self.session_id = self._generate_session_id()
        self.module_v_state = ModuleVState()

        # Module A state
        self.module_a_results: dict[str, Any] | None = None

    def _generate_session_id(self) -> str:
        """Generate unique session identifier using uuid4."""
        return str(uuid.uuid4())

    def create_app(self) -> None:
        """Create the main NiceGUI application with tabs."""
        ui.page_title("Sample Size Calculator")

        with ui.header().classes("items-center justify-between"):
            ui.label("Sample Size Calculator").classes("text-h4")
            ui.label("Medical Device Design Verification & Process Validation").classes(
                "text-subtitle1"
            )

        with ui.tabs().classes("w-full") as tabs:
            module_a_tab = ui.tab("Module A: Attribute Data")
            module_v_tab = ui.tab("Module V: Variable Data")

        with ui.tab_panels(tabs, value=module_a_tab).classes("w-full"):
            with ui.tab_panel(module_a_tab):
                self.create_module_a_tab()

            with ui.tab_panel(module_v_tab):
                self.create_module_v_tab()

    def create_module_a_tab(self) -> None:
        """Create Module A UI tab for attribute data analysis."""
        ui.label("Module A: Attribute Data Analysis").classes("text-h5")
        ui.label(
            "Calculate sample sizes for binary Pass/Fail test scenarios"
        ).classes("text-subtitle2")
        ui.separator()

        # Input fields
        with ui.card().classes("w-full"):
            ui.label("Input Parameters").classes("text-h6")

            # Confidence input
            with ui.row().classes("w-full items-center"):
                confidence_input = (
                    ui.number(
                        label="Confidence Level (%)",
                        value=95.0,
                        min=0.01,
                        max=99.99,
                        step=0.1,
                        precision=2,
                    )
                    .classes("w-64")
                    .tooltip(
                        "The probability that the true reliability is at least "
                        "the specified value. Typical values: 90%, 95%, 99%.",
                    )
                )

            # Reliability input
            with ui.row().classes("w-full items-center"):
                reliability_input = (
                    ui.number(
                        label="Reliability Level (%)",
                        value=95.0,
                        min=0.01,
                        max=99.99,
                        step=0.1,
                        precision=2,
                    )
                    .classes("w-64")
                    .tooltip(
                        "The minimum acceptable proportion of passing units. "
                        "Typical values: 90%, 95%, 99%.",
                    )
                )

            # Allowable failures input
            with ui.row().classes("w-full items-center"):
                allowable_failures_input = (
                    ui.number(
                        label="Allowable Failures (c)",
                        value=None,
                        min=0,
                        step=1,
                        precision=0,
                    )
                    .classes("w-64")
                    .tooltip(
                        "Number of failures allowed in the test. "
                        "Leave empty for sensitivity analysis (c=0,1,2,3). "
                        "Use 0 for zero-failure testing (Success Run Theorem).",
                    )
                )
                ui.label("(Leave empty for sensitivity analysis)").classes(
                    "text-caption"
                )

        # Calculate button
        with ui.row().classes("w-full"):
            calculate_btn = ui.button("Calculate Sample Size", icon="calculate").classes(
                "bg-primary"
            )

        # Results display
        results_card = ui.card().classes("w-full")
        with results_card:
            results_container = ui.column().classes("w-full")

        # Report generation button (initially hidden)
        report_btn_container = ui.row().classes("w-full")
        with report_btn_container:
            report_btn = ui.button(
                "Generate PDF Report", icon="picture_as_pdf"
            ).classes("bg-secondary")
        report_btn_container.set_visibility(False)

        # Calculate button handler
        def handle_calculate() -> None:
            """Handle Module A calculation."""
            self.logger.log_button_click(
                "calculate_module_a", "Module_A", None, self.session_id
            )

            try:
                # Validate inputs
                confidence = confidence_input.value
                reliability = reliability_input.value
                allowable_failures = allowable_failures_input.value

                if confidence is None or reliability is None:
                    ui.notify("Please enter confidence and reliability values", type="negative")
                    return

                # Create input model for validation
                inputs = AttributeInputs(
                    confidence=confidence,
                    reliability=reliability,
                    allowable_failures=int(allowable_failures)
                    if allowable_failures is not None
                    else None,
                )

                # Log calculation
                engine_hash = get_engine_hash()

                # Perform calculation
                if inputs.allowable_failures is None:
                    # Sensitivity analysis
                    results = CalculationEngine.sensitivity_analysis(
                        confidence, reliability
                    )

                    # Store results
                    self.module_a_results = {
                        "type": "sensitivity",
                        "confidence": confidence,
                        "reliability": reliability,
                        "results": results,
                    }

                    # Display results
                    results_container.clear()
                    with results_container:
                        ui.label("Calculation Results").classes("text-h6")
                        ui.label("Method: Sensitivity Analysis").classes("text-body1")
                        ui.separator()

                        # Create table
                        table_data = {
                            "columnDefs": [
                                {"headerName": "Allowable Failures (c)", "field": "c"},
                                {"headerName": "Required Sample Size (n)", "field": "n"},
                            ],
                            "rowData": [{"c": c, "n": n} for c, n in results],
                        }
                        ui.aggrid(table_data).classes("w-full")

                    # Log calculation
                    self.logger.log_calculation(
                        "sensitivity_analysis",
                        {"confidence": confidence, "reliability": reliability},
                        {"results": results},
                        engine_hash,
                        self.session_id,
                    )

                else:
                    # Single calculation
                    if inputs.allowable_failures == 0:
                        n = CalculationEngine.success_run_theorem(confidence, reliability)
                        method = "Success Run Theorem"
                    else:
                        n = CalculationEngine.cumulative_binomial(
                            confidence, reliability, inputs.allowable_failures
                        )
                        method = "Cumulative Binomial"

                    # Store results
                    self.module_a_results = {
                        "type": "single",
                        "confidence": confidence,
                        "reliability": reliability,
                        "allowable_failures": inputs.allowable_failures,
                        "sample_size": n,
                        "method": method,
                    }

                    # Display results
                    results_container.clear()
                    with results_container:
                        ui.label("Calculation Results").classes("text-h6")
                        ui.label(f"Method: {method}").classes("text-body1")
                        ui.separator()
                        ui.label(f"Required Sample Size (n): {n}").classes(
                            "text-h4 text-primary"
                        )

                    # Log calculation
                    self.logger.log_calculation(
                        method.lower().replace(" ", "_"),
                        {
                            "confidence": confidence,
                            "reliability": reliability,
                            "allowable_failures": inputs.allowable_failures,
                        },
                        {"sample_size": n},
                        engine_hash,
                        self.session_id,
                    )

                # Show report button
                report_btn_container.set_visibility(True)
                ui.notify("Calculation completed successfully", type="positive")

            except ValueError as e:
                self.logger.log_validation_error(
                    "input_validation",
                    str(e),
                    "module_a_inputs",
                    {
                        "confidence": confidence_input.value,
                        "reliability": reliability_input.value,
                        "allowable_failures": allowable_failures_input.value,
                    },
                    self.session_id,
                )
                ui.notify(f"Validation error: {e}", type="negative")
            except Exception as e:
                ui.notify(f"Calculation error: {e}", type="negative")

        calculate_btn.on_click(handle_calculate)

        # Report generation handler
        def handle_generate_report() -> None:
            """Generate PDF report for Module A."""
            self.logger.log_button_click(
                "generate_report_module_a", "Module_A", None, self.session_id
            )

            try:
                if self.module_a_results is None:
                    ui.notify("No results to report", type="warning")
                    return

                # Get engine hash and validation state
                engine_hash = get_engine_hash()
                validation_state = is_validated_state()

                # Prepare report data
                if self.module_a_results["type"] == "sensitivity":
                    inputs = {
                        "confidence": self.module_a_results["confidence"],
                        "reliability": self.module_a_results["reliability"],
                        "allowable_failures": "Sensitivity Analysis (c=0,1,2,3)",
                    }
                    results = {
                        "method": "Sensitivity Analysis",
                        "results": str(self.module_a_results["results"]),
                    }
                    method_path = "Sensitivity Analysis: Success Run Theorem and Cumulative Binomial"
                else:
                    inputs = {
                        "confidence": self.module_a_results["confidence"],
                        "reliability": self.module_a_results["reliability"],
                        "allowable_failures": self.module_a_results["allowable_failures"],
                    }
                    results = {
                        "method": self.module_a_results["method"],
                        "sample_size": self.module_a_results["sample_size"],
                    }
                    method_path = self.module_a_results["method"]

                report_data = CalculationReport(
                    timestamp=datetime.now().isoformat(),
                    module="Module A",
                    inputs=inputs,
                    results=results,
                    engine_hash=engine_hash,
                    validation_state=validation_state,
                    method_path=method_path,
                )

                # Generate PDF
                pdf_bytes = ReportGenerator.generate_user_report(report_data)

                # Log report generation
                self.logger.log_report_generation(
                    "user_calculation", engine_hash, validation_state, self.session_id
                )

                # Trigger download
                ui.download(
                    pdf_bytes,
                    f"sample_size_report_module_a_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                )
                ui.notify("Report generated successfully", type="positive")

            except Exception as e:
                ui.notify(f"Report generation error: {e}", type="negative")

        report_btn.on_click(handle_generate_report)

    def create_module_v_tab(self) -> None:
        """Create Module V UI tab with 4-phase sequential workflow."""
        ui.label("Module V: Variable Data Analysis").classes("text-h5")
        ui.label(
            "4-Phase sequential workflow for continuous measurement analysis"
        ).classes("text-subtitle2")
        ui.separator()

        # Method transparency display
        self.method_transparency_card = ui.card().classes("w-full bg-blue-50")
        with self.method_transparency_card:
            self.method_transparency_label = ui.label(
                "Active Mathematical Path: Not yet determined"
            ).classes("text-body1 font-mono")
        self.method_transparency_card.set_visibility(False)

        # Phase 1: Specification Definition & Pilot Data
        with ui.expansion("Phase 1: Specification Definition & Pilot Data", icon="looks_one").classes(
            "w-full"
        ) as phase1_expansion:
            phase1_expansion.open()
            self._create_phase1_ui()

        # Phase 2: Outlier Exclusion & Normality Testing
        with ui.expansion(
            "Phase 2: Outlier Exclusion & Normality Testing", icon="looks_two"
        ).classes("w-full") as phase2_expansion:
            self.phase2_expansion = phase2_expansion
            self._create_phase2_ui()

        # Phase 3: Sample Size Calculation
        with ui.expansion("Phase 3: Sample Size Calculation", icon="looks_3").classes(
            "w-full"
        ) as phase3_expansion:
            self.phase3_expansion = phase3_expansion
            self._create_phase3_ui()

        # Phase 4: Final Validation Data & Tolerance Limits
        with ui.expansion(
            "Phase 4: Final Validation Data & Tolerance Limits", icon="looks_4"
        ).classes("w-full") as phase4_expansion:
            self.phase4_expansion = phase4_expansion
            self._create_phase4_ui()

        # Initially disable phases 2, 3, 4
        self._enforce_sequential_workflow()

    def _create_phase1_ui(self) -> None:
        """Create Phase 1 UI (specification definition and pilot data)."""
        with ui.card().classes("w-full"):
            ui.label("Specification Type").classes("text-h6")

            # Specification type selector
            self.spec_type_radio = ui.radio(
                ["One-Sided", "Two-Sided"], value="Two-Sided"
            ).props("inline")

            ui.separator()

            # Specification limits
            ui.label("Specification Limits").classes("text-h6")

            with ui.row().classes("w-full"):
                self.lsl_input = (
                    ui.number(
                        label="Lower Specification Limit (LSL)",
                        value=None,
                        step=0.1,
                    )
                    .classes("w-64")
                    .tooltip(
                        "The minimum acceptable value for the measured parameter",
                    )
                )

                self.usl_input = (
                    ui.number(
                        label="Upper Specification Limit (USL)",
                        value=None,
                        step=0.1,
                    )
                    .classes("w-64")
                    .tooltip(
                        "The maximum acceptable value for the measured parameter",
                    )
                )

            ui.separator()

            # Confidence and Reliability
            ui.label("Statistical Parameters").classes("text-h6")

            with ui.row().classes("w-full"):
                self.v_confidence_input = (
                    ui.number(
                        label="Confidence Level (%)",
                        value=95.0,
                        min=0.01,
                        max=99.99,
                        step=0.1,
                        precision=2,
                    )
                    .classes("w-64")
                    .tooltip(
                        "The probability that the tolerance interval contains "
                        "the specified proportion of the population",
                    )
                )

                self.v_reliability_input = (
                    ui.number(
                        label="Reliability Level (%)",
                        value=95.0,
                        min=0.01,
                        max=99.99,
                        step=0.1,
                        precision=2,
                    )
                    .classes("w-64")
                    .tooltip(
                        "The minimum proportion of the population that must be "
                        "within the tolerance interval",
                    )
                )

            ui.separator()

            # Pilot data input
            ui.label("Pilot Data Input").classes("text-h6")

            self.pilot_data_input = (
                ui.textarea(
                    label="Pilot Dataset (comma-separated values)",
                    placeholder="e.g., 10.5, 12.3, 11.8, 13.2, 12.1",
                )
                .classes("w-full")
                .tooltip(
                    "Enter pilot data measurements separated by commas. "
                    "Minimum 3 values required. Recommended: 12-30 samples.",
                )
            )

        # Analyze button
        with ui.row().classes("w-full"):
            analyze_phase1_btn = ui.button(
                "Analyze Pilot Data", icon="analytics"
            ).classes("bg-primary")

        # Results display
        self.phase1_results_card = ui.card().classes("w-full")
        with self.phase1_results_card:
            self.phase1_results_container = ui.column().classes("w-full")
        self.phase1_results_card.set_visibility(False)

        # Phase 1 button handler
        def handle_analyze_phase1() -> None:
            """Handle Phase 1 analysis."""
            self.logger.log_button_click(
                "analyze_phase1", "Module_V", "Phase_1", self.session_id
            )

            try:
                # Parse pilot data
                pilot_data_str = self.pilot_data_input.value
                if not pilot_data_str:
                    ui.notify("Please enter pilot data", type="warning")
                    return

                pilot_data = [
                    float(x.strip()) for x in pilot_data_str.split(",") if x.strip()
                ]

                if len(pilot_data) < 3:
                    ui.notify(
                        "Pilot dataset must contain at least 3 data points",
                        type="negative",
                    )
                    return

                # Validate specification limits
                spec_type = SpecificationType(self.spec_type_radio.value)
                lsl = self.lsl_input.value
                usl = self.usl_input.value

                spec_limits = SpecificationLimits(
                    spec_type=spec_type, lsl=lsl, usl=usl
                )

                # Store for later phases
                self.module_v_state.spec_limits = spec_limits
                self.module_v_state.confidence = self.v_confidence_input.value
                self.module_v_state.reliability = self.v_reliability_input.value
                self.module_v_state.pilot_data = pilot_data

                # Detect outliers
                phase1_results = detect_outliers(pilot_data)
                self.module_v_state.complete_phase1(phase1_results)

                # Display results
                self.phase1_results_container.clear()
                with self.phase1_results_container:
                    ui.label("Outlier Detection Results").classes("text-h6")
                    ui.label(f"Q1: {phase1_results.q1:.4f}").classes("text-body1")
                    ui.label(f"Q3: {phase1_results.q3:.4f}").classes("text-body1")
                    ui.label(f"IQR: {phase1_results.iqr:.4f}").classes("text-body1")
                    ui.separator()

                    if phase1_results.outliers:
                        ui.label(
                            f"Outliers Detected: {len(phase1_results.outliers)}"
                        ).classes("text-body1 text-warning")
                        for outlier in phase1_results.outliers:
                            ui.label(f"  • Value: {outlier.value}").classes(
                                "text-body2"
                            )
                    else:
                        ui.label("No outliers detected").classes(
                            "text-body1 text-positive"
                        )

                    # Warning for small datasets
                    if len(pilot_data) < 30:
                        ui.label(
                            f"⚠ Warning: Pilot dataset contains {len(pilot_data)} data points. "
                            "For reliable variance estimation, use 12-30 samples."
                        ).classes("text-body2 text-warning")

                self.phase1_results_card.set_visibility(True)

                # Enable Phase 2
                self._enforce_sequential_workflow()
                self.phase2_expansion.open()

                # Log phase transition
                self.logger.log_phase_transition(
                    "Phase_1", "Phase_2", "button_click", self.session_id
                )

                ui.notify("Phase 1 completed successfully", type="positive")

            except ValueError as e:
                self.logger.log_validation_error(
                    "phase1_validation",
                    str(e),
                    "phase1_inputs",
                    {
                        "pilot_data": self.pilot_data_input.value,
                        "spec_type": self.spec_type_radio.value,
                        "lsl": self.lsl_input.value,
                        "usl": self.usl_input.value,
                    },
                    self.session_id,
                )
                ui.notify(f"Validation error: {e}", type="negative")
            except Exception as e:
                ui.notify(f"Analysis error: {e}", type="negative")

        analyze_phase1_btn.on_click(handle_analyze_phase1)

    def _create_phase2_ui(self) -> None:
        """Create Phase 2 UI (outlier exclusion and transformation cascade)."""
        with ui.card().classes("w-full"):
            ui.label("Outlier Exclusion").classes("text-h6")

            self.outlier_exclusion_container = ui.column().classes("w-full")

            ui.separator()

            # Manual transformation override
            ui.label("Transformation Method").classes("text-h6")

            self.manual_override_checkbox = ui.checkbox(
                "Enable Manual Override"
            ).tooltip(
                "Override automatic transformation cascade and manually select method",
            )

            self.manual_method_radio = ui.radio(
                [
                    "None (Parametric)",
                    "Logarithmic",
                    "Box-Cox",
                    "Yeo-Johnson",
                    "Non-Parametric (Wilks)",
                ],
                value="None (Parametric)",
            ).props("inline")
            self.manual_method_radio.set_visibility(False)

            def toggle_manual_method() -> None:
                """Toggle manual method selector visibility."""
                self.manual_method_radio.set_visibility(
                    self.manual_override_checkbox.value
                )

            self.manual_override_checkbox.on('change', toggle_manual_method)

        # Process button
        with ui.row().classes("w-full"):
            process_phase2_btn = ui.button(
                "Process Normality Testing", icon="science"
            ).classes("bg-primary")

        # Results display
        self.phase2_results_card = ui.card().classes("w-full")
        with self.phase2_results_card:
            self.phase2_results_container = ui.column().classes("w-full")
        self.phase2_results_card.set_visibility(False)

        # Phase 2 button handler
        def handle_process_phase2() -> None:
            """Handle Phase 2 processing."""
            self.logger.log_button_click(
                "process_phase2", "Module_V", "Phase_2", self.session_id
            )

            try:
                if not self.module_v_state.phase1_complete:
                    ui.notify("Please complete Phase 1 first", type="warning")
                    return

                # Get outlier exclusions
                phase1_results = self.module_v_state.phase1_results
                if phase1_results is None:
                    ui.notify("Phase 1 results not found", type="negative")
                    return

                # Apply exclusions (if any were marked)
                excluded_outliers = [
                    o for o in phase1_results.outliers if o.is_excluded
                ]

                if excluded_outliers:
                    # Validate rationales
                    for outlier in excluded_outliers:
                        if not outlier.rationale or not outlier.rationale.strip():
                            ui.notify(
                                f"Please provide rationale for excluding outlier {outlier.value}",
                                type="negative",
                            )
                            return

                    cleaned_data = apply_exclusions(phase1_results, excluded_outliers)

                    # Log exclusions
                    for outlier in excluded_outliers:
                        self.logger.log_outlier_exclusion(
                            outlier.value, outlier.rationale or "", self.session_id
                        )
                else:
                    cleaned_data = phase1_results.pilot_data

                # Determine transformation method
                manual_method = None
                if self.manual_override_checkbox.value:
                    method_str = self.manual_method_radio.value
                    if method_str == "None (Parametric)":
                        manual_method = TransformationMethod.NONE
                    elif method_str == "Logarithmic":
                        manual_method = TransformationMethod.LOGARITHMIC
                    elif method_str == "Box-Cox":
                        manual_method = TransformationMethod.BOX_COX
                    elif method_str == "Yeo-Johnson":
                        manual_method = TransformationMethod.YEO_JOHNSON
                    else:  # Non-Parametric
                        manual_method = AnalysisMethod.NON_PARAMETRIC

                # Run transformation cascade
                if manual_method == AnalysisMethod.NON_PARAMETRIC:
                    # Special handling for manual non-parametric selection
                    from sample_size_calculator.normality import shapiro_wilk_test

                    p_value = shapiro_wilk_test(cleaned_data)
                    phase2_results = Phase2Results(
                        cleaned_data=cleaned_data,
                        shapiro_p_value=p_value,
                        transformation_method=TransformationMethod.NONE,
                        analysis_method=AnalysisMethod.NON_PARAMETRIC,
                        lambda_param=None,
                        manual_override=True,
                    )
                else:
                    phase2_results = transformation_cascade(cleaned_data, manual_method)

                self.module_v_state.complete_phase2(phase2_results)

                # Display results
                self.phase2_results_container.clear()
                with self.phase2_results_container:
                    ui.label("Normality Testing Results").classes("text-h6")
                    ui.label(
                        f"Shapiro-Wilk p-value: {phase2_results.shapiro_p_value:.4f}"
                    ).classes("text-body1")
                    ui.separator()

                    ui.label("Locked Method:").classes("text-body1 font-bold")
                    ui.label(
                        f"  Transformation: {phase2_results.transformation_method.value}"
                    ).classes("text-body1")
                    ui.label(
                        f"  Analysis Method: {phase2_results.analysis_method.value}"
                    ).classes("text-body1")

                    if phase2_results.lambda_param is not None:
                        ui.label(
                            f"  Lambda Parameter: {phase2_results.lambda_param:.4f}"
                        ).classes("text-body1")

                    if phase2_results.manual_override:
                        ui.label("  (Manual Override Applied)").classes(
                            "text-body2 text-warning"
                        )

                self.phase2_results_card.set_visibility(True)

                # Update method transparency
                self._display_method_transparency()

                # Log method lock
                self.logger.log_method_lock(
                    phase2_results.transformation_method.value,
                    phase2_results.lambda_param,
                    phase2_results.shapiro_p_value,
                    self.session_id,
                )

                # Enable Phase 3
                self._enforce_sequential_workflow()
                self.phase3_expansion.open()

                # Log phase transition
                self.logger.log_phase_transition(
                    "Phase_2", "Phase_3", "button_click", self.session_id
                )

                ui.notify("Phase 2 completed successfully", type="positive")

            except ValueError as e:
                self.logger.log_validation_error(
                    "phase2_validation",
                    str(e),
                    "phase2_inputs",
                    {"manual_override": self.manual_override_checkbox.value},
                    self.session_id,
                )
                ui.notify(f"Validation error: {e}", type="negative")
            except Exception as e:
                ui.notify(f"Processing error: {e}", type="negative")

        process_phase2_btn.on_click(handle_process_phase2)

    def _create_phase3_ui(self) -> None:
        """Create Phase 3 UI (sample size calculation)."""
        with ui.card().classes("w-full"):
            ui.label("Sample Size Calculation").classes("text-h6")
            ui.label(
                "Calculate the required sample size for final validation"
            ).classes("text-body2")

        # Calculate button
        with ui.row().classes("w-full"):
            calculate_phase3_btn = ui.button(
                "Calculate Required Sample Size", icon="calculate"
            ).classes("bg-primary")

        # Results display
        self.phase3_results_card = ui.card().classes("w-full")
        with self.phase3_results_card:
            self.phase3_results_container = ui.column().classes("w-full")
        self.phase3_results_card.set_visibility(False)

        # Phase 3 button handler
        def handle_calculate_phase3() -> None:
            """Handle Phase 3 calculation."""
            self.logger.log_button_click(
                "calculate_phase3", "Module_V", "Phase_3", self.session_id
            )

            try:
                if not self.module_v_state.phase2_complete:
                    ui.notify("Please complete Phase 2 first", type="warning")
                    return

                phase2_results = self.module_v_state.phase2_results
                spec_limits = self.module_v_state.spec_limits
                confidence = self.module_v_state.confidence
                reliability = self.module_v_state.reliability

                if (
                    phase2_results is None
                    or spec_limits is None
                    or confidence is None
                    or reliability is None
                ):
                    ui.notify("Missing required data from previous phases", type="negative")
                    return

                # Calculate capability margin
                k_margin = calculate_capability_margin(
                    phase2_results.cleaned_data,
                    spec_limits,
                    phase2_results.transformation_method,
                    phase2_results.lambda_param,
                )

                # Calculate required sample size
                phase3_results = calculate_required_sample_size(
                    k_margin,
                    confidence,
                    reliability,
                    spec_limits.spec_type,
                    phase2_results.analysis_method,
                )

                self.module_v_state.complete_phase3(phase3_results)

                # Display results
                self.phase3_results_container.clear()
                with self.phase3_results_container:
                    ui.label("Sample Size Calculation Results").classes("text-h6")
                    ui.label(f"Capability Margin (k_margin): {k_margin:.4f}").classes(
                        "text-body1"
                    )
                    ui.label(
                        f"Tolerance Factor (k_factor): {phase3_results.k_factor:.4f}"
                    ).classes("text-body1")
                    ui.separator()
                    ui.label(
                        f"Required Sample Size (N): {phase3_results.required_sample_size}"
                    ).classes("text-h4 text-primary")

                    # Display formula used
                    if phase2_results.analysis_method == AnalysisMethod.PARAMETRIC:
                        if spec_limits.spec_type == SpecificationType.ONE_SIDED:
                            formula = "One-Sided Tolerance Factor (Non-Central t-Distribution)"
                        else:
                            formula = "Two-Sided Tolerance Factor (Howe-Guenther Approximation)"
                    else:
                        if spec_limits.spec_type == SpecificationType.ONE_SIDED:
                            formula = "Non-Parametric One-Sided (Extreme Order Statistics)"
                        else:
                            formula = "Non-Parametric Two-Sided (Min/Max Order Statistics)"

                    ui.label(f"Formula Used: {formula}").classes("text-body2")

                self.phase3_results_card.set_visibility(True)

                # Update method transparency
                self._display_method_transparency()

                # Log calculation
                engine_hash = get_engine_hash()
                self.logger.log_calculation(
                    "sample_size_calculation",
                    {
                        "k_margin": k_margin,
                        "confidence": confidence,
                        "reliability": reliability,
                        "spec_type": spec_limits.spec_type.value,
                        "analysis_method": phase2_results.analysis_method.value,
                    },
                    {
                        "required_sample_size": phase3_results.required_sample_size,
                        "k_factor": phase3_results.k_factor,
                    },
                    engine_hash,
                    self.session_id,
                )

                # Enable Phase 4
                self._enforce_sequential_workflow()
                self.phase4_expansion.open()

                # Log phase transition
                self.logger.log_phase_transition(
                    "Phase_3", "Phase_4", "button_click", self.session_id
                )

                ui.notify("Phase 3 completed successfully", type="positive")

            except ValueError as e:
                self.logger.log_validation_error(
                    "phase3_validation",
                    str(e),
                    "phase3_calculation",
                    {},
                    self.session_id,
                )
                ui.notify(f"Calculation error: {e}", type="negative")
            except Exception as e:
                ui.notify(f"Calculation error: {e}", type="negative")

        calculate_phase3_btn.on_click(handle_calculate_phase3)

    def _create_phase4_ui(self) -> None:
        """Create Phase 4 UI (final validation data and tolerance limits)."""
        with ui.card().classes("w-full"):
            ui.label("Final Validation Dataset").classes("text-h6")

            self.final_data_input = (
                ui.textarea(
                    label="Final Validation Dataset (comma-separated values)",
                    placeholder="Enter N measurements as calculated in Phase 3",
                )
                .classes("w-full")
                .tooltip(
                    "Enter final validation measurements. "
                    "Must match the required sample size from Phase 3.",
                )
            )

        # Calculate button
        with ui.row().classes("w-full"):
            calculate_phase4_btn = ui.button(
                "Calculate Tolerance Limits", icon="rule"
            ).classes("bg-primary")

        # Results display
        self.phase4_results_card = ui.card().classes("w-full")
        with self.phase4_results_card:
            self.phase4_results_container = ui.column().classes("w-full")
        self.phase4_results_card.set_visibility(False)

        # Report generation button (initially hidden)
        self.v_report_btn_container = ui.row().classes("w-full")
        with self.v_report_btn_container:
            v_report_btn = ui.button("Generate PDF Report", icon="picture_as_pdf").classes(
                "bg-secondary"
            )
        self.v_report_btn_container.set_visibility(False)

        # Phase 4 button handler
        def handle_calculate_phase4() -> None:
            """Handle Phase 4 calculation."""
            self.logger.log_button_click(
                "calculate_phase4", "Module_V", "Phase_4", self.session_id
            )

            try:
                if not self.module_v_state.phase3_complete:
                    ui.notify("Please complete Phase 3 first", type="warning")
                    return

                # Parse final data
                final_data_str = self.final_data_input.value
                if not final_data_str:
                    ui.notify("Please enter final validation data", type="warning")
                    return

                final_data = [
                    float(x.strip()) for x in final_data_str.split(",") if x.strip()
                ]

                phase2_results = self.module_v_state.phase2_results
                phase3_results = self.module_v_state.phase3_results
                spec_limits = self.module_v_state.spec_limits

                if (
                    phase2_results is None
                    or phase3_results is None
                    or spec_limits is None
                ):
                    ui.notify("Missing required data from previous phases", type="negative")
                    return

                # Calculate tolerance limits
                phase4_results = calculate_tolerance_limits(
                    final_data, phase2_results, phase3_results, spec_limits
                )

                self.module_v_state.complete_phase4(phase4_results)

                # Display results
                self.phase4_results_container.clear()
                with self.phase4_results_container:
                    ui.label("Tolerance Limits & Validation Results").classes("text-h6")

                    # Tolerance limits
                    ui.label("Tolerance Limits (Original Space):").classes(
                        "text-body1 font-bold"
                    )
                    if "lower" in phase4_results.tolerance_limits:
                        ui.label(
                            f"  Lower: {phase4_results.tolerance_limits['lower']:.4f}"
                        ).classes("text-body1")
                    if "upper" in phase4_results.tolerance_limits:
                        ui.label(
                            f"  Upper: {phase4_results.tolerance_limits['upper']:.4f}"
                        ).classes("text-body1")

                    ui.separator()

                    # Specification limits
                    ui.label("Specification Limits:").classes("text-body1 font-bold")
                    if spec_limits.lsl is not None:
                        ui.label(f"  LSL: {spec_limits.lsl:.4f}").classes("text-body1")
                    if spec_limits.usl is not None:
                        ui.label(f"  USL: {spec_limits.usl:.4f}").classes("text-body1")

                    ui.separator()

                    # Pass/Fail
                    pass_fail_color = (
                        "text-positive" if phase4_results.pass_fail == "Pass" else "text-negative"
                    )
                    ui.label(f"Result: {phase4_results.pass_fail}").classes(
                        f"text-h5 {pass_fail_color}"
                    )

                    # Ppk (if available)
                    if phase4_results.ppk is not None:
                        ui.label(f"Process Capability (Ppk): {phase4_results.ppk:.4f}").classes(
                            "text-body1"
                        )

                self.phase4_results_card.set_visibility(True)

                # Show report button
                self.v_report_btn_container.set_visibility(True)

                # Log calculation
                engine_hash = get_engine_hash()
                self.logger.log_calculation(
                    "tolerance_limits",
                    {"final_data_size": len(final_data)},
                    {
                        "tolerance_limits": phase4_results.tolerance_limits,
                        "pass_fail": phase4_results.pass_fail,
                        "ppk": phase4_results.ppk,
                    },
                    engine_hash,
                    self.session_id,
                )

                ui.notify("Phase 4 completed successfully", type="positive")

            except ValueError as e:
                self.logger.log_validation_error(
                    "phase4_validation",
                    str(e),
                    "phase4_inputs",
                    {"final_data": self.final_data_input.value},
                    self.session_id,
                )
                ui.notify(f"Validation error: {e}", type="negative")
            except Exception as e:
                ui.notify(f"Calculation error: {e}", type="negative")

        calculate_phase4_btn.on_click(handle_calculate_phase4)

        # Report generation handler
        def handle_generate_v_report() -> None:
            """Generate PDF report for Module V."""
            self.logger.log_button_click(
                "generate_report_module_v", "Module_V", "Phase_4", self.session_id
            )

            try:
                if not self.module_v_state.phase4_complete:
                    ui.notify("Please complete all phases first", type="warning")
                    return

                # Get engine hash and validation state
                engine_hash = get_engine_hash()
                validation_state = is_validated_state()

                # Prepare report data
                phase2 = self.module_v_state.phase2_results
                phase3 = self.module_v_state.phase3_results
                phase4 = self.module_v_state.phase4_results
                spec_limits = self.module_v_state.spec_limits

                if phase2 is None or phase3 is None or phase4 is None or spec_limits is None:
                    ui.notify("Missing phase results", type="negative")
                    return

                inputs = {
                    "specification_type": spec_limits.spec_type.value,
                    "lsl": spec_limits.lsl,
                    "usl": spec_limits.usl,
                    "confidence": self.module_v_state.confidence,
                    "reliability": self.module_v_state.reliability,
                    "pilot_data_size": len(self.module_v_state.pilot_data or []),
                    "final_data_size": len(phase4.final_data),
                }

                results = {
                    "transformation_method": phase2.transformation_method.value,
                    "analysis_method": phase2.analysis_method.value,
                    "lambda_param": phase2.lambda_param,
                    "required_sample_size": phase3.required_sample_size,
                    "k_margin": phase3.k_margin,
                    "k_factor": phase3.k_factor,
                    "tolerance_limits": phase4.tolerance_limits,
                    "pass_fail": phase4.pass_fail,
                    "ppk": phase4.ppk,
                }

                # Build method path
                method_path = f"Specification: {spec_limits.spec_type.value}\n"
                method_path += f"Transformation: {phase2.transformation_method.value}\n"
                method_path += f"Analysis: {phase2.analysis_method.value}\n"
                if phase2.lambda_param is not None:
                    method_path += f"Lambda: {phase2.lambda_param:.4f}\n"

                report_data = CalculationReport(
                    timestamp=datetime.now().isoformat(),
                    module="Module V",
                    inputs=inputs,
                    results=results,
                    engine_hash=engine_hash,
                    validation_state=validation_state,
                    method_path=method_path,
                )

                # Generate PDF
                pdf_bytes = ReportGenerator.generate_user_report(report_data)

                # Log report generation
                self.logger.log_report_generation(
                    "user_calculation", engine_hash, validation_state, self.session_id
                )

                # Trigger download
                ui.download(
                    pdf_bytes,
                    f"sample_size_report_module_v_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                )
                ui.notify("Report generated successfully", type="positive")

            except Exception as e:
                ui.notify(f"Report generation error: {e}", type="negative")

        v_report_btn.on_click(handle_generate_v_report)

    def _enforce_sequential_workflow(self) -> None:
        """Enable/disable phase controls based on completion status."""
        # Phase 2
        if self.module_v_state.is_phase_enabled(2):
            self.phase2_expansion.enable()
            # Populate outlier exclusion UI
            if self.module_v_state.phase1_results:
                self._populate_outlier_exclusion_ui()
        else:
            self.phase2_expansion.disable()

        # Phase 3
        if self.module_v_state.is_phase_enabled(3):
            self.phase3_expansion.enable()
        else:
            self.phase3_expansion.disable()

        # Phase 4
        if self.module_v_state.is_phase_enabled(4):
            self.phase4_expansion.enable()
        else:
            self.phase4_expansion.disable()

    def _populate_outlier_exclusion_ui(self) -> None:
        """Populate outlier exclusion UI with detected outliers."""
        phase1_results = self.module_v_state.phase1_results
        if phase1_results is None or not phase1_results.outliers:
            self.outlier_exclusion_container.clear()
            with self.outlier_exclusion_container:
                ui.label("No outliers detected").classes("text-body1")
            return

        self.outlier_exclusion_container.clear()
        with self.outlier_exclusion_container:
            for i, outlier in enumerate(phase1_results.outliers):
                with ui.card().classes("w-full bg-yellow-50"):
                    with ui.row().classes("w-full items-center"):
                        ui.label(f"Outlier Value: {outlier.value}").classes(
                            "text-body1 font-bold"
                        )

                        # Exclude checkbox
                        exclude_cb = ui.checkbox("Exclude").bind_value(
                            outlier, "is_excluded"
                        )

                    # Rationale input
                    rationale_input = (
                        ui.textarea(
                            label="Engineering Rationale (required if excluded)",
                            placeholder="e.g., Measurement error, sensor malfunction, process upset",
                        )
                        .classes("w-full")
                        .bind_value(outlier, "rationale")
                    )

                    # Show/hide rationale based on checkbox
                    def update_rationale_visibility(
                        checkbox: ui.checkbox, textarea: ui.textarea
                    ) -> None:
                        """Update rationale input visibility."""

                        def toggle() -> None:
                            textarea.set_visibility(checkbox.value)

                        checkbox.on('change', toggle)
                        textarea.set_visibility(checkbox.value)

                    update_rationale_visibility(exclude_cb, rationale_input)

    def _display_method_transparency(self) -> None:
        """Display active mathematical path."""
        phase2 = self.module_v_state.phase2_results
        phase3 = self.module_v_state.phase3_results
        spec_limits = self.module_v_state.spec_limits

        if phase2 is None:
            return

        # Build method path string
        method_path = "Active Mathematical Path:\n"
        method_path += "━" * 80 + "\n"

        if spec_limits:
            method_path += f"Specification Type: {spec_limits.spec_type.value}\n"

        method_path += f"Transformation: {phase2.transformation_method.value}"
        if phase2.lambda_param is not None:
            method_path += f" (λ = {phase2.lambda_param:.4f})"
        method_path += "\n"

        method_path += f"Analysis Method: {phase2.analysis_method.value}\n"

        if phase3 and phase2.analysis_method == AnalysisMethod.PARAMETRIC:
            if spec_limits and spec_limits.spec_type == SpecificationType.ONE_SIDED:
                method_path += "Tolerance Factor: k1 (Non-Central t-Distribution)\n"
            else:
                method_path += "Tolerance Factor: k2 (Howe-Guenther Approximation)\n"

        if phase2.transformation_method != TransformationMethod.NONE:
            if phase2.transformation_method == TransformationMethod.LOGARITHMIC:
                method_path += "Formula: Limits = exp(mean_log ± k * std_log)\n"
            elif phase2.transformation_method == TransformationMethod.BOX_COX:
                method_path += "Formula: Limits = (λ * y + 1)^(1/λ) where y = mean ± k * std\n"
            elif phase2.transformation_method == TransformationMethod.YEO_JOHNSON:
                method_path += "Formula: Limits = inverse_YJ(mean_yj ± k * std_yj)\n"

        method_path += "━" * 80

        # Update display
        self.method_transparency_label.set_text(method_path)
        self.method_transparency_card.set_visibility(True)


def create_ui() -> None:
    """Create and run the NiceGUI application."""
    controller = UIController()
    controller.create_app()
    ui.run(title="Sample Size Calculator", port=8080, reload=False)


if __name__ == "__main__":
    create_ui()
