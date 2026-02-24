"""Integration tests for full report generation.

This module tests the end-to-end full report generation and saving.
"""

import tempfile
from datetime import datetime
from pathlib import Path

from sample_size_calculator.full_report_generator import FullReportGenerator
from sample_size_calculator.models import CalculationReport
from sample_size_calculator.report_paths import (
    ensure_report_directories,
    get_full_report_path,
    save_report,
)


def test_full_report_end_to_end():
    """Test complete full report generation and saving workflow."""
    # Create test calculation report
    report_data = CalculationReport(
        timestamp=datetime.now().isoformat(),
        module="Module A",
        inputs={
            "confidence": 95.0,
            "reliability": 95.0,
            "allowable_failures": 0,
        },
        results={
            "sample_size": 59,
            "method": "Success Run Theorem",
        },
        engine_hash="abc123def456",
        validation_state=True,
        method_path="Success Run Theorem (c=0)",
    )

    session_id = "integration_test_session"

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

    # Test saving to temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        report_path = Path(temp_dir) / "full" / "test_full_report.pdf"
        saved_path = save_report(pdf_bytes, report_path)

        # Verify file was saved
        assert saved_path.exists()
        assert saved_path.stat().st_size > 0

        # Verify content matches
        saved_content = saved_path.read_bytes()
        assert saved_content == pdf_bytes


def test_ensure_report_directories():
    """Test that report directories are created correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Temporarily change the base directory
        import sample_size_calculator.report_paths as rp

        original_base = rp.REPORTS_BASE_DIR
        original_validation = rp.VALIDATION_DIR
        original_calculations = rp.CALCULATIONS_DIR
        original_full = rp.FULL_DIR

        try:
            # Set temporary paths
            rp.REPORTS_BASE_DIR = Path(temp_dir) / "reports"
            rp.VALIDATION_DIR = rp.REPORTS_BASE_DIR / "validation"
            rp.CALCULATIONS_DIR = rp.REPORTS_BASE_DIR / "calculations"
            rp.FULL_DIR = rp.REPORTS_BASE_DIR / "full"

            # Ensure directories
            ensure_report_directories()

            # Verify all directories exist
            assert rp.VALIDATION_DIR.exists()
            assert rp.CALCULATIONS_DIR.exists()
            assert rp.FULL_DIR.exists()

        finally:
            # Restore original paths
            rp.REPORTS_BASE_DIR = original_base
            rp.VALIDATION_DIR = original_validation
            rp.CALCULATIONS_DIR = original_calculations
            rp.FULL_DIR = original_full


def test_get_full_report_path_format():
    """Test that full report path has correct format."""
    report_path = get_full_report_path()

    # Verify path structure
    assert "reports/full" in str(report_path)
    assert report_path.name.startswith("full_report_")
    assert report_path.suffix == ".pdf"

    # Verify timestamp format (YYYYMMDD_HHMMSS)
    filename = report_path.stem  # Remove .pdf extension
    parts = filename.split("_")
    assert len(parts) >= 3  # full, report, YYYYMMDD, HHMMSS
    
    # Check date part (YYYYMMDD)
    date_part = parts[2]
    assert len(date_part) == 8
    assert date_part.isdigit()
    
    # Check time part (HHMMSS)
    time_part = parts[3]
    assert len(time_part) == 6
    assert time_part.isdigit()
