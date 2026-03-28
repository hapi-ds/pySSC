"""Tests for full report generator module.

This module tests the comprehensive full report generation functionality.
"""

import tempfile
from datetime import datetime
from pathlib import Path

from sample_size_calculator.full_report_generator import FullReportGenerator
from sample_size_calculator.models import CalculationReport


class TestFullReportGenerator:
    """Test suite for FullReportGenerator."""

    def test_generate_full_report_basic(self):
        """Test basic full report generation with minimal data."""
        # Create test calculation report
        report_data = CalculationReport(
            timestamp=datetime.now().isoformat(),
            module="Module A",
            inputs={"confidence": 95.0, "reliability": 95.0, "allowable_failures": 0},
            results={"sample_size": 59, "method": "Success Run Theorem"},
            engine_hash="test_hash_123",
            validation_state=True,
            method_path="Success Run Theorem (c=0)",
        )

        session_id = "test_session_123"

        # Generate full report
        pdf_bytes = FullReportGenerator.generate_full_report(
            calculation_report=report_data,
            session_id=session_id,
            log_dir="logs",
            validation_reports_dir="reports/validation",
        )

        # Verify PDF was generated
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"  # PDF magic number

    def test_generate_full_report_with_logs(self):
        """Test full report generation with audit logs."""
        # Create temporary log directory
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)
            log_file = log_dir / "audit.log"

            # Create sample log entries
            session_id = "test_session_456"
            log_entries = [
                f"[2024-03-15T14:30:22+0000] [INFO] [{session_id}] [button_click] "
                + '{"timestamp": "2024-03-15T14:30:22", "button_id": "calculate", "module": "Module_A"}',
                f"[2024-03-15T14:30:23+0000] [INFO] [{session_id}] [calculation] "
                + '{"timestamp": "2024-03-15T14:30:23", "calc_type": "success_run_theorem", "inputs": {}, "outputs": {}}',
            ]

            log_file.write_text("\n".join(log_entries))

            # Create test calculation report
            report_data = CalculationReport(
                timestamp=datetime.now().isoformat(),
                module="Module A",
                inputs={"confidence": 95.0, "reliability": 95.0},
                results={"sample_size": 59},
                engine_hash="test_hash_456",
                validation_state=False,
                method_path="Success Run Theorem",
            )

            # Generate full report
            pdf_bytes = FullReportGenerator.generate_full_report(
                calculation_report=report_data,
                session_id=session_id,
                log_dir=str(log_dir),
                validation_reports_dir="reports/validation",
            )

            # Verify PDF was generated
            assert pdf_bytes is not None
            assert len(pdf_bytes) > 0
            assert pdf_bytes[:4] == b"%PDF"

    def test_generate_full_report_with_validation_cert(self):
        """Test full report generation with validation certificate present."""
        # Create temporary validation directory
        with tempfile.TemporaryDirectory() as temp_dir:
            validation_dir = Path(temp_dir)
            cert_file = validation_dir / "validation_certificate_20240315_143022.pdf"
            cert_file.write_bytes(b"%PDF-1.4\ntest")

            # Create test calculation report
            report_data = CalculationReport(
                timestamp=datetime.now().isoformat(),
                module="Module V",
                inputs={"confidence": 95.0, "reliability": 95.0},
                results={"sample_size": 30},
                engine_hash="test_hash_789",
                validation_state=True,
                method_path="Parametric (Two-Sided)",
            )

            session_id = "test_session_789"

            # Generate full report
            pdf_bytes = FullReportGenerator.generate_full_report(
                calculation_report=report_data,
                session_id=session_id,
                log_dir="logs",
                validation_reports_dir=str(validation_dir),
            )

            # Verify PDF was generated
            assert pdf_bytes is not None
            assert len(pdf_bytes) > 0
            assert pdf_bytes[:4] == b"%PDF"

    def test_parse_log_line_valid(self):
        """Test parsing a valid log line."""
        log_line = (
            "[2024-03-15T14:30:22+0000] [INFO] [session_123] [button_click] "
            '{"timestamp": "2024-03-15T14:30:22", "button_id": "calculate", "module": "Module_A"}'
        )

        parsed = FullReportGenerator._parse_log_line(log_line)

        assert parsed is not None
        assert "timestamp" in parsed
        assert "event_type" in parsed
        assert "details" in parsed
        assert parsed["event_type"] == "button_click"

    def test_parse_log_line_invalid(self):
        """Test parsing an invalid log line."""
        log_line = "Invalid log line format"

        parsed = FullReportGenerator._parse_log_line(log_line)

        assert parsed is None

    def test_get_session_logs_empty(self):
        """Test retrieving logs when no logs exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logs = FullReportGenerator._get_session_logs(
                session_id="nonexistent_session",
                log_dir=temp_dir,
            )

            assert logs == []

    def test_get_session_logs_with_entries(self):
        """Test retrieving logs with matching session entries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)
            log_file = log_dir / "audit.log"

            session_id = "test_session_999"
            log_entries = [
                f"[2024-03-15T14:30:22+0000] [INFO] [{session_id}] [button_click] "
                + '{"timestamp": "2024-03-15T14:30:22", "button_id": "calculate"}',
                "[2024-03-15T14:30:23+0000] [INFO] [other_session] [button_click] "
                + '{"timestamp": "2024-03-15T14:30:23", "button_id": "calculate"}',
                f"[2024-03-15T14:30:24+0000] [INFO] [{session_id}] [calculation] "
                + '{"timestamp": "2024-03-15T14:30:24", "calc_type": "success_run_theorem"}',
            ]

            log_file.write_text("\n".join(log_entries))

            logs = FullReportGenerator._get_session_logs(
                session_id=session_id,
                log_dir=str(log_dir),
            )

            # Should only get logs for the specified session
            assert len(logs) == 2
            assert all(
                log["event_type"] in ["button_click", "calculation"] for log in logs
            )

    def test_get_latest_validation_info_no_dir(self):
        """Test getting validation info when directory doesn't exist."""
        info = FullReportGenerator._get_latest_validation_info(
            validation_reports_dir="/nonexistent/path"
        )

        assert info is None

    def test_get_latest_validation_info_no_files(self):
        """Test getting validation info when no PDF files exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            info = FullReportGenerator._get_latest_validation_info(
                validation_reports_dir=temp_dir
            )

            assert info is None

    def test_get_latest_validation_info_with_files(self):
        """Test getting validation info with PDF files present."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validation_dir = Path(temp_dir)

            # Create multiple validation certificates
            cert1 = validation_dir / "validation_certificate_20240315_143022.pdf"
            cert2 = validation_dir / "validation_certificate_20240316_103045.pdf"

            cert1.write_bytes(b"%PDF-1.4\ntest1")
            cert2.write_bytes(b"%PDF-1.4\ntest2")

            info = FullReportGenerator._get_latest_validation_info(
                validation_reports_dir=str(validation_dir)
            )

            assert info is not None
            assert "filename" in info
            assert "date" in info
            # Should get the most recent file
            assert "validation_certificate" in info["filename"]

    def test_generate_full_report_with_sampled_data(self):
        """Test full report generation with sampled data and outliers."""
        report_data = CalculationReport(
            timestamp=datetime.now().isoformat(),
            module="Module V",
            inputs={"confidence": 95.0, "reliability": 95.0},
            results={
                "sample_size": 30,
                "transformation_method": "None",
                "analysis_method": "Parametric",
            },
            engine_hash="test_hash_sampled_123",
            validation_state=True,
            method_path="Parametric (Two-Sided)",
            sampled_data=[1.5, 2.3, 3.1, 4.7, 5.2, 6.8, 7.9],
            detected_outliers=[
                {
                    "value": 7.9,
                    "is_excluded": True,
                    "rationale": "Sensor malfunction during high load test",
                },
                {"value": 1.5, "is_excluded": False, "rationale": None},
            ],
            outlier_exclusions=[
                {"value": 7.9, "rationale": "Sensor malfunction during high load test"}
            ],
        )

        session_id = "test_session_sampled_123"

        # Generate full report
        pdf_bytes = FullReportGenerator.generate_full_report(
            calculation_report=report_data,
            session_id=session_id,
            log_dir="logs",
            validation_reports_dir="reports/validation",
        )

        # Verify PDF was generated
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_full_report_without_sampled_data(self):
        """Test full report generation without sampled data (Module A style)."""
        report_data = CalculationReport(
            timestamp=datetime.now().isoformat(),
            module="Module A",
            inputs={"confidence": 95.0, "reliability": 95.0},
            results={"sample_size": 59, "method": "Success Run Theorem"},
            engine_hash="test_hash_no_sampled_123",
            validation_state=True,
            method_path="Success Run Theorem (c=0)",
        )

        session_id = "test_session_no_sampled_123"

        # Generate full report
        pdf_bytes = FullReportGenerator.generate_full_report(
            calculation_report=report_data,
            session_id=session_id,
            log_dir="logs",
            validation_reports_dir="reports/validation",
        )

        # Verify PDF was generated
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_full_report_with_only_outliers(self):
        """Test full report generation with outliers but no exclusions."""
        report_data = CalculationReport(
            timestamp=datetime.now().isoformat(),
            module="Module V",
            inputs={"confidence": 95.0, "reliability": 95.0},
            results={
                "sample_size": 30,
                "transformation_method": "None",
                "analysis_method": "Parametric",
            },
            engine_hash="test_hash_outliers_only_123",
            validation_state=True,
            method_path="Parametric (Two-Sided)",
            sampled_data=[1.5, 2.3, 3.1, 4.7, 5.2],
            detected_outliers=[{"value": 5.2, "is_excluded": False, "rationale": None}],
        )

        session_id = "test_session_outliers_only_123"

        # Generate full report
        pdf_bytes = FullReportGenerator.generate_full_report(
            calculation_report=report_data,
            session_id=session_id,
            log_dir="logs",
            validation_reports_dir="reports/validation",
        )

        # Verify PDF was generated
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"
