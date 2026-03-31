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

    def test_extract_validation_cert_info_no_file(self):
        """Test extracting cert info when file doesn't exist."""
        info = FullReportGenerator._extract_validation_certificate_info(
            Path("/nonexistent/path/validation_certificate.pdf")
        )

        assert info is not None
        assert info["total_tests"] == 0
        assert info["passed_tests"] == 0
        assert info["failed_tests"] == 0
        assert info["validation_status"] == "N/A"

    def test_extract_validation_cert_info_with_test_results(self):
        """Test extracting cert info with test results JSON files."""
        import json

        with tempfile.TemporaryDirectory() as temp_dir:
            validation_dir = Path(temp_dir)

            # Create a mock certificate file
            cert_file = validation_dir / "validation_certificate_20240315_143022.pdf"
            cert_file.write_bytes(b"%PDF-1.4\ntest")

            # Create test results files
            iq_results = {
                "tests": [
                    {"nodeid": "test_iq.py::test_1", "outcome": "passed"},
                    {"nodeid": "test_iq.py::test_2", "outcome": "passed"},
                ]
            }
            oq_results = {
                "tests": [
                    {"nodeid": "test_oq.py::test_1", "outcome": "failed"},
                ]
            }

            (validation_dir / "test_results_iq.json").write_text(json.dumps(iq_results))
            (validation_dir / "test_results_oq.json").write_text(json.dumps(oq_results))

            info = FullReportGenerator._extract_validation_certificate_info(cert_file)

            assert info is not None
            assert info["total_tests"] == 3
            assert info["passed_tests"] == 2
            assert info["failed_tests"] == 1
            assert info["validation_status"] == "FAILED"

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

    def test_extract_validation_cert_info_all_passed(self):
        """Test extracting cert info when all tests passed."""
        import json

        with tempfile.TemporaryDirectory() as temp_dir:
            validation_dir = Path(temp_dir)
            cert_file = validation_dir / "validation_certificate_20240315_143022.pdf"
            cert_file.write_bytes(b"%PDF-1.4\ntest")

            iq_results = {
                "tests": [
                    {"nodeid": "test_iq.py::test_1", "outcome": "passed"},
                    {"nodeid": "test_iq.py::test_2", "outcome": "passed"},
                ]
            }
            oq_results = {
                "tests": [
                    {"nodeid": "test_oq.py::test_1", "outcome": "passed"},
                ]
            }

            (validation_dir / "test_results_iq.json").write_text(json.dumps(iq_results))
            (validation_dir / "test_results_oq.json").write_text(json.dumps(oq_results))

            info = FullReportGenerator._extract_validation_certificate_info(cert_file)

            assert info is not None
            assert info["total_tests"] == 3
            assert info["passed_tests"] == 3
            assert info["failed_tests"] == 0
            assert info["validation_status"] == "PASSED"

    def test_extract_validation_cert_info_mixed_outcomes(self):
        """Test extracting cert info with mixed pass/fail outcomes."""
        import json

        with tempfile.TemporaryDirectory() as temp_dir:
            validation_dir = Path(temp_dir)
            cert_file = validation_dir / "validation_certificate_20240315_143022.pdf"
            cert_file.write_bytes(b"%PDF-1.4\ntest")

            iq_results = {
                "tests": [
                    {"nodeid": "test_iq.py::test_1", "outcome": "passed"},
                    {"nodeid": "test_iq.py::test_2", "outcome": "failed"},
                    {"nodeid": "test_iq.py::test_3", "outcome": "unknown"},
                ]
            }

            (validation_dir / "test_results_iq.json").write_text(json.dumps(iq_results))

            info = FullReportGenerator._extract_validation_certificate_info(cert_file)

            assert info is not None
            assert info["total_tests"] == 3
            assert info["passed_tests"] == 1
            assert info["failed_tests"] == 2
            assert info["validation_status"] == "FAILED"

    def test_extract_validation_cert_info_with_coverage_metrics(self):
        """Test extracting cert info with coverage metrics file."""
        import json

        with tempfile.TemporaryDirectory() as temp_dir:
            validation_dir = Path(temp_dir)
            cert_file = validation_dir / "validation_certificate_20240315_143022.pdf"
            cert_file.write_bytes(b"%PDF-1.4\ntest")

            coverage_metrics = {
                "coverage_percentage": 87.5,
                "total_requirements": 40,
                "covered_requirements": 35,
            }
            (validation_dir / "coverage_metrics.json").write_text(
                json.dumps(coverage_metrics)
            )

            info = FullReportGenerator._extract_validation_certificate_info(cert_file)

            assert info is not None
            assert info["coverage_percentage"] == 87.5

    def test_extract_validation_cert_info_with_vtm_file(self):
        """Test extracting tester name from VTM file."""
        import json

        with tempfile.TemporaryDirectory() as temp_dir:
            validation_dir = Path(temp_dir)
            cert_file = validation_dir / "validation_certificate_20240315_143022.pdf"
            cert_file.write_bytes(b"%PDF-1.4\ntest")

            vtm_content = """# Validation Traceability Matrix
# Tester: John Doe
# Date: 2024-03-15
URS_ID,Test_ID,Status
URS-001,test_iq.py::test_1,PASSED
"""
            (validation_dir / "validation_traceability_matrix.csv").write_text(
                vtm_content
            )

            iq_results = {
                "tests": [
                    {"nodeid": "test_iq.py::test_1", "outcome": "passed"},
                ]
            }
            (validation_dir / "test_results_iq.json").write_text(json.dumps(iq_results))

            info = FullReportGenerator._extract_validation_certificate_info(cert_file)

            assert info is not None
            assert info["tester_name"] == "John Doe"

    def test_extract_validation_cert_info_empty_json(self):
        """Test extracting cert info with empty test results."""
        import json

        with tempfile.TemporaryDirectory() as temp_dir:
            validation_dir = Path(temp_dir)
            cert_file = validation_dir / "validation_certificate_20240315_143022.pdf"
            cert_file.write_bytes(b"%PDF-1.4\ntest")

            empty_results = {"tests": []}
            (validation_dir / "test_results_iq.json").write_text(json.dumps(empty_results))

            info = FullReportGenerator._extract_validation_certificate_info(cert_file)

            assert info is not None
            assert info["total_tests"] == 0
            assert info["passed_tests"] == 0
            assert info["failed_tests"] == 0

    def test_extract_validation_cert_info_corrupt_json(self):
        """Test extracting cert info with corrupt JSON file."""

        with tempfile.TemporaryDirectory() as temp_dir:
            validation_dir = Path(temp_dir)
            cert_file = validation_dir / "validation_certificate_20240315_143022.pdf"
            cert_file.write_bytes(b"%PDF-1.4\ntest")

            (validation_dir / "test_results_iq.json").write_text("this is not json {")

            info = FullReportGenerator._extract_validation_certificate_info(cert_file)

            assert info is not None
            assert info["total_tests"] == 0

    def test_extract_validation_cert_info_missing_json_files(self):
        """Test extracting cert info when no JSON files exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            validation_dir = Path(temp_dir)
            cert_file = validation_dir / "validation_certificate_20240315_143022.pdf"
            cert_file.write_bytes(b"%PDF-1.4\ntest")

            info = FullReportGenerator._extract_validation_certificate_info(cert_file)

            assert info is not None
            assert info["total_tests"] == 0
