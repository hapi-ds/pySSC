"""Audit trail logging for UI interactions and system events.

This module provides comprehensive logging functionality for QMS compliance,
tracking all user interactions, calculations, and system events with timestamps
and structured context.
"""

import json
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


class AuditLogger:
    """Manages audit trail logging for QMS compliance.

    Logs all UI interactions, calculations, and system events to local files
    with ISO 8601 timestamps and structured JSON context. Uses rotating file
    handlers with 10MB size limit and 90-day retention.
    """

    def __init__(self, log_dir: str = "logs") -> None:
        """Initialize audit logger with rotating file handler.

        Args:
            log_dir: Directory path for log files (default: "logs")
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create logger instance
        self.logger = logging.getLogger("audit_logger")
        self.logger.setLevel(logging.INFO)

        # Remove any existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Create rotating file handler
        # 10MB = 10 * 1024 * 1024 bytes
        # Keep 90 backup files (approximately 90 days with daily rotation)
        log_file = self.log_dir / "audit.log"
        handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=90,
            encoding="utf-8",
        )

        # Set formatter with structured format
        # Format: [TIMESTAMP] [LEVEL] [SESSION_ID] [EVENT_TYPE] {context_json}
        formatter = logging.Formatter(
            fmt=(
                "[%(asctime)s] [%(levelname)s] [%(session_id)s] "
                "[%(event_type)s] %(message)s"
            ),
            datefmt="%Y-%m-%dT%H:%M:%S%z",  # ISO 8601 format
        )
        handler.setFormatter(formatter)

        # Add handler to logger
        self.logger.addHandler(handler)

        # Prevent propagation to root logger
        self.logger.propagate = False

    def _log(
        self, level: int, event_type: str, session_id: str, context: dict[str, Any]
    ) -> None:
        """Internal method to log events with structured context.

        Args:
            level: Logging level (INFO, WARNING, ERROR)
            event_type: Type of event being logged
            session_id: User session identifier
            context: Dictionary of contextual information
        """
        # Convert context to JSON string
        context_json = json.dumps(context, default=str)

        # Log with extra fields for formatter
        self.logger.log(
            level,
            context_json,
            extra={"event_type": event_type, "session_id": session_id},
        )

    def log_ui_interaction(
        self, event_type: str, session_id: str, context: dict[str, Any]
    ) -> None:
        """Log general UI interaction event.

        Args:
            event_type: Type of UI interaction (e.g., "tab_switch", "field_focus")
            session_id: User session identifier
            context: Dictionary with interaction details
        """
        self._log(
            logging.INFO,
            event_type,
            session_id,
            {"timestamp": datetime.now().isoformat(), **context},
        )

    def log_button_click(
        self, button_id: str, module: str, phase: str | None, session_id: str
    ) -> None:
        """Log button click event.

        Args:
            button_id: Identifier of the clicked button
            module: Module name (e.g., "Module_A", "Module_V")
            phase: Phase context for Module V (e.g., "Phase_1", "Phase_2"),
                None for Module A
            session_id: User session identifier
        """
        context = {
            "timestamp": datetime.now().isoformat(),
            "button_id": button_id,
            "module": module,
        }

        if phase is not None:
            context["phase"] = phase

        self._log(logging.INFO, "button_click", session_id, context)

    def log_input_change(
        self,
        field_id: str,
        old_value: Any,
        new_value: Any,
        validation_result: bool,
        session_id: str,
    ) -> None:
        """Log input field modification.

        Args:
            field_id: Identifier of the input field
            old_value: Previous value before change
            new_value: New value after change
            validation_result: Whether the new value passed validation
            session_id: User session identifier
        """
        self._log(
            logging.INFO,
            "input_change",
            session_id,
            {
                "timestamp": datetime.now().isoformat(),
                "field_id": field_id,
                "old_value": old_value,
                "new_value": new_value,
                "validation_result": validation_result,
            },
        )

    def log_calculation(
        self,
        calc_type: str,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        engine_hash: str,
        session_id: str,
    ) -> None:
        """Log calculation execution.

        Args:
            calc_type: Type of calculation (e.g., "success_run_theorem",
                "tolerance_limits")
            inputs: Dictionary of input parameters
            outputs: Dictionary of output results
            engine_hash: SHA-256 hash of calculation engine
            session_id: User session identifier
        """
        self._log(
            logging.INFO,
            "calculation",
            session_id,
            {
                "timestamp": datetime.now().isoformat(),
                "calc_type": calc_type,
                "inputs": inputs,
                "outputs": outputs,
                "engine_hash": engine_hash,
            },
        )

    def log_validation_error(
        self,
        error_type: str,
        error_message: str,
        field_id: str,
        invalid_value: Any,
        session_id: str,
    ) -> None:
        """Log validation error.

        Args:
            error_type: Type of validation error (e.g., "range_error", "type_error")
            error_message: Human-readable error message
            field_id: Identifier of the field that failed validation
            invalid_value: The invalid value that was rejected
            session_id: User session identifier
        """
        self._log(
            logging.WARNING,
            "validation_error",
            session_id,
            {
                "timestamp": datetime.now().isoformat(),
                "error_type": error_type,
                "error_message": error_message,
                "field_id": field_id,
                "invalid_value": invalid_value,
            },
        )

    def log_phase_transition(
        self, source_phase: str, dest_phase: str, trigger: str, session_id: str
    ) -> None:
        """Log Module V phase transition.

        Args:
            source_phase: Source phase (e.g., "Phase_1")
            dest_phase: Destination phase (e.g., "Phase_2")
            trigger: What triggered the transition (e.g., "button_click",
                "auto_advance")
            session_id: User session identifier
        """
        self._log(
            logging.INFO,
            "phase_transition",
            session_id,
            {
                "timestamp": datetime.now().isoformat(),
                "source_phase": source_phase,
                "dest_phase": dest_phase,
                "trigger": trigger,
            },
        )

    def log_method_lock(
        self, method: str, lambda_param: float | None, p_value: float, session_id: str
    ) -> None:
        """Log transformation method lock.

        Args:
            method: Locked method name (e.g., "Logarithmic", "Box-Cox",
                "Non-Parametric")
            lambda_param: Lambda parameter if applicable (for Box-Cox, Yeo-Johnson)
            p_value: Shapiro-Wilk p-value that led to the lock
            session_id: User session identifier
        """
        context = {
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "p_value": p_value,
        }

        if lambda_param is not None:
            context["lambda_param"] = lambda_param

        self._log(logging.INFO, "method_lock", session_id, context)

    def log_outlier_exclusion(
        self, outlier_value: float, rationale: str, session_id: str
    ) -> None:
        """Log outlier exclusion.

        Args:
            outlier_value: The value being excluded as an outlier
            rationale: Engineering rationale provided by user
            session_id: User session identifier
        """
        self._log(
            logging.INFO,
            "outlier_exclusion",
            session_id,
            {
                "timestamp": datetime.now().isoformat(),
                "outlier_value": outlier_value,
                "rationale": rationale,
            },
        )

    def log_report_generation(
        self,
        report_type: str,
        engine_hash: str,
        validation_state: bool,
        session_id: str,
    ) -> None:
        """Log PDF report generation.

        Args:
            report_type: Type of report (e.g., "user_calculation",
                "validation_certificate")
            engine_hash: SHA-256 hash of calculation engine
            validation_state: Whether engine is in validated state
            session_id: User session identifier
        """
        self._log(
            logging.INFO,
            "report_generation",
            session_id,
            {
                "timestamp": datetime.now().isoformat(),
                "report_type": report_type,
                "engine_hash": engine_hash,
                "validation_state": validation_state,
            },
        )
