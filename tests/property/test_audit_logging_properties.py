"""Property-based tests for audit logging.

This module contains property-based tests using Hypothesis to verify
the correctness of audit logging functionality including event logging,
format consistency, and non-idempotence.
"""

import json
import re
import tempfile
from pathlib import Path
from typing import Any

from hypothesis import given
from hypothesis import strategies as st

from src.sample_size_calculator.audit_logger import AuditLogger

# Strategies for generating test data
session_id_strategy = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"
    ),
)

field_id_strategy = st.text(
    min_size=1,
    max_size=30,
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"
    ),
)

button_id_strategy = st.text(
    min_size=1,
    max_size=30,
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"
    ),
)

module_strategy = st.sampled_from(["Module_A", "Module_V"])
phase_strategy = st.one_of(
    st.none(), st.sampled_from(["Phase_1", "Phase_2", "Phase_3", "Phase_4"])
)

value_strategy = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-1000, max_value=1000),
    st.floats(
        min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False
    ),
    st.text(min_size=0, max_size=100),
)


class TestAuditLogging:
    """Property-based tests for audit logging functionality."""

    @given(
        button_id=button_id_strategy,
        module=module_strategy,
        phase=phase_strategy,
        session_id=session_id_strategy,
    )
    def test_property_34_comprehensive_event_logging_button_click(
        self, button_id: str, module: str, phase: str | None, session_id: str
    ) -> None:
        """Property 34: Comprehensive Event Logging - Button Click.

        **Validates: Requirements 38.1, 38.2**

        When a user clicks a button, the system should log the event with
        button identifier, module name, phase context, and session ID.
        """
        # Create temporary log directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            logger = AuditLogger(log_dir=tmp_dir)

            # Log button click
            logger.log_button_click(button_id, module, phase, session_id)

            # Read log file
            log_file = Path(tmp_dir) / "audit.log"
            assert log_file.exists(), "Log file should be created"

            with open(log_file) as f:
                log_content = f.read()

            # Verify log entry exists
            assert len(log_content) > 0, "Log file should not be empty"

            # Verify session ID is in log
            assert session_id in log_content, (
                f"Session ID {session_id} should be in log"
            )

            # Verify event type is in log
            assert "button_click" in log_content, (
                "Event type 'button_click' should be in log"
            )

            # Verify button_id is in log (may be JSON-escaped)
            # Check both raw and JSON-escaped versions
            button_id_found = (
                button_id in log_content or json.dumps(button_id)[1:-1] in log_content
            )
            assert button_id_found, f"Button ID {button_id} should be in log"

            # Verify module is in log
            assert module in log_content, f"Module {module} should be in log"

            # Verify phase is in log if provided
            if phase is not None:
                assert phase in log_content, f"Phase {phase} should be in log"

    @given(
        field_id=field_id_strategy,
        old_value=value_strategy,
        new_value=value_strategy,
        validation_result=st.booleans(),
        session_id=session_id_strategy,
    )
    def test_property_34_comprehensive_event_logging_input_change(
        self,
        field_id: str,
        old_value: Any,
        new_value: Any,
        validation_result: bool,
        session_id: str,
    ) -> None:
        """Property 34: Comprehensive Event Logging - Input Change.

        **Validates: Requirements 38.1, 38.3**

        When a user modifies input data, the system should log the field identifier,
        previous value, new value, validation result, and session ID.
        """
        # Create temporary log directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            logger = AuditLogger(log_dir=tmp_dir)

            # Log input change
            logger.log_input_change(
                field_id, old_value, new_value, validation_result, session_id
            )

            # Read log file
            log_file = Path(tmp_dir) / "audit.log"
            assert log_file.exists(), "Log file should be created"

            with open(log_file) as f:
                log_content = f.read()

            # Verify log entry exists
            assert len(log_content) > 0, "Log file should not be empty"

            # Verify session ID is in log
            assert session_id in log_content, (
                f"Session ID {session_id} should be in log"
            )

            # Verify event type is in log
            assert "input_change" in log_content, (
                "Event type 'input_change' should be in log"
            )

            # Verify field_id is in log (may be JSON-escaped)
            # Check both raw and JSON-escaped versions
            field_id_found = (
                field_id in log_content or json.dumps(field_id)[1:-1] in log_content
            )
            assert field_id_found, f"Field ID {field_id} should be in log"

            # Verify validation_result is in log
            assert str(validation_result).lower() in log_content.lower(), (
                f"Validation result {validation_result} should be in log"
            )

    @given(
        calc_type=st.text(min_size=1, max_size=50),
        engine_hash=st.text(min_size=64, max_size=64, alphabet="0123456789abcdef"),
        session_id=session_id_strategy,
    )
    def test_property_34_comprehensive_event_logging_calculation(
        self, calc_type: str, engine_hash: str, session_id: str
    ) -> None:
        """Property 34: Comprehensive Event Logging - Calculation.

        **Validates: Requirements 38.1, 38.4**

        When a calculation is performed, the system should log the calculation type,
        input parameters, output results, calculation engine hash, and session ID.
        """
        # Create temporary log directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            logger = AuditLogger(log_dir=tmp_dir)

            # Log calculation
            inputs = {"confidence": 95.0, "reliability": 95.0}
            outputs = {"sample_size": 59}
            logger.log_calculation(calc_type, inputs, outputs, engine_hash, session_id)

            # Read log file
            log_file = Path(tmp_dir) / "audit.log"
            assert log_file.exists(), "Log file should be created"

            with open(log_file) as f:
                log_content = f.read()

            # Verify log entry exists
            assert len(log_content) > 0, "Log file should not be empty"

            # Verify session ID is in log
            assert session_id in log_content, (
                f"Session ID {session_id} should be in log"
            )

            # Verify event type is in log
            assert "calculation" in log_content, (
                "Event type 'calculation' should be in log"
            )

            # Verify calc_type is in log (may be JSON-escaped)
            # Check both raw and JSON-escaped versions
            calc_type_found = (
                calc_type in log_content or json.dumps(calc_type)[1:-1] in log_content
            )
            assert calc_type_found, f"Calculation type {calc_type} should be in log"

            # Verify engine_hash is in log
            assert engine_hash in log_content, (
                f"Engine hash {engine_hash} should be in log"
            )

    @given(
        source_phase=st.sampled_from(["Phase_1", "Phase_2", "Phase_3"]),
        dest_phase=st.sampled_from(["Phase_2", "Phase_3", "Phase_4"]),
        trigger=st.text(min_size=1, max_size=30),
        session_id=session_id_strategy,
    )
    def test_property_34_comprehensive_event_logging_phase_transition(
        self, source_phase: str, dest_phase: str, trigger: str, session_id: str
    ) -> None:
        """Property 34: Comprehensive Event Logging - Phase Transition.

        **Validates: Requirements 38.1, 38.6**

        When a phase transition occurs in Module V, the system should log
        the source phase, destination phase, trigger, and session ID.
        """
        # Create temporary log directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            logger = AuditLogger(log_dir=tmp_dir)

            # Log phase transition
            logger.log_phase_transition(source_phase, dest_phase, trigger, session_id)

            # Read log file
            log_file = Path(tmp_dir) / "audit.log"
            assert log_file.exists(), "Log file should be created"

            with open(log_file) as f:
                log_content = f.read()

            # Verify log entry exists
            assert len(log_content) > 0, "Log file should not be empty"

            # Verify session ID is in log
            assert session_id in log_content, (
                f"Session ID {session_id} should be in log"
            )

            # Verify event type is in log
            assert "phase_transition" in log_content, (
                "Event type 'phase_transition' should be in log"
            )

            # Verify source_phase is in log
            assert source_phase in log_content, (
                f"Source phase {source_phase} should be in log"
            )

            # Verify dest_phase is in log
            assert dest_phase in log_content, (
                f"Destination phase {dest_phase} should be in log"
            )

    @given(
        method=st.sampled_from(
            ["Logarithmic", "Box-Cox", "Yeo-Johnson", "Non-Parametric"]
        ),
        lambda_param=st.one_of(st.none(), st.floats(min_value=-5.0, max_value=5.0)),
        p_value=st.floats(min_value=0.0, max_value=1.0),
        session_id=session_id_strategy,
    )
    def test_property_34_comprehensive_event_logging_method_lock(
        self, method: str, lambda_param: float | None, p_value: float, session_id: str
    ) -> None:
        """Property 34: Comprehensive Event Logging - Method Lock.

        **Validates: Requirements 38.1, 38.7**

        When a transformation method is locked, the system should log
        the selected method, lambda parameter (if applicable), p-value, and session ID.
        """
        # Create temporary log directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            logger = AuditLogger(log_dir=tmp_dir)

            # Log method lock
            logger.log_method_lock(method, lambda_param, p_value, session_id)

            # Read log file
            log_file = Path(tmp_dir) / "audit.log"
            assert log_file.exists(), "Log file should be created"

            with open(log_file) as f:
                log_content = f.read()

            # Verify log entry exists
            assert len(log_content) > 0, "Log file should not be empty"

            # Verify session ID is in log
            assert session_id in log_content, (
                f"Session ID {session_id} should be in log"
            )

            # Verify event type is in log
            assert "method_lock" in log_content, (
                "Event type 'method_lock' should be in log"
            )

            # Verify method is in log
            assert method in log_content, f"Method {method} should be in log"

    @given(
        event_count=st.integers(min_value=1, max_value=10),
        session_id=session_id_strategy,
    )
    def test_property_35_log_format_consistency(
        self, event_count: int, session_id: str
    ) -> None:
        """Property 35: Log Format Consistency.

        **Validates: Requirements 38.11, 38.12, 38.16**

        All log entries should follow the structured format:
        [TIMESTAMP] [LEVEL] [SESSION_ID] [EVENT_TYPE] {context_json}

        Timestamps should be in ISO 8601 format.
        """
        # Create temporary log directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            logger = AuditLogger(log_dir=tmp_dir)

            # Log multiple events
            for i in range(event_count):
                logger.log_button_click(f"button_{i}", "Module_A", None, session_id)

            # Read log file
            log_file = Path(tmp_dir) / "audit.log"
            assert log_file.exists(), "Log file should be created"

            with open(log_file) as f:
                log_lines = f.readlines()

            # Verify we have the expected number of log entries
            assert len(log_lines) == event_count, (
                f"Expected {event_count} log entries, got {len(log_lines)}"
            )

            # Define regex pattern for log format
            # [TIMESTAMP] [LEVEL] [SESSION_ID] [EVENT_TYPE] {context_json}
            # ISO 8601 timestamp: YYYY-MM-DDTHH:MM:SS+ZZZZ or YYYY-MM-DDTHH:MM:SS
            log_pattern = re.compile(
                r"^\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]?\d*)\] "
                r"\[(INFO|WARNING|ERROR)\] "
                r"\[([^\]]+)\] "
                r"\[([^\]]+)\] "
                r"(\{.+\})$"
            )

            # Verify each log line matches the format
            for i, line in enumerate(log_lines):
                match = log_pattern.match(line.strip())
                assert match is not None, (
                    f"Log line {i + 1} does not match expected format:\n{line}"
                )

                timestamp, level, logged_session_id, event_type, context_json = (
                    match.groups()
                )

                # Verify timestamp is ISO 8601 format
                assert "T" in timestamp, (
                    f"Timestamp should contain 'T' separator: {timestamp}"
                )

                # Verify level is valid
                assert level in ["INFO", "WARNING", "ERROR"], (
                    f"Invalid log level: {level}"
                )

                # Verify session ID matches
                assert logged_session_id == session_id, (
                    f"Session ID mismatch: expected {session_id}, got {logged_session_id}"
                )

                # Verify event type is present
                assert len(event_type) > 0, "Event type should not be empty"

                # Verify context is valid JSON
                try:
                    context = json.loads(context_json)
                    assert isinstance(context, dict), "Context should be a dictionary"
                except json.JSONDecodeError as e:
                    raise AssertionError(
                        f"Context is not valid JSON: {context_json}"
                    ) from e

    @given(
        session_id=session_id_strategy,
        button_id=button_id_strategy,
    )
    def test_property_36_logging_non_idempotence(
        self, session_id: str, button_id: str
    ) -> None:
        """Property 36: Logging Non-Idempotence.

        **Validates: Requirements 38.17**

        Writing the same event multiple times should produce separate
        timestamped entries (no idempotence for logging).
        """
        # Create temporary log directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            logger = AuditLogger(log_dir=tmp_dir)

            # Log the same event multiple times
            num_logs = 3
            for _ in range(num_logs):
                logger.log_button_click(button_id, "Module_A", None, session_id)

            # Read log file
            log_file = Path(tmp_dir) / "audit.log"
            assert log_file.exists(), "Log file should be created"

            with open(log_file) as f:
                log_lines = f.readlines()

            # Verify we have multiple separate entries
            assert len(log_lines) == num_logs, (
                f"Expected {num_logs} separate log entries, got {len(log_lines)}"
            )

            # Extract timestamps from each log entry
            timestamps = []
            for line in log_lines:
                # Extract timestamp from format: [TIMESTAMP] [LEVEL] ...
                match = re.match(r"^\[([^\]]+)\]", line)
                assert match is not None, f"Could not extract timestamp from: {line}"
                timestamps.append(match.group(1))

            # Verify all timestamps are present (may be identical if logged very quickly)
            assert len(timestamps) == num_logs, (
                f"Expected {num_logs} timestamps, got {len(timestamps)}"
            )

            # Verify each log entry is complete and separate
            for i, line in enumerate(log_lines):
                # Check both raw and JSON-escaped versions for button_id
                button_id_found = (
                    button_id in line or json.dumps(button_id)[1:-1] in line
                )
                assert button_id_found, (
                    f"Log entry {i + 1} should contain button_id {button_id}"
                )
                assert session_id in line, (
                    f"Log entry {i + 1} should contain session_id {session_id}"
                )
