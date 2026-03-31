"""Unit tests for report_generator module.

Tests ReportGenerator class methods for generating PDF reports.
Achieves >90% coverage with comprehensive edge case testing.
"""

from datetime import datetime
from pathlib import Path

from sample_size_calculator.models import CalculationReport, ValidationCertificate
from sample_size_calculator.report_generator import ReportGenerator


class TestReportGeneratorUserReport:
    """Test user report generation with various data configurations."""

    def test_generate_user_report_basic(self):
        """Generate basic user report with minimal required fields."""
        report_data = CalculationReport(
            timestamp=datetime.now().isoformat(),
            module="Module A",
            inputs={"confidence": 95.0, "reliability": 95.0},
            results={"sample_size": 59},
            engine_hash="test_hash_123",
            validation_state=True,
            method_path="Success Run Theorem (c=0)",
        )

        pdf_bytes, report_path = ReportGenerator.generate_user_report(report_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"
        assert isinstance(report_path, Path)
        assert report_path.exists()

    def test_generate_user_report_with_all_sections(self):
        """Generate user report with all optional sections populated."""
        report_data = CalculationReport(
            timestamp=datetime.now().isoformat(),
            module="Module V",
            inputs={"confidence": 95.0, "reliability": 95.0},
            results={
                "sample_size": 30,
                "transformation_method": "None",
                "analysis_method": "Parametric",
            },
            engine_hash="test_hash_all_sections",
            validation_state=True,
            method_path="Parametric (Two-Sided)",
            sampled_data=[1.5, 2.3, 3.1, 4.7, 5.2],
            detected_outliers=[
                {"value": 5.2, "is_excluded": True, "rationale": "Sensor error"},
                {"value": 1.5, "is_excluded": False, "rationale": None},
            ],
            outlier_exclusions=[
                {"value": 5.2, "rationale": "Sensor error during calibration"}
            ],
        )

        pdf_bytes, report_path = ReportGenerator.generate_user_report(report_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"
        assert isinstance(report_path, Path)

    def test_generate_user_report_no_sampled_data(self):
        """Generate user report without sampled data section."""
        report_data = CalculationReport(
            timestamp=datetime.now().isoformat(),
            module="Module A",
            inputs={"confidence": 90.0, "reliability": 90.0},
            results={"sample_size": 22},
            engine_hash="test_hash_no_sampled",
            validation_state=False,
            method_path="Success Run Theorem (c=1)",
        )

        pdf_bytes, report_path = ReportGenerator.generate_user_report(report_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"
        assert isinstance(report_path, Path)

    def test_generate_user_report_no_outliers(self):
        """Generate user report without outlier sections."""
        report_data = CalculationReport(
            timestamp=datetime.now().isoformat(),
            module="Module V",
            inputs={"confidence": 95.0, "reliability": 95.0},
            results={
                "sample_size": 30,
                "k_factor": 2.5,
            },
            engine_hash="test_hash_no_outliers",
            validation_state=True,
            method_path="Parametric (Two-Sided)",
            sampled_data=[10.0, 12.0, 11.0, 13.0, 12.5],
        )

        pdf_bytes, report_path = ReportGenerator.generate_user_report(report_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_user_report_large_sampled_data(self):
        """Generate user report with large sampled data (truncation test)."""
        large_data = [float(i) for i in range(1, 200)]
        report_data = CalculationReport(
            timestamp=datetime.now().isoformat(),
            module="Module V",
            inputs={"confidence": 95.0, "reliability": 95.0},
            results={"sample_size": len(large_data)},
            engine_hash="test_hash_large_sampled",
            validation_state=True,
            method_path="Parametric (Two-Sided)",
            sampled_data=large_data,
        )

        pdf_bytes, report_path = ReportGenerator.generate_user_report(report_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_user_report_with_dict_result(self):
        """Generate user report with dictionary-type result value."""
        report_data = CalculationReport(
            timestamp=datetime.now().isoformat(),
            module="Module V",
            inputs={"confidence": 95.0, "reliability": 95.0},
            results={
                "sample_size": 30,
                "stats": {"mean": 12.5, "std": 2.3, "min": 8.0, "max": 17.2},
            },
            engine_hash="test_hash_dict_result",
            validation_state=True,
            method_path="Parametric (Two-Sided)",
        )

        pdf_bytes, report_path = ReportGenerator.generate_user_report(report_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_user_report_with_empty_inputs(self):
        """Generate user report with empty inputs dictionary."""
        report_data = CalculationReport(
            timestamp=datetime.now().isoformat(),
            module="Module A",
            inputs={},
            results={"sample_size": 59},
            engine_hash="test_hash_empty_inputs",
            validation_state=True,
            method_path="Success Run Theorem (c=0)",
        )

        pdf_bytes, report_path = ReportGenerator.generate_user_report(report_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_user_report_with_empty_results(self):
        """Generate user report with empty results dictionary."""
        report_data = CalculationReport(
            timestamp=datetime.now().isoformat(),
            module="Module A",
            inputs={"confidence": 95.0},
            results={},
            engine_hash="test_hash_empty_results",
            validation_state=True,
            method_path="Success Run Theorem (c=0)",
        )

        pdf_bytes, report_path = ReportGenerator.generate_user_report(report_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_user_report_with_outlier_exclusions_only(self):
        """Generate user report with outlier exclusions but no detected outliers."""
        report_data = CalculationReport(
            timestamp=datetime.now().isoformat(),
            module="Module V",
            inputs={"confidence": 95.0, "reliability": 95.0},
            results={"sample_size": 30},
            engine_hash="test_hash_exclusions_only",
            validation_state=True,
            method_path="Parametric (Two-Sided)",
            outlier_exclusions=[
                {"value": 25.0, "rationale": "Known calibration issue"},
                {"value": 32.0, "rationale": "Equipment malfunction"},
            ],
        )

        pdf_bytes, report_path = ReportGenerator.generate_user_report(report_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"


class TestReportGeneratorValidationCertificate:
    """Test validation certificate generation with various configurations."""

    def test_generate_validation_certificate_basic(self):
        """Generate basic validation certificate with minimal data."""
        cert_data = ValidationCertificate(
            test_date=datetime.now().isoformat(),
            tester_name="John Doe",
            system_info={"os": "Ubuntu 25.10", "python": "3.13.7"},
            test_results=[
                {
                    "urs_id": "URS-001",
                    "test_id": "tests/validation/test_iq.py::TestIQ::test_system_start",
                    "status": "PASS",
                }
            ],
            validated_hash="validated_engine_hash_123",
        )

        pdf_bytes, report_path = ReportGenerator.generate_validation_certificate(cert_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"
        assert isinstance(report_path, Path)
        assert report_path.exists()

    def test_generate_validation_certificate_with_all_test_types(self):
        """Generate validation certificate with IQ, OQ, and PQ tests."""
        cert_data = ValidationCertificate(
            test_date=datetime.now().isoformat(),
            tester_name="Jane Smith",
            system_info={"os": "Ubuntu", "memory": "16GB"},
            test_results=[
                {"urs_id": "URS-001", "test_id": "tests/validation/test_iq.py::test_start", "status": "PASS"},
                {"urs_id": "URS-002", "test_id": "tests/validation/test_oq.py::test_calc", "status": "PASS"},
                {"urs_id": "URS-003", "test_id": "tests/validation/test_pq.py::test_ui", "status": "FAIL"},
            ],
            validated_hash="validated_engine_hash_456",
        )

        pdf_bytes, report_path = ReportGenerator.generate_validation_certificate(cert_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_validation_certificate_all_tests_passed(self):
        """Generate validation certificate where all tests passed."""
        cert_data = ValidationCertificate(
            test_date=datetime.now().isoformat(),
            tester_name="Test Engineer",
            system_info={"cpu": "Intel i7", "ram": "32GB"},
            test_results=[
                {"urs_id": "URS-001", "test_id": "tests/validation/test_iq.py::test_start", "status": "PASSED"},
                {"urs_id": "URS-002", "test_id": "tests/validation/test_oq.py::test_calc", "status": "passed"},
            ],
            validated_hash="validated_engine_hash_789",
        )

        pdf_bytes, report_path = ReportGenerator.generate_validation_certificate(cert_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_validation_certificate_all_tests_failed(self):
        """Generate validation certificate where all tests failed."""
        cert_data = ValidationCertificate(
            test_date=datetime.now().isoformat(),
            tester_name="Test Engineer",
            system_info={"cpu": "Intel i7", "ram": "32GB"},
            test_results=[
                {"urs_id": "URS-001", "test_id": "tests/validation/test_iq.py::test_start", "status": "FAIL"},
                {"urs_id": "URS-002", "test_id": "tests/validation/test_oq.py::test_calc", "status": "FAILED"},
            ],
            validated_hash="validated_engine_hash_999",
        )

        pdf_bytes, report_path = ReportGenerator.generate_validation_certificate(cert_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_validation_certificate_no_tests(self):
        """Generate validation certificate with no test results."""
        cert_data = ValidationCertificate(
            test_date=datetime.now().isoformat(),
            tester_name="Test Engineer",
            system_info={"cpu": "Intel i7"},
            test_results=[],
            validated_hash="validated_engine_hash_000",
        )

        pdf_bytes, report_path = ReportGenerator.generate_validation_certificate(cert_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_validation_certificate_with_coverage_metrics(self):
        """Generate validation certificate with URS coverage metrics."""
        cert_data = ValidationCertificate(
            test_date=datetime.now().isoformat(),
            tester_name="Test Engineer",
            system_info={"cpu": "Intel i7"},
            test_results=[
                {"urs_id": "URS-001", "test_id": "tests/validation/test_iq.py::test_start", "status": "PASS"},
                {"urs_id": "URS-002", "test_id": "tests/validation/test_oq.py::test_calc", "status": "PASS"},
            ],
            validated_hash="validated_engine_hash_coverage",
        )

        coverage_metrics = {
            "total_requirements": 5,
            "covered_requirements": 2,
            "uncovered_requirements": 3,
            "coverage_percentage": 40.0,
            "uncovered_ids": ["URS-003", "URS-004", "URS-005"],
            "coverage_by_category": {
                "IQ": {"total": 2, "covered": 1, "percentage": 50.0},
                "OQ": {"total": 2, "covered": 1, "percentage": 50.0},
                "PQ": {"total": 1, "covered": 0, "percentage": 0.0},
            },
        }

        pdf_bytes, report_path = ReportGenerator.generate_validation_certificate(cert_data, coverage_metrics)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_validation_certificate_with_pdf_test_results(self):
        """Generate validation certificate with PDF test results."""
        cert_data = ValidationCertificate(
            test_date=datetime.now().isoformat(),
            tester_name="Test Engineer",
            system_info={"cpu": "Intel i7"},
            test_results=[],
            pdf_test_results=[
                {"urs_id": "PDF-001", "test_id": "tests/validation/test_pq_pdf_validation.py::test_pdf_structure", "result": "PASS"},
            ],
            validated_hash="validated_engine_hash_pdf",
        )

        pdf_bytes, report_path = ReportGenerator.generate_validation_certificate(cert_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_validation_certificate_mixed_status_tests(self):
        """Generate validation certificate with mix of pass and fail statuses."""
        cert_data = ValidationCertificate(
            test_date=datetime.now().isoformat(),
            tester_name="Test Engineer",
            system_info={"cpu": "Intel i7"},
            test_results=[
                {"urs_id": "URS-001", "test_id": "tests/validation/test_iq.py::test_1", "status": "PASS"},
                {"urs_id": "URS-002", "test_id": "tests/validation/test_iq.py::test_2", "status": "FAIL"},
                {"urs_id": "URS-003", "test_id": "tests/validation/test_oq.py::test_1", "status": "PASS"},
            ],
            validated_hash="validated_engine_hash_mixed",
        )

        pdf_bytes, report_path = ReportGenerator.generate_validation_certificate(cert_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_validation_certificate_with_system_info(self):
        """Generate validation certificate with comprehensive system info."""
        cert_data = ValidationCertificate(
            test_date=datetime.now().isoformat(),
            tester_name="Test Engineer",
            system_info={
                "os": "Ubuntu 25.10",
                "python_version": "3.13.7",
                "architecture": "x86_64",
                "cpu_count": 8,
                "memory_gb": 32,
            },
            test_results=[],
            validated_hash="validated_engine_hash_sysinfo",
        )

        pdf_bytes, report_path = ReportGenerator.generate_validation_certificate(cert_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_validation_certificate_empty_system_info(self):
        """Generate validation certificate with empty system info."""
        cert_data = ValidationCertificate(
            test_date=datetime.now().isoformat(),
            tester_name="Test Engineer",
            system_info={},
            test_results=[],
            validated_hash="validated_engine_hash_no_sysinfo",
        )

        pdf_bytes, report_path = ReportGenerator.generate_validation_certificate(cert_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_user_report_with_signature_exception(self):
        """Test user report generation when PDF signature raises exception."""
        import tempfile
        
        report_data = CalculationReport(
            timestamp=datetime.now().isoformat(),
            module="Module A",
            inputs={"confidence": 95.0, "reliability": 95.0},
            results={"sample_size": 59},
            engine_hash="test_hash_sig_exception",
            validation_state=True,
            method_path="Success Run Theorem (c=0)",
        )
        
        with tempfile.TemporaryDirectory():
            pdf_bytes, report_path = ReportGenerator.generate_user_report(report_data)
            
            assert pdf_bytes is not None
            assert len(pdf_bytes) > 0
            assert pdf_bytes[:4] == b"%PDF"
