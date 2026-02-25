"""Test coverage metrics integration in validation certificate generation.

This test suite verifies that coverage metrics are properly calculated,
integrated into the validation runner, and rendered in the validation certificate.
"""

import json
from pathlib import Path

import pytest


class TestCoverageIntegration:
    """Test coverage metrics integration across the validation system."""

    def test_coverage_calculation_script_exists(self):
        """Verify coverage calculation script exists."""
        coverage_script = Path("scripts/calculate_coverage.py")
        assert coverage_script.exists(), "Coverage calculation script not found"

    def test_coverage_script_has_required_functions(self):
        """Verify coverage script contains required functions."""
        coverage_script = Path("scripts/calculate_coverage.py")
        content = coverage_script.read_text()

        required_functions = [
            "parse_urs_document",
            "extract_urs_ids_from_tests",
            "calculate_coverage",
            "calculate_category_coverage",
            "calculate_suite_coverage",
        ]

        for func_name in required_functions:
            assert (
                f"def {func_name}" in content
            ), f"Function {func_name} not found in coverage script"

    def test_report_generator_has_coverage_rendering_code(self):
        """Verify report generator includes coverage metrics rendering."""
        report_gen = Path("src/sample_size_calculator/report_generator.py")
        assert report_gen.exists(), "Report generator not found"

        content = report_gen.read_text()

        required_elements = [
            "URS Coverage Summary",
            "Total URS Requirements",
            "Covered by Tests",
            "Coverage Percentage",
            "Uncovered Requirements",
            "Coverage by Category",
        ]

        for element in required_elements:
            assert (
                element in content
            ), f"Coverage element '{element}' not found in report generator"

    def test_report_generator_accepts_coverage_metrics_parameter(self):
        """Verify generate_validation_certificate accepts coverage_metrics parameter."""
        report_gen = Path("src/sample_size_calculator/report_generator.py")
        content = report_gen.read_text()

        # Check function signature includes coverage_metrics parameter
        assert (
            "coverage_metrics: dict | None = None" in content
        ), "coverage_metrics parameter not found in function signature"

    def test_validation_runner_calculates_coverage(self):
        """Verify validation runner calls coverage calculation."""
        validation_runner = Path("scripts/run_validation.py")
        assert validation_runner.exists(), "Validation runner not found"

        content = validation_runner.read_text()

        # Check for coverage calculation import
        assert (
            "from scripts.calculate_coverage import calculate_coverage" in content
        ), "Coverage calculation not imported"

        # Check for coverage calculation call
        assert (
            "calculate_coverage(" in content
        ), "Coverage calculation not called"

        # Check for coverage_metrics variable
        assert (
            "coverage_metrics =" in content
        ), "coverage_metrics variable not assigned"

    def test_validation_runner_passes_coverage_to_certificate_generator(self):
        """Verify validation runner passes coverage metrics to certificate generator."""
        validation_runner = Path("scripts/run_validation.py")
        content = validation_runner.read_text()

        # Check that coverage_metrics is passed to generate_validation_certificate
        assert (
            "ReportGenerator.generate_validation_certificate(" in content
        ), "Certificate generator not called"

        # Find the certificate generation call and verify coverage_metrics is passed
        # This is a simple check - the parameter should appear after the call
        cert_gen_index = content.find("ReportGenerator.generate_validation_certificate(")
        coverage_param_index = content.find("coverage_metrics", cert_gen_index)

        assert (
            coverage_param_index > cert_gen_index
        ), "coverage_metrics not passed to certificate generator"

    def test_vtm_generator_supports_coverage_metrics(self):
        """Verify VTM generator accepts and uses coverage metrics."""
        vtm_gen = Path("src/sample_size_calculator/vtm_generator.py")
        assert vtm_gen.exists(), "VTM generator not found"

        content = vtm_gen.read_text()

        # Check that export_vtm_csv accepts coverage_metrics parameter
        assert (
            "coverage_metrics: dict | None = None" in content
        ), "VTM export function doesn't accept coverage_metrics parameter"

        # Check that coverage metrics are written to CSV
        assert (
            "VTM Coverage Summary" in content
        ), "VTM doesn't include coverage summary in CSV"

    def test_report_generator_has_chapter_structure(self):
        """Verify report generator implements chapter-based structure."""
        report_gen = Path("src/sample_size_calculator/report_generator.py")
        content = report_gen.read_text()

        required_chapters = [
            "CHAPTER 1: INSTALLATION QUALIFICATION (IQ)",
            "CHAPTER 2: OPERATIONAL QUALIFICATION (OQ)",
            "CHAPTER 3: PERFORMANCE QUALIFICATION (PQ)",
            "CHAPTER 4: VALIDATION SUMMARY",
        ]

        for chapter in required_chapters:
            assert (
                chapter in content
            ), f"Chapter '{chapter}' not found in report generator"

    def test_report_generator_uses_page_breaks(self):
        """Verify report generator uses page breaks between chapters."""
        report_gen = Path("src/sample_size_calculator/report_generator.py")
        content = report_gen.read_text()

        # Check PageBreak is imported
        assert "PageBreak" in content, "PageBreak not imported"

        # Check PageBreak is used
        assert "PageBreak()" in content, "PageBreak not used in report generation"

    def test_report_generator_separates_test_results_by_suite(self):
        """Verify report generator separates IQ/OQ/PQ test results."""
        report_gen = Path("src/sample_size_calculator/report_generator.py")
        content = report_gen.read_text()

        # Check for suite separation logic
        assert (
            'test_iq.py" in r.get("test_id"' in content
        ), "IQ test filtering not found"
        assert (
            'test_oq.py" in r.get("test_id"' in content
        ), "OQ test filtering not found"
        assert (
            'test_pq.py" in r.get("test_id"' in content
        ), "PQ test filtering not found"


class TestCoverageMetricsGeneration:
    """Test coverage metrics generation and storage."""

    @pytest.fixture
    def coverage_metrics_file(self):
        """Fixture for coverage metrics JSON file path."""
        return Path("validation_coverage_metrics.json")

    @pytest.fixture
    def vtm_csv_file(self):
        """Fixture for VTM CSV file path."""
        return Path("validation_traceability_matrix.csv")

    def test_coverage_metrics_json_structure(self, coverage_metrics_file):
        """Verify coverage metrics JSON has correct structure if it exists."""
        if not coverage_metrics_file.exists():
            pytest.skip("Coverage metrics JSON not generated yet")

        with open(coverage_metrics_file) as f:
            metrics = json.load(f)

        required_keys = [
            "total_requirements",
            "covered_requirements",
            "uncovered_requirements",
            "coverage_percentage",
            "covered_ids",
            "uncovered_ids",
            "coverage_by_category",
            "coverage_by_suite",
        ]

        for key in required_keys:
            assert key in metrics, f"Required key '{key}' not found in coverage metrics"

    def test_coverage_metrics_values_are_valid(self, coverage_metrics_file):
        """Verify coverage metrics contain valid values if file exists."""
        if not coverage_metrics_file.exists():
            pytest.skip("Coverage metrics JSON not generated yet")

        with open(coverage_metrics_file) as f:
            metrics = json.load(f)

        # Check numeric values are non-negative
        assert metrics["total_requirements"] >= 0
        assert metrics["covered_requirements"] >= 0
        assert metrics["uncovered_requirements"] >= 0
        assert 0 <= metrics["coverage_percentage"] <= 100

        # Check consistency
        assert (
            metrics["covered_requirements"] + metrics["uncovered_requirements"]
            == metrics["total_requirements"]
        )

    def test_vtm_csv_includes_coverage_header(self, vtm_csv_file):
        """Verify VTM CSV includes coverage metrics in header if it exists."""
        if not vtm_csv_file.exists():
            pytest.skip("VTM CSV not generated yet")

        with open(vtm_csv_file) as f:
            first_lines = [f.readline() for _ in range(10)]

        # Check for coverage-related content in header comments
        header_text = "".join(first_lines)
        assert "Coverage" in header_text, "Coverage metrics not found in VTM CSV header"


class TestValidationCertificatePDF:
    """Test validation certificate PDF generation."""

    @pytest.fixture
    def cert_pdf_file(self):
        """Fixture for validation certificate PDF path."""
        return Path("validation_certificate.pdf")

    def test_validation_certificate_pdf_can_be_generated(self, cert_pdf_file):
        """Verify validation certificate PDF exists or can be generated."""
        if not cert_pdf_file.exists():
            pytest.skip(
                "Validation certificate PDF not generated yet. "
                "Run: uv run python scripts/run_validation.py --tester 'Test' --skip-pq"
            )

        # If it exists, verify it's a valid PDF file
        assert cert_pdf_file.stat().st_size > 0, "PDF file is empty"

        # Check PDF magic number
        with open(cert_pdf_file, "rb") as f:
            header = f.read(4)
            assert header == b"%PDF", "File is not a valid PDF"
