"""NiceGUI-based web interface controller for the Sample Size Calculator.

This module provides the complete user interface for both Module A (attribute data)
and Module V (variable data) analysis, with session management, workflow enforcement,
and comprehensive audit logging.
"""

import io
import math
import uuid
from datetime import datetime
from typing import Any

import anyio
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

matplotlib.use("Agg")  # Use non-interactive backend for NiceGUI

from nicegui import ui

from sample_size_calculator.audit_logger import AuditLogger
from sample_size_calculator.calculations import CalculationEngine
from sample_size_calculator.full_report_generator import FullReportGenerator
from sample_size_calculator.hash_verifier import get_engine_hash, is_validated_state
from sample_size_calculator.jupyter_manager import JupyterManager
from sample_size_calculator.models import (
    AnalysisMethod,
    AttributeInputs,
    CalculationReport,
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
from sample_size_calculator.report_paths import get_full_report_path, save_report
from sample_size_calculator.tolerance import (
    calculate_capability_margin,
    calculate_required_sample_size,
    calculate_tolerance_limits,
)
from sample_size_calculator.transformations import transformation_cascade
from sample_size_calculator.validation_runner import ValidationRunner


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
        self.estimated_mean: float | None = None
        self.estimated_std: float | None = None

        # Store initial data from Phase 1 (for preservation tests)
        self.initial_data: list[float] | None = None

    def complete_phase1(self, results: Phase1Results | list[float]) -> None:
        """Mark Phase 1 complete and enable Phase 2.

        Args:
            results: Either Phase1Results object or list of initial data
        """
        # Handle both Phase1Results and raw data list for compatibility
        if isinstance(results, Phase1Results):
            self.phase1_results = results
            self.initial_data = results.pilot_data
        else:
            # Raw data list (for backward compatibility with tests)
            self.initial_data = results
            self.phase1_results = None

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
        """Check if a phase is enabled.

        A phase is enabled only if all previous phases are complete.
        This ensures proper sequential workflow enforcement.
        """
        if phase == 1:
            return True
        elif phase == 2:
            return self.phase1_complete
        elif phase == 3:
            return self.phase1_complete and self.phase2_complete
        elif phase == 4:
            return (
                self.phase1_complete and self.phase2_complete and self.phase3_complete
            )
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

        # JupyterLab manager
        self.jupyter_manager = JupyterManager()

        # Validation button reference (will be set in create_app)
        self.validation_button: ui.button | None = None

    def _generate_session_id(self) -> str:
        """Generate unique session identifier using uuid4."""
        return str(uuid.uuid4())

    def _update_validation_button_color(self) -> None:
        """Update validation button color based on validation state."""
        if self.validation_button is None:
            return

        if is_validated_state():
            self.validation_button.props("color=positive text-color=white")
        else:
            self.validation_button.props("color=negative text-color=white")

    def create_app(self) -> None:
        """Create the main NiceGUI application with tabs."""
        ui.page_title("Sample Size Calculator")

        with ui.header().classes("items-center justify-between w-full"):
            with ui.row().classes("items-center gap-4"):
                ui.label("Sample Size Calculator").classes("text-h4")
                ui.label(
                    "Medical Device Design Verification & Process Validation"
                ).classes("text-subtitle2")

            # Validation button in header - solid background with white text
            self.validation_button = ui.button(
                "Run Full Validation (IQ/OQ/PQ)",
                on_click=self._handle_validation_button_click,
                icon="verified",
            )
            # Set background color and white text using Quasar classes
            self.validation_button.classes("rounded")
            if is_validated_state():
                self.validation_button.classes("bg-green-6 text-white")
            else:
                self.validation_button.classes("bg-red-6 text-white")

        with ui.tabs().classes("w-full") as tabs:
            module_a_tab = ui.tab("Module Attribute")
            module_v_tab = ui.tab("Module Variable")
            examples_tab = ui.tab("Examples")
            help_tab = ui.tab("Help")

        with ui.tab_panels(tabs, value=module_a_tab).classes("w-full"):
            with ui.tab_panel(module_a_tab):
                self.create_module_a_tab()

            with ui.tab_panel(module_v_tab):
                self.create_module_v_tab()

            with ui.tab_panel(examples_tab):
                self.create_examples_tab()

            with ui.tab_panel(help_tab):
                self.create_help_tab()

    def create_module_a_tab(self) -> None:
        """Create Module A UI tab for attribute data analysis."""
        ui.label("Module A: Attribute Data Analysis").classes("text-h5")
        ui.label("Calculate sample sizes for binary Pass/Fail test scenarios").classes(
            "text-subtitle2"
        )
        ui.separator()

        # Input fields
        with ui.card().classes("w-full"):
            ui.label("Input Parameters").classes("text-h6")

            # Confidence input
            with ui.row().classes("w-full items-center"):
                confidence_input = (
                    ui.number(
                        label="Reliability Level (%)",
                        value=95.0,
                        min=50.00,
                        max=99.95,
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
                        min=50.00,
                        max=99.95,
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

            # Population size input (optional)
            with ui.row().classes("w-full items-center"):
                population_size_input = (
                    ui.number(
                        label="Population Size (N)",
                        value=None,
                        min=1,
                        step=1,
                        precision=0,
                    )
                    .classes("w-64")
                    .tooltip(
                        "Total population size for finite population correction. "
                        "Leave empty to skip correction.",
                    )
                )
                ui.label("(Optional: leave empty to skip correction)").classes(
                    "text-caption"
                )

        # Calculate button
        with ui.row().classes("w-full"):
            calculate_btn = ui.button(
                "Calculate Sample Size", icon="calculate"
            ).classes("bg-primary")

        # Results display
        results_card = ui.card().classes("w-full")
        with results_card:
            results_container = ui.column().classes("w-full")

        # Report generation buttons (initially hidden)
        report_btn_container = ui.row().classes("w-full gap-2")
        with report_btn_container:
            report_btn = ui.button(
                "Generate PDF Report", icon="picture_as_pdf"
            ).classes("bg-secondary")
            full_report_btn = (
                ui.button("Generate Full Report", icon="description")
                .classes("bg-accent")
                .tooltip(
                    "Generate comprehensive report including calculation, validation status, and audit trail"
                )
            )
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
                population_size = population_size_input.value

                if confidence is None or reliability is None:
                    ui.notify(
                        "Please enter confidence and reliability values",
                        type="negative",
                        timeout=0,
                    )
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
                    # Sensitivity analysis with optional population correction
                    if population_size is not None and population_size > 1:
                        results = (
                            CalculationEngine.sensitivity_analysis_with_correction(
                                confidence, reliability, int(population_size)
                            )
                        )
                    else:
                        results = (
                            CalculationEngine.sensitivity_analysis_with_correction(
                                confidence, reliability, None
                            )
                        )

                    # Store results
                    self.module_a_results = {
                        "type": "sensitivity",
                        "confidence": confidence,
                        "reliability": reliability,
                        "results": results,
                        "population_size": int(population_size)
                        if population_size is not None
                        else None,
                    }

                    # Display results
                    results_container.clear()
                    with results_container:
                        ui.label("Calculation Results").classes("text-h6")
                        ui.label("Method: Sensitivity Analysis").classes("text-body1")
                        ui.separator()

                        # Create table with original and corrected sample sizes
                        if population_size is not None and population_size > 1:
                            # Show both original and corrected values
                            column_defs = [
                                {"headerName": "Allowable Failures (c)", "field": "c"},
                                {
                                    "headerName": "Sample Size (Original)",
                                    "field": "n_original",
                                },
                                {
                                    "headerName": "Sample Size (Corrected for N={})".format(
                                        int(population_size)
                                    ),
                                    "field": "n_corrected",
                                },
                            ]
                            row_data = [
                                {
                                    "c": c,
                                    "n_original": n_orig,
                                    "n_corrected": round(n_corr, 2),
                                }
                                for c, n_orig, n_corr in results
                            ]
                        else:
                            # Show only original values (no correction)
                            column_defs = [
                                {"headerName": "Allowable Failures (c)", "field": "c"},
                                {
                                    "headerName": "Required Sample Size (n)",
                                    "field": "n",
                                },
                            ]
                            row_data = [{"c": c, "n": n} for c, n, _ in results]

                        table_data = {"columnDefs": column_defs, "rowData": row_data}
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
                        n = CalculationEngine.success_run_theorem(
                            confidence, reliability
                        )
                        method = "Success Run Theorem"
                    else:
                        n = CalculationEngine.cumulative_binomial(
                            confidence, reliability, inputs.allowable_failures
                        )
                        method = "Cumulative Binomial"

                    # Apply finite population correction if applicable
                    n_original = n
                    if population_size is not None and population_size > 1:
                        n_corrected = CalculationEngine.finite_population_correction(
                            n, int(population_size)
                        )
                        method_display = f"{method} (FPC applied)"
                    else:
                        n_corrected = None
                        method_display = method

                    # Store results
                    self.module_a_results = {
                        "type": "single",
                        "confidence": confidence,
                        "reliability": reliability,
                        "allowable_failures": inputs.allowable_failures,
                        "sample_size_original": n_original,
                        "sample_size_corrected": n_corrected,
                        "population_size": int(population_size)
                        if population_size is not None
                        else None,
                        "method": method_display,
                    }

                    # Display results
                    results_container.clear()
                    with results_container:
                        ui.label("Calculation Results").classes("text-h6")
                        ui.label(f"Method: {method_display}").classes("text-body1")
                        ui.separator()
                        ui.label(
                            f"Original Sample Size (for large populations): {n_original}"
                        ).classes("text-body2 text-secondary")
                        if n_corrected is not None:
                            ui.label(
                                f"Corrected Sample Size (N={int(population_size)}): {round(n_corrected, 2)}"
                            ).classes("text-h4 text-primary")
                        else:
                            ui.label(f"Required Sample Size (n): {n_original}").classes(
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
                ui.notify(f"Validation error: {e}", type="negative", timeout=0)
            except Exception as e:
                ui.notify(f"Calculation error: {e}", type="negative", timeout=0)

        calculate_btn.on_click(handle_calculate)

        # Report generation handler
        def handle_generate_report() -> None:
            """Generate PDF report for Module A."""
            ui.notify("📝 Generating Module A PDF report...", type="info")
            self.logger.log_button_click(
                "generate_report_module_a", "Module_A", None, self.session_id
            )

            try:
                if self.module_a_results is None:
                    ui.notify("No results to report", type="warning", timeout=0)
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
                    results_list = self.module_a_results.get("results", [])

                    # Format results to show both original and corrected
                    formatted_results = []
                    for item in results_list:
                        if len(item) == 3:  # (c, n_original, n_corrected)
                            c, n_orig, n_corr = item
                            if n_corr is not None:
                                formatted_results.append(
                                    f"c={c}: n_original={n_orig}, n_corrected={round(n_corr, 2)}"
                                )
                            else:
                                formatted_results.append(f"c={c}: n={n_orig}")
                        else:  # (c, n)
                            c, n = item
                            formatted_results.append(f"c={c}: n={n}")

                    # Get population size
                    population_size = self.module_a_results.get("population_size")

                    results = {
                        "method": "Sensitivity Analysis",
                        "results": "\n".join(formatted_results),
                        "population_size": int(population_size)
                        if population_size is not None
                        else None,
                    }
                    method_path = "Sensitivity Analysis: Success Run Theorem and Cumulative Binomial"
                else:
                    inputs = {
                        "confidence": self.module_a_results["confidence"],
                        "reliability": self.module_a_results["reliability"],
                        "allowable_failures": self.module_a_results[
                            "allowable_failures"
                        ],
                    }
                    sample_size_original = self.module_a_results.get(
                        "sample_size_original"
                    )
                    sample_size_corrected = self.module_a_results.get(
                        "sample_size_corrected"
                    )

                    results = {
                        "method": self.module_a_results["method"],
                        "sample_size_original": sample_size_original,
                        "sample_size_corrected": sample_size_corrected,
                    }

                    # Include population size if correction was applied
                    if self.module_a_results.get("population_size") is not None:
                        results["population_size"] = self.module_a_results[
                            "population_size"
                        ]
                        if sample_size_corrected is not None:
                            method_path = f"{self.module_a_results['method']} (FPC: N={int(self.module_a_results['population_size'])})"
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

                # Generate PDF and save to reports directory
                pdf_bytes, report_path = ReportGenerator.generate_user_report(
                    report_data
                )

                # Log report generation
                self.logger.log_report_generation(
                    "user_calculation", engine_hash, validation_state, self.session_id
                )

                # Display report file path in UI
                ui.notify(
                    f"Report saved to: {report_path}", type="positive", position="top"
                )

                # Trigger download
                ui.download(
                    pdf_bytes,
                    f"sample_size_report_module_a_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                )

                # Log PDF generation
                self.logger.log_report_generation(
                    "Module A PDF Report",
                    report_path,
                    validation_state,
                    self.session_id,
                )
                ui.notify("✅ Module A PDF report saved and logged", type="positive")

            except Exception as e:
                ui.notify(f"Report generation error: {e}", type="negative", timeout=0)

        report_btn.on_click(handle_generate_report)

        # Full report generation handler
        def handle_generate_full_report() -> None:
            """Generate comprehensive full report for Module A."""
            ui.notify("📝 Generating Module A full report...", type="info")
            self.logger.log_button_click(
                "generate_full_report_module_a", "Module_A", None, self.session_id
            )

            try:
                if self.module_a_results is None:
                    ui.notify("No results to report", type="warning", timeout=0)
                    return

                # Get engine hash and validation state
                engine_hash = get_engine_hash()
                validation_state = is_validated_state()

                # Prepare report data (same as regular report)
                if self.module_a_results["type"] == "sensitivity":
                    inputs = {
                        "confidence": self.module_a_results["confidence"],
                        "reliability": self.module_a_results["reliability"],
                        "allowable_failures": "Sensitivity Analysis (c=0,1,2,3)",
                    }
                    results_list = self.module_a_results.get("results", [])

                    # Format results to show both original and corrected
                    formatted_results = []
                    for item in results_list:
                        if len(item) == 3:  # (c, n_original, n_corrected)
                            c, n_orig, n_corr = item
                            if n_corr is not None:
                                formatted_results.append(
                                    f"c={c}: n_original={n_orig}, n_corrected={round(n_corr, 2)}"
                                )
                            else:
                                formatted_results.append(f"c={c}: n={n_orig}")
                        else:  # (c, n)
                            c, n = item
                            formatted_results.append(f"c={c}: n={n}")

                    # Get population size
                    population_size = self.module_a_results.get("population_size")

                    results = {
                        "method": "Sensitivity Analysis",
                        "results": "\n".join(formatted_results),
                        "population_size": int(population_size)
                        if population_size is not None
                        else None,
                    }
                    method_path = "Sensitivity Analysis: Success Run Theorem and Cumulative Binomial"
                else:
                    inputs = {
                        "confidence": self.module_a_results["confidence"],
                        "reliability": self.module_a_results["reliability"],
                        "allowable_failures": self.module_a_results[
                            "allowable_failures"
                        ],
                    }
                    sample_size_original = self.module_a_results.get(
                        "sample_size_original"
                    )
                    sample_size_corrected = self.module_a_results.get(
                        "sample_size_corrected"
                    )

                    results = {
                        "method": self.module_a_results["method"],
                        "sample_size_original": sample_size_original,
                        "sample_size_corrected": sample_size_corrected,
                    }

                    # Include population size if correction was applied
                    if self.module_a_results.get("population_size") is not None:
                        results["population_size"] = self.module_a_results[
                            "population_size"
                        ]
                        if sample_size_corrected is not None:
                            method_path = f"{self.module_a_results['method']} (FPC: N={int(self.module_a_results['population_size'])})"
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

                # Generate full report PDF
                full_report_bytes = FullReportGenerator.generate_full_report(
                    calculation_report=report_data,
                    session_id=self.session_id,
                    log_dir="logs",
                    validation_reports_dir="reports/validation",
                )

                # Save to reports/full/ directory
                report_path = get_full_report_path()
                saved_path = save_report(full_report_bytes, report_path)

                # Sign the PDF with hash for tamper detection
                try:
                    from sample_size_calculator.pdf_signature import PDFSignature

                    signature = PDFSignature.sign_pdf(full_report_bytes, engine_hash)
                    PDFSignature.save_signature(saved_path, signature)
                except Exception:
                    pass

                # Log report generation
                self.logger.log_report_generation(
                    "full_report", engine_hash, validation_state, self.session_id
                )

                # Display report file path in UI
                ui.notify(
                    f"Full report saved to: {saved_path}",
                    type="positive",
                    position="top",
                    timeout=5000,
                )

                # Trigger download
                ui.download(
                    full_report_bytes,
                    f"full_report_module_a_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                )

                # Log PDF generation
                self.logger.log_report_generation(
                    "Module A Full Report",
                    saved_path,
                    validation_state,
                    self.session_id,
                )
                ui.notify(
                    "✅ Module A full report generated successfully", type="positive"
                )

            except Exception as e:
                ui.notify(
                    f"Full report generation error: {e}", type="negative", timeout=0
                )

        full_report_btn.on_click(handle_generate_full_report)

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
        with ui.expansion(
            "Phase 1: Specification Definition & Pilot Data", icon="looks_one"
        ).classes("w-full") as phase1_expansion:
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

        # Reset button for Module V
        with ui.row().classes("w-full mt-4"):
            reset_btn = ui.button("Reset All", icon="refresh").classes(
                "bg-warning text-dark"
            )

        # Reset button handler - must be defined before _enforce_sequential_workflow to capture expansion vars
        def handle_reset_v() -> None:
            """Reset Module V to initial state."""
            self.logger.log_button_click(
                "reset_module_v", "Module_V", None, self.session_id
            )

            # Clear all inputs
            self.lsl_input.value = None
            self.usl_input.value = None
            self.v_confidence_input.value = 95.0
            self.v_reliability_input.value = 95.0
            self.input_method_radio.value = "Enter Pilot Dataset"
            self.pilot_data_input.value = ""
            if hasattr(self, "estimated_mean_input"):
                self.estimated_mean_input.value = None
            if hasattr(self, "estimated_std_input"):
                self.estimated_std_input.value = None

            # Clear all results cards
            self.phase1_results_card.set_visibility(False)

            # Reset phase expansion states
            phase2_expansion.close()
            phase3_expansion.close()
            phase4_expansion.close()

            ui.notify("Module V reset to initial state", type="info")

        reset_btn.on_click(handle_reset_v)

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
                        min=50.00,
                        max=99.95,
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
                        min=50.00,
                        max=99.95,
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

            # Input method selector
            self.input_method_radio = (
                ui.radio(
                    ["Enter Pilot Dataset", "Enter Estimated Statistics"],
                    value="Enter Pilot Dataset",
                )
                .props("inline")
                .tooltip(
                    "Choose how to provide pilot data: "
                    "enter actual measurements or estimated mean/std from prior knowledge"
                )
            )

            # Dataset input (default visible)
            with ui.column().classes("w-full") as self.dataset_input_container:
                self.pilot_data_input = (
                    ui.textarea(
                        label="Pilot Dataset (comma-separated values)",
                        placeholder="e.g., 10.5, 12.3, 11.8, 13.2, 12.1",
                    )
                    .classes("w-full")
                    .tooltip(
                        "Enter pilot data measurements separated by commas. "
                        "Minimum 3 values required. Recommended: 12-30 samples. Format: 10.5, ...",
                    )
                )

            # Statistics input (initially hidden)
            with ui.column().classes("w-full") as self.statistics_input_container:
                with ui.row().classes("w-full"):
                    self.estimated_mean_input = (
                        ui.number(
                            label="Estimated Mean",
                            value=None,
                            min=0.0001,
                            step=0.1,
                        )
                        .classes("w-64")
                        .tooltip(
                            "The estimated mean value from prior knowledge or historical data"
                        )
                    )

                    self.estimated_std_input = (
                        ui.number(
                            label="Estimated Standard Deviation",
                            value=None,
                            min=0.0001,
                            step=0.1,
                        )
                        .classes("w-64")
                        .tooltip("The estimated standard deviation (must be > 0)")
                    )

            self.statistics_input_container.set_visibility(False)

            # Handler to toggle input visibility and clear data
            def handle_input_method_change() -> None:
                """Toggle between dataset and statistics input."""
                if self.input_method_radio.value == "Enter Pilot Dataset":
                    self.dataset_input_container.set_visibility(True)
                    self.statistics_input_container.set_visibility(False)
                    # Clear statistics inputs
                    self.estimated_mean_input.value = None
                    self.estimated_std_input.value = None
                else:
                    self.dataset_input_container.set_visibility(False)
                    self.statistics_input_container.set_visibility(True)
                    # Clear dataset input
                    self.pilot_data_input.value = ""

            self.input_method_radio.on_value_change(handle_input_method_change)

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
                # Validate specification limits
                spec_type = SpecificationType(self.spec_type_radio.value)
                lsl = self.lsl_input.value
                usl = self.usl_input.value

                spec_limits = SpecificationLimits(spec_type=spec_type, lsl=lsl, usl=usl)

                # Store for later phases
                self.module_v_state.spec_limits = spec_limits
                self.module_v_state.confidence = self.v_confidence_input.value
                self.module_v_state.reliability = self.v_reliability_input.value

                # Check input method
                input_method = self.input_method_radio.value

                if input_method == "Enter Pilot Dataset":
                    # Parse pilot data
                    pilot_data_str = self.pilot_data_input.value
                    if not pilot_data_str:
                        ui.notify("Please enter pilot data", type="warning", timeout=0)
                        return

                    pilot_data = [
                        float(x.strip()) for x in pilot_data_str.split(",") if x.strip()
                    ]

                    if len(pilot_data) < 3:
                        ui.notify(
                            "Pilot dataset must contain at least 3 data points",
                            type="negative",
                            timeout=0,
                        )
                        return

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

                else:  # Enter Estimated Statistics
                    # Validate estimated statistics
                    estimated_mean = self.estimated_mean_input.value
                    estimated_std = self.estimated_std_input.value

                    if estimated_mean is None:
                        ui.notify(
                            "Please enter estimated mean",
                            type="warning",
                        )
                        return

                    if estimated_std is None:
                        ui.notify(
                            "Please enter estimated standard deviation",
                            type="warning",
                            timeout=0,
                        )
                        return

                    if estimated_std <= 0:
                        ui.notify(
                            "Estimated standard deviation must be greater than 0",
                            type="negative",
                            timeout=0,
                        )
                        return

                    # Store estimated statistics
                    self.module_v_state.pilot_data = None
                    self.module_v_state.estimated_mean = estimated_mean
                    self.module_v_state.estimated_std = estimated_std

                    # Create Phase1Results with no outliers (no dataset to analyze)
                    phase1_results = Phase1Results(
                        pilot_data=[],
                        outliers=[],
                        q1=0.0,
                        q3=0.0,
                        iqr=0.0,
                    )
                    self.module_v_state.complete_phase1(phase1_results)

                    # Display results
                    self.phase1_results_container.clear()
                    with self.phase1_results_container:
                        ui.label("Estimated Statistics").classes("text-h6")
                        ui.label(f"Mean: {estimated_mean:.4f}").classes("text-body1")
                        ui.label(f"Standard Deviation: {estimated_std:.4f}").classes(
                            "text-body1"
                        )
                        ui.separator()
                        ui.label(
                            "Using estimated statistics (no outlier detection performed)"
                        ).classes("text-body2 text-info")
                        ui.separator()
                        ui.label(
                            "Note: Phase 2 (normality testing) is not applicable for estimated statistics. "
                            "You must enable manual override and select an analysis method in Phase 2 before proceeding to Phase 3."
                        ).classes("text-body2 text-info")

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
                        "input_method": self.input_method_radio.value,
                        "pilot_data": self.pilot_data_input.value
                        if self.input_method_radio.value == "Enter Pilot Dataset"
                        else None,
                        "estimated_mean": self.estimated_mean_input.value
                        if self.input_method_radio.value == "Enter Estimated Statistics"
                        else None,
                        "estimated_std": self.estimated_std_input.value
                        if self.input_method_radio.value == "Enter Estimated Statistics"
                        else None,
                        "spec_type": self.spec_type_radio.value,
                        "lsl": self.lsl_input.value,
                        "usl": self.usl_input.value,
                    },
                    self.session_id,
                )
                ui.notify(f"Validation error: {e}", type="negative", timeout=0)
            except Exception as e:
                ui.notify(f"Analysis error: {e}", type="negative", timeout=0)

        analyze_phase1_btn.on_click(handle_analyze_phase1)

    def _create_phase2_ui(self) -> None:
        """Create Phase 2 UI (outlier exclusion and transformation cascade)."""
        # Add conditional message for estimated statistics
        self.phase2_estimated_stats_notice = ui.card().classes("w-full bg-blue-50")
        with self.phase2_estimated_stats_notice:
            ui.label(
                "Using Estimated Statistics: Normality testing is not applicable. "
                "Please enable manual override and select your analysis method below."
            ).classes("text-body1")
        self.phase2_estimated_stats_notice.set_visibility(False)

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
                    "None/Parametric",
                    "Logarithmic",
                    "Box-Cox",
                    "Yeo-Johnson",
                    "Non-Parametric/Wilks",
                ],
                value="None/Parametric",
            ).props("inline")
            self.manual_method_radio.set_visibility(False)

            def toggle_manual_method() -> None:
                """Toggle manual method selector visibility."""
                self.manual_method_radio.set_visibility(
                    self.manual_override_checkbox.value
                )

            self.manual_override_checkbox.on(
                "update:model-value", lambda e: toggle_manual_method()
            )

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

        # Diagnostic plots display
        self.phase2_plots_card = ui.card().classes("w-full")
        with self.phase2_plots_card:
            ui.label("Normality Diagnostic Plots").classes("text-h6")
            with ui.row().classes("w-full"):
                with ui.column().classes("w-1/3"):
                    self.qq_plot_image = ui.image().classes("w-full")
                with ui.column().classes("w-1/3"):
                    self.pp_plot_image = ui.image().classes("w-full")
                with ui.column().classes("w-1/3"):
                    self.imr_plot_image = ui.image().classes("w-full")
        self.phase2_plots_card.set_visibility(False)

        # Phase 2 button handler
        def handle_process_phase2() -> None:
            """Handle Phase 2 processing."""
            self.logger.log_button_click(
                "process_phase2", "Module_V", "Phase_2", self.session_id
            )

            try:
                if not self.module_v_state.phase1_complete:
                    ui.notify(
                        "Please complete Phase 1 first", type="warning", timeout=0
                    )
                    return

                # Get outlier exclusions
                phase1_results = self.module_v_state.phase1_results
                if phase1_results is None:
                    ui.notify("Phase 1 results not found", type="negative", timeout=0)
                    return

                # Check if using estimated statistics (no pilot data)
                if (
                    not phase1_results.pilot_data
                ):  # Empty list means estimated statistics
                    # Show notice
                    self.phase2_estimated_stats_notice.set_visibility(True)

                    # Skip outlier handling and transformation cascade
                    # User must manually select analysis method
                    if not self.manual_override_checkbox.value:
                        ui.notify(
                            "For estimated statistics, please enable manual override and select analysis method",
                            type="warning",
                        )
                        return

                    # Determine transformation method from manual selection
                    method_str = self.manual_method_radio.value
                    if method_str == "None/Parametric":
                        transformation_method = TransformationMethod.NONE
                        analysis_method = AnalysisMethod.PARAMETRIC
                    elif method_str == "Logarithmic":
                        transformation_method = TransformationMethod.LOGARITHMIC
                        analysis_method = AnalysisMethod.PARAMETRIC
                    elif method_str == "Box-Cox":
                        transformation_method = TransformationMethod.BOX_COX
                        analysis_method = AnalysisMethod.PARAMETRIC
                    elif method_str == "Yeo-Johnson":
                        transformation_method = TransformationMethod.YEO_JOHNSON
                        analysis_method = AnalysisMethod.PARAMETRIC
                    else:  # Non-Parametric
                        transformation_method = TransformationMethod.NONE
                        analysis_method = AnalysisMethod.NON_PARAMETRIC

                    # Create Phase2Results with user-selected method
                    phase2_results = Phase2Results(
                        cleaned_data=[],  # Empty list for estimated statistics
                        shapiro_p_value=0.0,  # Not applicable
                        transformation_method=transformation_method,
                        analysis_method=analysis_method,
                        lambda_param=None,  # Not applicable for estimated statistics
                        manual_override=True,
                    )
                else:
                    # Pilot dataset case - existing logic
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
                                    timeout=0,
                                )
                                return

                        cleaned_data = apply_exclusions(
                            phase1_results, excluded_outliers
                        )

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
                        if method_str == "None/Parametric":
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

                        _, p_value = shapiro_wilk_test(cleaned_data)
                        phase2_results = Phase2Results(
                            cleaned_data=cleaned_data,
                            shapiro_p_value=p_value,
                            transformation_method=TransformationMethod.NONE,
                            analysis_method=AnalysisMethod.NON_PARAMETRIC,
                            lambda_param=None,
                            manual_override=True,
                        )
                    else:
                        phase2_results = transformation_cascade(
                            cleaned_data, manual_method
                        )

                self.module_v_state.complete_phase2(phase2_results)

                # Display results
                self.phase2_results_container.clear()
                with self.phase2_results_container:
                    ui.label("Normality Testing Results").classes("text-h6")

                    # Perform both normality tests if we have actual data
                    if phase2_results.cleaned_data:
                        from sample_size_calculator.normality import (
                            anderson_darling_test,
                            shapiro_wilk_test,
                        )

                        # Shapiro-Wilk test
                        sw_statistic, sw_p_value = shapiro_wilk_test(
                            phase2_results.cleaned_data
                        )
                        ui.label(
                            f"Shapiro-Wilk: statistic={sw_statistic:.4f}, p-value={sw_p_value:.4f}"
                        ).classes("text-body1")

                        # Anderson-Darling test
                        ad_statistic, ad_critical_values, ad_sig_levels = (
                            anderson_darling_test(phase2_results.cleaned_data)
                        )
                        critical_str = ", ".join(
                            [f"{cv:.3f}" for cv in ad_critical_values]
                        )
                        sig_str = ", ".join([f"{sl:.1f}%" for sl in ad_sig_levels])
                        ui.label(
                            f"Anderson-Darling: statistic={ad_statistic:.4f}"
                        ).classes("text-body1")
                        ui.label(
                            f"  Critical values at [{sig_str}]: [{critical_str}]"
                        ).classes("text-body2")
                    else:
                        # For estimated statistics, just show the stored p-value
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

                # Generate and display diagnostic plots (only for pilot data, not estimated statistics)
                if phase2_results.cleaned_data:  # Only if we have actual data
                    try:
                        qq_plot_src = self._generate_qq_plot(
                            phase2_results.cleaned_data
                        )
                        pp_plot_src = self._generate_pp_plot(
                            phase2_results.cleaned_data
                        )
                        imr_plot_src = self._generate_imr_chart(
                            phase2_results.cleaned_data
                        )

                        self.qq_plot_image.set_source(qq_plot_src)
                        self.pp_plot_image.set_source(pp_plot_src)
                        self.imr_plot_image.set_source(imr_plot_src)

                        self.phase2_plots_card.set_visibility(True)
                    except Exception as plot_error:
                        # Log but don't fail the entire process if plots fail
                        ui.notify(
                            f"Warning: Could not generate diagnostic plots: {plot_error}",
                            type="warning",
                        )

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
                ui.notify(f"Validation error: {e}", type="negative", timeout=0)
            except Exception as e:
                ui.notify(f"Processing error: {e}", type="negative", timeout=0)

        process_phase2_btn.on_click(handle_process_phase2)

    def _create_phase3_ui(self) -> None:
        """Create Phase 3 UI (sample size calculation)."""
        with ui.card().classes("w-full"):
            ui.label("Sample Size Calculation").classes("text-h6")
            ui.label("Calculate the required sample size for final validation").classes(
                "text-body2"
            )

        # Calculate button
        with ui.row().classes("w-full"):
            self.calculate_phase3_btn = ui.button(
                "Calculate Required Sample Size", icon="calculate"
            ).classes("bg-primary")

        # Store Phase 3 controls for disabling after completion
        self.phase3_controls = [self.calculate_phase3_btn]

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
                    ui.notify(
                        "Please complete Phase 2 first", type="warning", timeout=0
                    )
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
                    ui.notify(
                        "Missing required data from previous phases",
                        type="negative",
                        timeout=0,
                    )
                    return

                # Check if using estimated statistics
                if (
                    self.module_v_state.estimated_mean is not None
                    and self.module_v_state.estimated_std is not None
                ):
                    # Use estimated statistics directly
                    mean = self.module_v_state.estimated_mean
                    std = self.module_v_state.estimated_std

                    # Calculate k_margin manually using the same logic as calculate_capability_margin
                    # Forward-transform spec limits based on transformation method
                    transformation_method = phase2_results.transformation_method
                    lambda_param = phase2_results.lambda_param

                    lsl_t = None
                    usl_t = None

                    if transformation_method == TransformationMethod.LOGARITHMIC:
                        # Log transformation: y = ln(x)
                        if spec_limits.lsl is not None:
                            if spec_limits.lsl <= 0:
                                raise ValueError(
                                    "LSL must be positive for logarithmic transformation"
                                )
                            lsl_t = math.log(spec_limits.lsl)
                        if spec_limits.usl is not None:
                            if spec_limits.usl <= 0:
                                raise ValueError(
                                    "USL must be positive for logarithmic transformation"
                                )
                            usl_t = math.log(spec_limits.usl)

                    elif transformation_method == TransformationMethod.BOX_COX:
                        # Box-Cox transformation: y = (x^λ - 1) / λ (for λ ≠ 0)
                        if lambda_param is None:
                            raise ValueError(
                                "Lambda parameter required for Box-Cox transformation"
                            )

                        if spec_limits.lsl is not None:
                            if spec_limits.lsl <= 0:
                                raise ValueError(
                                    "LSL must be positive for Box-Cox transformation"
                                )
                            if abs(lambda_param) < 1e-10:  # lambda ≈ 0
                                lsl_t = math.log(spec_limits.lsl)
                            else:
                                lsl_t = (
                                    spec_limits.lsl**lambda_param - 1
                                ) / lambda_param

                        if spec_limits.usl is not None:
                            if spec_limits.usl <= 0:
                                raise ValueError(
                                    "USL must be positive for Box-Cox transformation"
                                )
                            if abs(lambda_param) < 1e-10:  # lambda ≈ 0
                                usl_t = math.log(spec_limits.usl)
                            else:
                                usl_t = (
                                    spec_limits.usl**lambda_param - 1
                                ) / lambda_param

                    elif transformation_method == TransformationMethod.YEO_JOHNSON:
                        # Yeo-Johnson transformation (works with all values)
                        if lambda_param is None:
                            raise ValueError(
                                "Lambda parameter required for Yeo-Johnson transformation"
                            )

                        def yeo_johnson_forward_single(x: float, lmbda: float) -> float:
                            """Apply Yeo-Johnson transformation to a single value."""
                            if x >= 0:
                                if abs(lmbda) < 1e-10:  # lambda ≈ 0
                                    return math.log(x + 1)
                                else:
                                    return ((x + 1) ** lmbda - 1) / lmbda
                            else:  # x < 0
                                if abs(lmbda - 2) < 1e-10:  # lambda ≈ 2
                                    return -math.log(-x + 1)
                                else:
                                    return -((-x + 1) ** (2 - lmbda) - 1) / (2 - lmbda)

                        if spec_limits.lsl is not None:
                            lsl_t = yeo_johnson_forward_single(
                                spec_limits.lsl, lambda_param
                            )
                        if spec_limits.usl is not None:
                            usl_t = yeo_johnson_forward_single(
                                spec_limits.usl, lambda_param
                            )

                    else:  # TransformationMethod.NONE
                        # No transformation - use original limits
                        lsl_t = spec_limits.lsl
                        usl_t = spec_limits.usl

                    # Calculate capability margins
                    margins = []

                    if lsl_t is not None:
                        # Lower margin: (mean - LSL) / std
                        lower_margin = (mean - lsl_t) / std
                        margins.append(lower_margin)

                    if usl_t is not None:
                        # Upper margin: (USL - mean) / std
                        upper_margin = (usl_t - mean) / std
                        margins.append(upper_margin)

                    # k_margin is the minimum of the calculated margins
                    k_margin = min(margins)

                    # Check if process is capable
                    if k_margin <= 0:
                        raise ValueError(
                            "Process is incapable: k_margin <= 0. "
                            "Mean is outside specification limits or too close to limits."
                        )

                else:
                    # Use existing logic: calculate_capability_margin with pilot data
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

                # Disable Phase 3 controls after completion to prevent recalculation
                # that would invalidate Phase 4 results
                for control in self.phase3_controls:
                    control.set_enabled(False)

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
                            formula = (
                                "Non-Parametric One-Sided (Extreme Order Statistics)"
                            )
                        else:
                            formula = (
                                "Non-Parametric Two-Sided (Min/Max Order Statistics)"
                            )

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
                ui.notify(f"Calculation error: {e}", type="negative", timeout=0)
            except Exception as e:
                ui.notify(f"Calculation error: {e}", type="negative", timeout=0)

        self.calculate_phase3_btn.on_click(handle_calculate_phase3)

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

        # Report generation buttons (initially hidden)
        self.v_report_btn_container = ui.row().classes("w-full gap-2")
        with self.v_report_btn_container:
            v_report_btn = ui.button(
                "Generate PDF Report", icon="picture_as_pdf"
            ).classes("bg-secondary")
            v_full_report_btn = (
                ui.button("Generate Full Report", icon="description")
                .classes("bg-accent")
                .tooltip(
                    "Generate comprehensive report including calculation, validation status, and audit trail"
                )
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
                    ui.notify(
                        "Please complete Phase 3 first", type="warning", timeout=0
                    )
                    return

                # Parse final data
                final_data_str = self.final_data_input.value
                if not final_data_str:
                    ui.notify(
                        "Please enter final validation data",
                        type="warning",
                        timeout=0,
                    )
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
                    ui.notify(
                        "Missing required data from previous phases",
                        type="negative",
                        timeout=0,
                    )
                    return

                # Check if dataset size exceeds required sample size
                if len(final_data) > phase3_results.required_sample_size:
                    ui.notify(
                        f"Dataset contains {len(final_data)} samples, which exceeds the required "
                        f"{phase3_results.required_sample_size}. Using all {len(final_data)} samples.",
                        type="info",
                    )

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
                        "text-positive"
                        if phase4_results.pass_fail == "Pass"
                        else "text-negative"
                    )
                    ui.label(f"Result: {phase4_results.pass_fail}").classes(
                        f"text-h5 {pass_fail_color}"
                    )

                    # Ppk (if available)
                    if phase4_results.ppk is not None:
                        ui.label(
                            f"Process Capability (Ppk): {phase4_results.ppk:.4f}"
                        ).classes("text-body1")

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
                ui.notify(f"Validation error: {e}", type="negative", timeout=0)
            except Exception as e:
                ui.notify(f"Calculation error: {e}", type="negative", timeout=0)

        calculate_phase4_btn.on_click(handle_calculate_phase4)

        # Report generation handler
        def handle_generate_v_report() -> None:
            """Generate PDF report for Module V."""
            ui.notify("📝 Generating Module V PDF report...", type="info")
            self.logger.log_button_click(
                "generate_report_module_v", "Module_V", "Phase_4", self.session_id
            )

            try:
                if not self.module_v_state.phase4_complete:
                    ui.notify(
                        "Please complete all phases first",
                        type="warning",
                        timeout=0,
                    )
                    return

                # Get engine hash and validation state
                engine_hash = get_engine_hash()
                validation_state = is_validated_state()

                # Prepare report data
                phase2 = self.module_v_state.phase2_results
                phase3 = self.module_v_state.phase3_results
                phase4 = self.module_v_state.phase4_results
                spec_limits = self.module_v_state.spec_limits

                if (
                    phase2 is None
                    or phase3 is None
                    or phase4 is None
                    or spec_limits is None
                ):
                    ui.notify("Missing phase results", type="negative", timeout=0)
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

                # Generate PDF and save to reports directory
                pdf_bytes, report_path = ReportGenerator.generate_user_report(
                    report_data
                )

                # Log report generation
                self.logger.log_report_generation(
                    "user_calculation", engine_hash, validation_state, self.session_id
                )

                # Display report file path in UI
                ui.notify(
                    f"Report saved to: {report_path}", type="positive", position="top"
                )

                # Trigger download
                ui.download(
                    pdf_bytes,
                    f"sample_size_report_module_v_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                )

                # Log PDF generation
                self.logger.log_report_generation(
                    "Module V PDF Report",
                    report_path,
                    validation_state,
                    self.session_id,
                )
                ui.notify("✅ Module V PDF report saved and logged", type="positive")

            except Exception as e:
                ui.notify(f"Report generation error: {e}", type="negative", timeout=0)

        v_report_btn.on_click(handle_generate_v_report)

        # Full report generation handler for Module V
        def handle_generate_v_full_report() -> None:
            """Generate comprehensive full report for Module V."""
            ui.notify("📝 Generating Module V full report...", type="info")
            self.logger.log_button_click(
                "generate_full_report_module_v", "Module_V", "Phase_4", self.session_id
            )

            try:
                if not self.module_v_state.phase4_complete:
                    ui.notify(
                        "Please complete all phases first",
                        type="warning",
                        timeout=0,
                    )
                    return

                # Get engine hash and validation state
                engine_hash = get_engine_hash()
                validation_state = is_validated_state()

                # Prepare report data (same as regular report)
                phase2 = self.module_v_state.phase2_results
                phase3 = self.module_v_state.phase3_results
                phase4 = self.module_v_state.phase4_results
                spec_limits = self.module_v_state.spec_limits

                if (
                    phase2 is None
                    or phase3 is None
                    or phase4 is None
                    or spec_limits is None
                ):
                    ui.notify("Missing phase results", type="negative", timeout=0)
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

                # Generate full report PDF
                full_report_bytes = FullReportGenerator.generate_full_report(
                    calculation_report=report_data,
                    session_id=self.session_id,
                    log_dir="logs",
                    validation_reports_dir="reports/validation",
                )

                # Save to reports/full/ directory
                report_path = get_full_report_path()
                saved_path = save_report(full_report_bytes, report_path)

                # Sign the PDF with hash for tamper detection
                try:
                    from sample_size_calculator.pdf_signature import PDFSignature

                    signature = PDFSignature.sign_pdf(full_report_bytes, engine_hash)
                    PDFSignature.save_signature(saved_path, signature)
                except Exception:
                    pass

                # Log report generation
                self.logger.log_report_generation(
                    "full_report", engine_hash, validation_state, self.session_id
                )

                # Display report file path in UI
                ui.notify(
                    f"Full report saved to: {saved_path}",
                    type="positive",
                    position="top",
                    timeout=5000,
                )

                # Trigger download
                ui.download(
                    full_report_bytes,
                    f"full_report_module_v_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                )

                # Log PDF generation
                self.logger.log_report_generation(
                    "Module V Full Report",
                    saved_path,
                    validation_state,
                    self.session_id,
                )
                ui.notify(
                    "✅ Module V full report generated successfully", type="positive"
                )

            except Exception as e:
                ui.notify(
                    f"Full report generation error: {e}", type="negative", timeout=0
                )

        v_full_report_btn.on_click(handle_generate_v_full_report)

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

        # Disable Phase 3 controls if phase is completed
        if self.module_v_state.phase3_complete:
            self.calculate_phase3_btn.disable()

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
            for _i, outlier in enumerate(phase1_results.outliers):
                with ui.card().classes("w-full bg-yellow-50"):
                    with ui.row().classes("w-full items-center"):
                        ui.label(f"Outlier Value: {outlier.value}").classes(
                            "text-body1 font-bold"
                        )

                        # Exclude checkbox
                        exclude_cb = ui.checkbox("Exclude").bind_value(
                            outlier, "is_excluded"
                        )

                    # Rationale input (inside the card)
                    rationale_input = (
                        ui.textarea(
                            label="Engineering Rationale (required if excluded)",
                            placeholder="e.g., Measurement error, sensor malfunction, process upset",
                        )
                        .classes("w-full")
                        .bind_value(outlier, "rationale")
                    )

                    # Initially hide the rationale input
                    rationale_input.set_visibility(False)

                    # Update visibility when checkbox changes
                    exclude_cb.on(
                        "update:model-value",
                        lambda e, r=rationale_input: r.set_visibility(e.args),
                    )

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
                method_path += (
                    "Formula: Limits = (λ * y + 1)^(1/λ) where y = mean ± k * std\n"
                )
            elif phase2.transformation_method == TransformationMethod.YEO_JOHNSON:
                method_path += "Formula: Limits = inverse_YJ(mean_yj ± k * std_yj)\n"

        method_path += "━" * 80

        # Update display
        self.method_transparency_label.set_text(method_path)
        self.method_transparency_card.set_visibility(True)

    def _generate_qq_plot(self, data: list[float]) -> str:
        """Generate Q-Q plot for normality assessment.

        Args:
            data: List of data values to plot

        Returns:
            Base64-encoded PNG image string
        """
        fig, ax = plt.subplots(figsize=(6, 5))

        # Generate Q-Q plot using scipy
        stats.probplot(data, dist="norm", plot=ax)

        ax.set_title("Q-Q Plot (Quantile-Quantile)", fontsize=12, fontweight="bold")
        ax.set_xlabel("Theoretical Quantiles", fontsize=10)
        ax.set_ylabel("Sample Quantiles", fontsize=10)
        ax.grid(True, alpha=0.3)

        # Save to bytes buffer
        buf = io.BytesIO()
        plt.tight_layout()
        fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)

        # Convert to base64 for display in NiceGUI
        import base64

        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        return f"data:image/png;base64,{img_base64}"

    def _generate_pp_plot(self, data: list[float]) -> str:
        """Generate P-P plot for normality assessment.

        Args:
            data: List of data values to plot

        Returns:
            Base64-encoded PNG image string
        """
        fig, ax = plt.subplots(figsize=(6, 5))

        # Sort data and calculate empirical CDF
        sorted_data = np.sort(data)
        n = len(sorted_data)
        empirical_cdf = np.arange(1, n + 1) / n

        # Calculate theoretical CDF (normal distribution)
        mean = np.mean(sorted_data)
        std = np.std(sorted_data, ddof=1)
        theoretical_cdf = stats.norm.cdf(sorted_data, loc=mean, scale=std)

        # Plot P-P
        ax.plot(
            theoretical_cdf, empirical_cdf, "bo", markersize=4, alpha=0.6, label="Data"
        )
        ax.plot([0, 1], [0, 1], "r--", linewidth=2, label="Perfect Fit")

        ax.set_title(
            "P-P Plot (Probability-Probability)", fontsize=12, fontweight="bold"
        )
        ax.set_xlabel("Theoretical Cumulative Probability", fontsize=10)
        ax.set_ylabel("Empirical Cumulative Probability", fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.legend(loc="lower right")
        ax.set_xlim((0, 1))
        ax.set_ylim((0, 1))

        # Save to bytes buffer
        buf = io.BytesIO()
        plt.tight_layout()
        fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)

        # Convert to base64
        import base64

        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        return f"data:image/png;base64,{img_base64}"

    def _generate_imr_chart(self, data: list[float]) -> str:
        """Generate I-MR chart for process stability assessment.

        Args:
            data: List of data values to plot

        Returns:
            Base64-encoded PNG image string
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))

        # Individual values chart
        x = np.arange(1, len(data) + 1)
        mean = np.mean(data)

        # Calculate moving ranges
        moving_ranges = [abs(data[i] - data[i - 1]) for i in range(1, len(data))]
        mr_mean = np.mean(moving_ranges) if moving_ranges else 0

        # Control limits for individuals (using d2=1.128 for n=2)
        d2 = 1.128
        ucl_i = mean + 3 * (mr_mean / d2)
        lcl_i = mean - 3 * (mr_mean / d2)

        # Plot individuals
        ax1.plot(x, data, "bo-", markersize=5, linewidth=1, label="Individual Values")
        ax1.axhline(
            mean, color="g", linestyle="-", linewidth=2, label=f"Mean = {mean:.3f}"
        )
        ax1.axhline(
            ucl_i, color="r", linestyle="--", linewidth=1.5, label=f"UCL = {ucl_i:.3f}"
        )
        ax1.axhline(
            lcl_i, color="r", linestyle="--", linewidth=1.5, label=f"LCL = {lcl_i:.3f}"
        )

        ax1.set_title(
            "Individual Values Chart (I-Chart)", fontsize=11, fontweight="bold"
        )
        ax1.set_xlabel("Observation", fontsize=9)
        ax1.set_ylabel("Value", fontsize=9)
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc="best", fontsize=8)

        # Moving range chart
        if moving_ranges:
            x_mr = np.arange(2, len(data) + 1)

            # Control limits for moving range (using D4=3.267 for n=2)
            d4 = 3.267
            ucl_mr = d4 * mr_mean

            ax2.plot(
                x_mr,
                moving_ranges,
                "go-",
                markersize=5,
                linewidth=1,
                label="Moving Range",
            )
            ax2.axhline(
                mr_mean,
                color="g",
                linestyle="-",
                linewidth=2,
                label=f"MR Mean = {mr_mean:.3f}",
            )
            ax2.axhline(
                ucl_mr,
                color="r",
                linestyle="--",
                linewidth=1.5,
                label=f"UCL = {ucl_mr:.3f}",
            )
            ax2.axhline(0, color="r", linestyle="--", linewidth=1.5, label="LCL = 0")

            ax2.set_title(
                "Moving Range Chart (MR-Chart)", fontsize=11, fontweight="bold"
            )
            ax2.set_xlabel("Observation", fontsize=9)
            ax2.set_ylabel("Moving Range", fontsize=9)
            ax2.grid(True, alpha=0.3)
            ax2.legend(loc="best", fontsize=8)

        # Save to bytes buffer
        buf = io.BytesIO()
        plt.tight_layout()
        fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)

        # Convert to base64
        import base64

        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        return f"data:image/png;base64,{img_base64}"

    def create_examples_tab(self) -> None:
        """Create Examples tab with JupyterLab integration."""
        ui.label("Examples").classes("text-h5")
        ui.label("Launch JupyterLab to explore example notebooks").classes(
            "text-subtitle2"
        )
        ui.separator()

        with ui.card().classes("w-full"):
            ui.label("JupyterLab Notebook Server").classes("text-h6")

            # Status indicator
            status_label = ui.label(self.jupyter_manager.get_status()).classes(
                "text-body2"
            )

            # Control buttons
            with ui.row().classes("gap-2"):
                start_btn = ui.button(
                    "Start JupyterLab",
                    icon="play_arrow",
                    on_click=lambda: self._start_jupyter(status_label),
                ).props("color=positive")

                stop_btn = ui.button(
                    "Stop JupyterLab",
                    icon="stop",
                    on_click=lambda: self._stop_jupyter(status_label),
                ).props("color=negative")

                open_btn = ui.button(
                    "Open JupyterLab",
                    icon="open_in_new",
                    on_click=lambda: self._open_jupyter(),
                ).props("color=primary")

            ui.separator()

            # Information section
            with ui.expansion("About JupyterLab Examples", icon="info").classes(
                "w-full"
            ):
                ui.markdown("""
### Available Notebooks

The `notebooks/` directory contains interactive examples:

- **Example.ipynb**
  - Process Validation of a CNC lathe machining metal shafts. (normal, two-sided)
  - Product Design Validation of a molded polymer bracket. (normal, one-sided)
  - Validation of a sterilization. (log-normal, one-sided)
  - Validation of lithium-ion battery capacities. (skewed, one-sided)
  - Validation of an extrusion process where the machine heater cycles ON and OFF. (U-shaped, two-sided)
  - Process Validation of a thermal curing plate. (quatratic, one-sided)
  - 2-cavity injection mold. (bimodal, two-sided)
  - Quality Validation of painted car panels. (poisson, one-sided)
  - Design Validation of a titanium aerospace pressure vessel. (small sample size)
  - Process Validation of a CNC milled component. (drift, two-sided)


### Getting Started

1. Click **Start JupyterLab** to launch the notebook server
2. Wait for the "JupyterLab started successfully!" notification
3. Click **Open JupyterLab** to access notebooks in a new tab
4. Navigate to the desired notebook and run cells

### Tips

- JupyterLab runs on port 8888 by default
- The token for authentication is automatically generated
- Notebooks have access to the full calculation engine
- Stop JupyterLab when done to free resources

### Docker Usage

When running in Docker, JupyterLab is accessible at the same URL. 
The notebooks directory is mounted as a volume for persistence.
                """)

        with ui.card().classes("w-full"):
            ui.label("Quick Examples (No JupyterLab Required)").classes("text-h6")

            with ui.expansion("Module A: Basic Calculation", icon="calculate").classes(
                "w-full"
            ):
                ui.markdown("""
```python
Input confidence (e.g. 95.0) and reliability (e.g.95.0) and press "CALCULATE SAMPLE SIZE"
Optional you can insert allowable failures or population size (to be implemented soon)

# Output: Required sample size: 59
# If allowable failures c=10 -> Required sample size: 336

```
                """)

            with ui.expansion(
                "Module V: Variable Data Workflow", icon="trending_up"
            ).classes("w-full"):
                ui.markdown("""
```python
# Phase 1: Analyze pilot data
Two-Sided
lsl: 9.9,
usl: 10.1
pilot_data: 10.015, 9.996, 10.019, 10.046, 9.993

# Phase 2: Check normality and transform if needed
--> is normal, no outliers
# Phase 3: Calculate required sample size
--> 7
# Phase 4: Validate with final dataset
Final Dataset: 10.022, 10.005, 9.997, 9.991, 9.956, 9.978, 9.986

--> Pass
--> Ppk: 1.4494

# See notebooks for complete workflow examples
```
                """)

    def _start_jupyter(self, status_label: ui.label) -> None:
        """Start JupyterLab and update status.

        Args:
            status_label: Label to update with status
        """
        self.jupyter_manager.start()
        status_label.text = self.jupyter_manager.get_status()

    def _stop_jupyter(self, status_label: ui.label) -> None:
        """Stop JupyterLab and update status.

        Args:
            status_label: Label to update with status
        """
        self.jupyter_manager.stop()
        status_label.text = self.jupyter_manager.get_status()

    def _open_jupyter(self) -> None:
        """Open JupyterLab in a new browser tab using JavaScript."""
        jupyter_url = self.jupyter_manager.get_url()
        ui.run_javascript(f'window.open("{jupyter_url}", "_blank");')

    def create_help_tab(self) -> None:
        """Create Help tab with comprehensive documentation and guidance."""
        ui.label("Help & Documentation").classes("text-h5")
        ui.label("Comprehensive guide for using the Sample Size Calculator").classes(
            "text-subtitle2"
        )
        ui.separator()

        # Section 1: Module A - Attribute Data Analysis
        with ui.expansion(
            "Risk-Based Statistical Strategies for Medical Device Verification and Validation",
            icon="warning",
        ).classes("w-full"):
            with ui.card().classes("w-full"):
                ui.markdown("""
## Introduction: Why We Can't Just Test 30 Units Anymore

The days of picking arbitrary sample sizes are gone. Regulators—the FDA, EU notified bodies—now require a documented,
statistically valid rationale for every test protocol we write. That means sample size can't be a guess. It has to be
calculated based on your specific risk profile.

This shift isn't just bureaucratic. It makes sense: we're trying to prove device safety, and that proof needs to be
mathematically sound. The regulations are clear: 21 CFR 820.250(b) and ISO 13485:2016 both mandate statistical techniques
with documented rationale for sampling plans.

The reality is, sample size depends on three things:

- **How severe is a failure?** (Risk from ISO 14971)
- **How confident do we need to be?** (Confidence level)
- **What percentage of devices must work?** (Reliability)

Link those three, do the math, and you get your sample size. That's the story regulators want to see in your Design
Verification Plan.

## The Problem With Old Heuristics

We used to lean on the "rule of 30"—test 30 units because the t-distribution approximates normal at n≥30. That's true,
but it's answering the wrong question. It's about the average performance. In design verification, you care about the
extremes—the worst-case units. That's a different statistical problem entirely.

## Building Your Statistical Policy: Risk Drives Sample Size

Start with ISO 14971. Map your hazards to severity levels, then define what confidence and reliability you actually need:

| Risk Level | Severity | Required Confidence | Required Reliability |
|------------|----------|---------------------|---------------------|
| **Critical** | Catastrophic (death, permanent injury) | 95% | 99.0% - 99.9% |
| **High** | Serious (life-threatening) | 95% | 99.0% |
| **Medium** | Moderate (medical intervention needed) | 95% | 95.0% |
| **Low** | Minor (temporary, no medical care) | 95% | 90.0% |
| **Negligible** | Inconvenience only | 90% | 80.0% |

This is my standard policy. It's an example of a “valid justification.”
<span style="color:red">Revise</span> and document it, stick to it,
 and you will obtain reasonable sample sizes.

## Confidence vs. Reliability: Get This Right

**Reliability (R)**: The percentage of devices in production that actually meet spec. 99% reliability = 99 out of 100
devices work as intended.

**Confidence (C)**: How sure you are about that claim. You're testing a sample, not everything, so there's always
uncertainty. 95% confidence means if you repeated the test 100 times, you'd get the right answer 95 times.

Regulators basically expect 95% confidence as a floor for safety-critical testing. Reliability is what scales with
risk—catastrophic failures demand 99.9%, while minor issues might only need 90%.

## Use Variable Data When Possible

Statistical power matters. Here's the hierarchy:

1. **Variable data (parametric)**: Measure actual values (dimension, force, output). Best sample size efficiency.
2. **Variable data (non-parametric)**: Measurements that don't fit normal distribution. Still good.
3. **Attribute data**: Pass/fail only. Requires the largest sample sizes.

Pro tip: Define specs in variable terms instead of binary pass/fail. You'll dramatically reduce your sample
size and get better insight into design margins.

## The Takeaway

Your sample size isn't a preference—it's a calculated answer to a quantified risk question. Start
with the risk assessment, define your confidence and reliability targets, then calculate. Document it all.
That's what regulators are actually looking for: the mathematical connection between "this could harm someone"
and "we tested this many units."
                """)

        # Section 1: Module A - Attribute Data Analysis
        with ui.expansion("Module A: Attribute Data Analysis", icon="info").classes(
            "w-full"
        ):
            with ui.card().classes("w-full"):
                ui.markdown("""
### Purpose
Module A is designed for **attribute data analysis** where measurements are binary (Pass/Fail, Good/Bad, Accept/Reject).
It calculates the minimum sample size required to demonstrate product reliability with statistical confidence.

### Input Requirements
- **Confidence Level (%)**: The statistical confidence that the true reliability exceeds the specified level (typically 90%, 95%, or 99%)
- **Reliability Level (%)**: The minimum acceptable proportion of passing units (e.g., 95% means at most 5% failures allowed)
- **[Optional] Allowable Failures**: Maximum number of failures permitted in the sample while still demonstrating reliability
- **[Optional] Population Size**: Total number of population

### Calculation Methodology
Module A uses binomial distribution theory to determine sample sizes. The calculation ensures that:
- If you observe ≤ allowable failures in your sample, you can claim the specified reliability at the given confidence level
- The method is conservative and provides one-sided confidence bounds
- Larger confidence levels or higher reliability requirements increase the required sample size
- If your sample is > 5% of the population, FPC (finite population correction) matters. If population size is provided, sample size is corrected with formula n = (N * n0) / (N - 1 + n0) with N=population size, n0=sample size of infinite population.

### Interpretation of Results
- **Required Sample Size (n)**: The minimum number of units you must test (original and corrected)
- **Decision Rule**: Test n units. If failures ≤ allowable failures, the product meets reliability requirements
- **Example**: n=100, allowable failures=2 means "Test 100 units; if 0, 1, or 2 fail, accept the lot"

### Typical Use Cases
- Acceptance sampling for incoming materials
- Production lot qualification
- Reliability demonstration testing
- Quality assurance verification
                """)

        # Section 2: Module V - Variable Data Analysis (4-Phase Workflow)
        with ui.expansion(
            "Module V: Variable Data Analysis (4-Phase Workflow)", icon="analytics"
        ).classes("w-full"):
            with ui.card().classes("w-full"):
                ui.markdown("""
### Purpose
Module V is designed for **variable data analysis** where measurements are continuous numerical values (dimensions, weights, voltages, etc.).
It uses a structured 4-phase workflow to ensure proper statistical analysis and sample size determination.

### Phase 1: Initial Data Collection & Outlier Detection
**Objective**: Collect preliminary data and identify statistical outliers

**Steps**:
1. Enter your initial measurement data (comma-separated values)
2. Specify the number of standard deviations for outlier detection (typically 3σ)
3. Click "Detect Outliers" to identify extreme values
4. Review flagged outliers and decide whether to remove them
5. Click "Complete Phase 1" to proceed

**Key Concepts**:
- **Outliers**: Data points that fall beyond ±k standard deviations from the mean
- **Why Remove Outliers**: Measurement errors or special causes can distort statistical analysis
- **When to Keep Outliers**: If they represent true process variation, keep them

### Phase 2: Normality Testing & Transformation Selection
**Objective**: Assess data normality and apply transformations if needed

**Steps**:
1. System automatically performs normality tests (Shapiro-Wilk and Anderson-Darling)
2. Review normality test results and diagnostic plots:
   - **Q-Q Plot**: Points should follow diagonal line for normal data
   - **P-P Plot**: Points should follow diagonal line for normal distribution
   - **I-MR Chart**: Checks process stability over time
3. If data is non-normal, system recommends transformations:
   - **Logarithmic**: For right-skewed data (positive values only)
   - **Box-Cox**: For positive data with varying skewness
   - **Yeo-Johnson**: For data including zero or negative values
4. Enable "Manual Override" to manually select transformation method if desired
5. Click "Complete Phase 2" to proceed

**Key Concepts**:
- **Normality**: Many statistical methods assume normally distributed data
- **Transformations**: Mathematical operations that can normalize non-normal data
- **Automatic Selection**: System chooses best transformation based on data characteristics

### Phase 3: Sample Size Calculation
**Objective**: Calculate required sample size for tolerance limit estimation

**Steps**:
1. Enter statistical requirements:
   - **Confidence Level**: Confidence in the tolerance interval (e.g., 95%)
   - **Coverage**: Proportion of population within tolerance limits (e.g., 99%)
   - **Sided**: One-sided (upper or lower) or two-sided tolerance limits
2. Click "Calculate Sample Size" to determine required n
3. Review the calculated sample size
4. System locks Phase 3 controls to prevent recalculation that would invalidate Phase 4

**Key Concepts**:
- **Tolerance Limits**: Statistical bounds that contain a specified proportion of the population
- **Confidence Level**: How confident you are that the tolerance limits are correct
- **Coverage**: What percentage of the population falls within the limits

### Phase 4: Final Validation & Tolerance Limit Calculation
**Objective**: Collect final sample and calculate tolerance limits

**Steps**:
1. Collect the required sample size (n) or more data points
2. Enter final validation data (comma-separated values)
3. Enter specification limits (LSL = Lower Spec Limit, USL = Upper Spec Limit)
4. Click "Calculate Tolerance Limits" to perform final analysis
5. Review results:
   - **Tolerance Limits**: Calculated statistical bounds
   - **Pass/Fail**: Whether tolerance limits fall within specification limits
   - **Ppk**: Process performance index (higher is better, ≥1.33 is typical target)

**Key Concepts**:
- **Specification Limits**: Engineering requirements (what the product must meet)
- **Tolerance Limits**: Statistical prediction (what the process actually produces)
- **Ppk**: Measures process capability relative to specifications
- **Pass Criteria**: Tolerance limits must fall entirely within specification limits
                """)

        # Section 3: Statistical Terms Glossary
        with ui.expansion("Statistical Terms & Methods Glossary", icon="book").classes(
            "w-full"
        ):
            with ui.card().classes("w-full"):
                ui.markdown("""
### Normality Tests

**Shapiro-Wilk Test**
- Tests whether data follows a normal distribution
- **Test Statistic (W)**: Ranges from 0 to 1; values close to 1 indicate normality
- **P-value**: If p > 0.05, data is likely normal; if p < 0.05, data is likely non-normal
- **Best for**: Small to medium sample sizes (n < 50)

**Anderson-Darling Test**
- Alternative normality test that gives more weight to tail deviations
- **Test Statistic (A²)**: Lower values indicate better fit to normal distribution
- **Critical Values**: Compared at different significance levels (15%, 10%, 5%, 2.5%, 1%)
- **Interpretation**: If statistic < critical value at desired level, data is normal
- **Best for**: Detecting departures from normality in distribution tails

### Data Transformations

**Logarithmic Transformation**
- **Formula**: y = log(x)
- **Use when**: Data is right-skewed (long tail to the right) and all values are positive
- **Effect**: Compresses large values, expands small values
- **Example**: Income data, reaction times, bacterial counts

**Box-Cox Transformation**
- **Formula**: y = (x^λ - 1) / λ for λ ≠ 0; y = log(x) for λ = 0
- **Use when**: Data is positive and you want to find optimal transformation
- **Parameter λ**: Automatically selected to maximize normality
- **Effect**: Flexible family of power transformations
- **Limitation**: Requires all positive values

**Yeo-Johnson Transformation**
- **Formula**: Extension of Box-Cox that handles zero and negative values
- **Use when**: Data includes zero or negative values
- **Parameter λ**: Automatically selected to maximize normality
- **Effect**: Most flexible transformation, works with any data
- **Advantage**: No restrictions on data values

**Non-Parametric (Wilks) Method**
- **Use when**: Data cannot be normalized through transformations
- **Approach**: Distribution-free method that doesn't assume normality
- **Trade-off**: Requires larger sample sizes than parametric methods
- **Advantage**: Robust to any data distribution

### Diagnostic Plots

**Q-Q Plot (Quantile-Quantile Plot)**
- **Purpose**: Visual assessment of normality
- **Interpretation**:
  - Points follow diagonal line → data is normal
  - Points curve above line → right-skewed data
  - Points curve below line → left-skewed data
  - S-shaped pattern → heavy-tailed distribution

**P-P Plot (Probability-Probability Plot)**
- **Purpose**: Compares cumulative distribution of data vs. theoretical normal
- **Interpretation**:
  - Points follow diagonal line → good fit to normal distribution
  - Deviations indicate non-normality
- **Difference from Q-Q**: More sensitive to deviations in center of distribution

**I-MR Chart (Individual Moving Range Chart)**
- **Purpose**: Assesses process stability over time
- **Components**:
  - Individual values plotted in sequence
  - Moving range (difference between consecutive points)
  - Control limits at ±3σ
- **Interpretation**:
  - Points within control limits → stable process
  - Points outside limits or patterns → special causes present

### Tolerance Limits & Process Capability

**Tolerance Limits**
- **Definition**: Statistical bounds that contain a specified proportion of the population with stated confidence
- **Example**: "95% confident that 99% of parts fall within [2.45, 2.55] mm"
- **Types**:
  - **Two-sided**: Both upper and lower limits
  - **One-sided**: Only upper or only lower limit

**Ppk (Process Performance Index)**
- **Definition**: Measures how well process output fits within specification limits
- **Formula**: Ppk = min[(USL - μ) / 3σ, (μ - LSL) / 3σ]
- **Interpretation**:
  - Ppk < 1.0: Process produces defects
  - Ppk = 1.0: Process just meets specifications
  - Ppk = 1.33: Typical minimum target (4σ process)
  - Ppk = 1.67: Good process capability (5σ process)
  - Ppk ≥ 2.0: Excellent process capability (6σ process)

**Confidence Level vs. Coverage**
- **Confidence Level**: How sure you are that your tolerance limits are correct (e.g., 95% confidence)
- **Coverage**: What proportion of the population falls within the limits (e.g., 99% coverage)
- **Example**: "95% confidence, 99% coverage" means "I'm 95% confident that 99% of parts meet requirements"
                """)

        # Section 4: Step-by-Step Workflows & Troubleshooting
        with ui.expansion(
            "Step-by-Step Workflows & Troubleshooting", icon="help"
        ).classes("w-full"):
            with ui.card().classes("w-full"):
                ui.markdown("""
### Common Workflow 1: Normal Data with No Transformation

**Scenario**: Your data is already normally distributed

**Steps**:
1. **Phase 1**: Enter data → Detect outliers → Remove if necessary → Complete Phase 1
2. **Phase 2**: Review normality tests
   - Shapiro-Wilk p-value > 0.05 ✓
   - Anderson-Darling statistic below critical value ✓
   - Q-Q plot points follow diagonal line ✓
   - System selects "None/Parametric" method → Complete Phase 2
3. **Phase 3**: Enter confidence (95%), coverage (99%), sided (Two-sided) → Calculate → Complete Phase 3
4. **Phase 4**: Collect n samples → Enter data → Enter LSL/USL → Calculate tolerance limits → Review Ppk

**Expected Outcome**: Straightforward analysis with no transformation needed

### Common Workflow 2: Right-Skewed Data Requiring Transformation

**Scenario**: Your data has a long tail to the right (e.g., cycle times, failure rates)

**Steps**:
1. **Phase 1**: Enter data → Detect outliers → Complete Phase 1
2. **Phase 2**: Review normality tests
   - Shapiro-Wilk p-value < 0.05 (non-normal) ✗
   - Q-Q plot curves above diagonal line (right-skewed)
   - System recommends "Logarithmic" or "Box-Cox" transformation
   - Accept recommendation → Complete Phase 2
3. **Phase 3**: Enter requirements → Calculate sample size → Complete Phase 3
4. **Phase 4**: Collect n samples → Enter data → Enter LSL/USL → Calculate tolerance limits
   - System applies same transformation to final data
   - Review results in original units

**Expected Outcome**: Transformation normalizes data, enabling valid statistical analysis

### Common Workflow 3: Manual Method Override

**Scenario**: You want to manually select the transformation method

**Steps**:
1. **Phase 1**: Enter data → Detect outliers → Complete Phase 1
2. **Phase 2**:
   - Review normality test results
   - Enable "Manual Override" checkbox
   - Dropdown now shows all methods: None/Parametric, Logarithmic, Box-Cox, Yeo-Johnson, Non-Parametric/Wilks
   - Select desired method → Complete Phase 2
3. **Phase 3**: Enter requirements → Calculate sample size → Complete Phase 3
4. **Phase 4**: Collect n samples → Enter data → Enter LSL/USL → Calculate tolerance limits

**Use Case**: When you have domain knowledge about appropriate transformation or want to compare methods

### Troubleshooting Guide

**Problem**: "Phase 2 shows data is non-normal even after transformation"
- **Solution 1**: Try different transformation (use Manual Override)
- **Solution 2**: Check for remaining outliers in Phase 1
- **Solution 3**: Use Non-Parametric/Wilks method (requires larger sample size)
- **Solution 4**: Investigate process for special causes of variation

**Problem**: "Phase 4 rejects my data saying I need more samples"
- **Cause**: You provided fewer than n samples calculated in Phase 3
- **Solution**: Collect additional data points to reach required sample size n
- **Note**: Providing MORE than n samples is acceptable (system uses all data)

**Problem**: "Tolerance limits fail (outside specification limits)"
- **Meaning**: Your process variation is too large relative to specifications
- **Solutions**:
  1. **Reduce variation**: Improve process control, reduce measurement error
  2. **Center process**: Adjust process mean to center between LSL and USL
  3. **Widen specifications**: If technically feasible, relax requirements
  4. **Sort/inspect**: If process cannot be improved, implement 100% inspection

**Problem**: "Ppk value is low (< 1.33)"
- **Meaning**: Process capability is insufficient
- **Interpretation**:
  - Ppk < 1.0: Process produces significant defects
  - Ppk 1.0-1.33: Process marginally capable, improvement needed
- **Solutions**: Same as tolerance limit failures above

**Problem**: "I-MR chart shows points outside control limits"
- **Meaning**: Process is not stable (special causes present)
- **Action**: Investigate and remove special causes before proceeding
- **Common causes**: Equipment malfunction, operator error, material variation, environmental changes

**Problem**: "Q-Q plot shows S-shaped pattern"
- **Meaning**: Data has heavier tails than normal distribution (more extreme values)
- **Solutions**:
  1. Check for outliers in Phase 1
  2. Try Yeo-Johnson transformation
  3. Consider Non-Parametric method
  4. Investigate process for multiple populations or modes

**Problem**: "Phase 3 controls are locked and I need to change parameters"
- **Reason**: Phase 3 locks after completion to prevent invalidating Phase 4 results
- **Solution**: If you must change Phase 3 parameters, you'll need to restart the workflow from Phase 3
- **Best Practice**: Carefully review Phase 3 inputs before completing

### Decision Tree: Choosing the Right Method

```
START: Do you have attribute (Pass/Fail) or variable (numerical) data?
│
├─ Attribute Data → Use Module A
│   └─ Enter confidence, reliability, allowable failures → Get sample size
│
└─ Variable Data → Use Module V
    │
    Phase 1: Clean data (remove outliers)
    │
    Phase 2: Is data normal?
    │
    ├─ YES (p > 0.05, Q-Q plot linear) → Use None/Parametric
    │
    └─ NO (p < 0.05, Q-Q plot non-linear) → Need transformation
        │
        ├─ All positive values + right-skewed → Try Logarithmic or Box-Cox
        │
        ├─ Includes zero/negative values → Try Yeo-Johnson
        │
        └─ Cannot normalize → Use Non-Parametric/Wilks (larger n required)
    │
    Phase 3: Calculate required sample size n
    │
    Phase 4: Collect n samples → Calculate tolerance limits → Check Ppk
```

### Tips for Success

1. **Collect Quality Data**: Ensure measurements are accurate and representative
2. **Remove True Outliers**: But investigate why they occurred
3. **Trust the Tests**: Normality tests are reliable for n > 20
4. **Use Adequate Sample Sizes**: Larger samples give more reliable results
5. **Check Process Stability**: Use I-MR chart before proceeding
6. **Understand Transformations**: Results are back-transformed to original units
7. **Review All Plots**: Visual assessment complements statistical tests
8. **Document Decisions**: Record why you chose specific methods or removed outliers
9. **Validate Results**: Do tolerance limits and Ppk make practical sense?
10. **Iterate if Needed**: If results are unexpected, review earlier phases
                """)

        # Section 5: About Reports
        with ui.expansion("Reports, and where you can find them", icon="menu").classes(
            "w-full"
        ):
            with ui.card().classes("w-full"):
                ui.markdown("""
### Validation Reports & Certificates
                            
After running the validation suite, a comprehensive report is generated that includes:

- Who and when the validation was performed
- System information where validation was executed
- The Hash of the code version used for validation (=a fingerprint of the exact code that was run, to ensure validity of the report)
- Detailed results of IQ, OQ, and PQ tests

You can find the generated validation report in the `reports/validation/` directory. Each report is saved as a PDF file named with validation_certificate and the timestamp.

### Calculation Reports

After running calculations you can generate a calculation report that includes:

- Validation state with Hash (Fingerprint) of the code version used for calculation
- Modul and statistical method used for calculation
- Input parameters and results

You can find the generated calculation reports in the `reports/calculations/` directory.

### Full Report

After running calculations, you can also generate a full report that combines the validation report and the calculation report. This provides a complete record of both the testing and analysis performed.

You can find the generated full reports in the `reports/full/` directory.
                """)

        # Section 6: About Validation
        with ui.expansion(
            "Computer Software Validation ISO TR 80002-2", icon="search"
        ).classes("w-full"):
            with ui.card().classes("w-full"):
                with open("./requirements/00_ComputerSoftwareValidation.md", "r") as f:
                    md_content = f.read()
                ui.markdown(md_content)

        ui.separator()
        with ui.card().classes("w-full"):
            ui.label("Need More Help?").classes("text-h6")
            ui.markdown("""
For additional assistance:
- Review the diagnostic plots and test results carefully
- Consult statistical references for deeper understanding of methods
- Consider consulting a statistician for complex or critical applications
- Document your analysis workflow for reproducibility and review
            """)

    def _handle_validation_button_click(self) -> None:
        """Handle validation button click to run IQ/OQ/PQ test suite."""
        # Log button click
        self.logger.log_button_click(
            button_id="run_validation",
            module="System",
            phase=None,
            session_id=self.session_id,
        )

        # Create dialog for tester name input
        with ui.dialog() as dialog, ui.card():
            ui.label("Run Full Validation Suite").classes("text-h6")
            ui.label(
                "This will run IQ/OQ/PQ tests and generate a validation certificate."
            ).classes("text-subtitle2")
            ui.separator()

            tester_input = ui.input(
                label="Tester Name",
                placeholder="Enter your name",
            ).classes("w-full")

            progress_log = ui.log().classes("w-full h-64")

            result_label = ui.label("").classes("text-subtitle1")

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel", on_click=dialog.close).props("flat")
                run_button = ui.button(
                    "Run Validation",
                    on_click=lambda: self._run_validation(
                        tester_input.value, progress_log, result_label, run_button
                    ),
                ).props("color=primary")

        dialog.open()

    async def _run_validation(
        self,
        tester_name: str,
        progress_log: ui.log,
        result_label: ui.label,
        run_button: ui.button,
    ) -> None:
        """Run validation suite asynchronously.

        Args:
            tester_name: Name of the validation tester
            progress_log: UI log component for progress updates
            result_label: UI label for final result message
            run_button: Button to disable during validation
        """

        if not tester_name or not tester_name.strip():
            ui.notify("Please enter tester name", type="warning", timeout=0)
            return

        # Disable button during validation
        run_button.disable()
        result_label.text = "Running validation..."

        def progress_callback(message: str) -> None:
            """Callback to update progress log."""
            progress_log.push(message)

        # Run validation in background
        runner = ValidationRunner(progress_callback=progress_callback)

        try:
            # Run validation (include PQ tests)
            success, message, cert_path = await anyio.to_thread.run_sync(  # type: ignore[attr-defined]
                runner.run_validation, tester_name.strip(), False
            )

            # Log validation execution
            self.logger.log_ui_interaction(
                event_type="validation_execution",
                session_id=self.session_id,
                context={
                    "tester": tester_name.strip(),
                    "success": success,
                    "certificate_path": str(cert_path) if cert_path else None,
                },
            )

            # Update result label
            if success:
                result_label.text = f"✅ {message}"
                result_label.classes("text-green-600")
                ui.notify("Validation completed successfully!", type="positive")
            else:
                result_label.text = f"⚠️ {message}"
                result_label.classes("text-orange-600")
                ui.notify(
                    "Validation completed with warnings", type="warning", timeout=0
                )
            # Always update button color regardless of success/failure
            self._update_validation_button_color()

        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            result_label.text = f"❌ {error_msg}"
            result_label.classes("text-red-600")
            ui.notify(error_msg, type="negative", timeout=0)

            # Update button color on exception
            self._update_validation_button_color()

            # Log error
            self.logger.log_validation_error(
                error_type="validation_execution_error",
                error_message=str(e),
                field_id="validation_runner",
                invalid_value=tester_name,
                session_id=self.session_id,
            )
        finally:
            # Re-enable button
            run_button.enable()


def create_ui() -> None:
    """Create and run the NiceGUI application."""
    controller = UIController()
    controller.create_app()
    ui.run(title="Sample Size Calculator", port=8080, reload=False)


if __name__ == "__main__":
    create_ui()
