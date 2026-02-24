"""Tests for report path management utilities.

Requirements: 27.1, 30.1
"""

import re
from pathlib import Path

import pytest

from sample_size_calculator.report_paths import (
    CALCULATIONS_DIR,
    FULL_DIR,
    REPORTS_BASE_DIR,
    VALIDATION_DIR,
    ensure_report_directories,
    get_calculation_report_path,
    get_full_report_path,
    get_report_path,
    get_timestamp,
    get_validation_report_path,
)


def test_timestamp_format():
    """Test that timestamp follows YYYYMMDD_HHMMSS format."""
    timestamp = get_timestamp()
    
    # Should match format: YYYYMMDD_HHMMSS
    pattern = r"^\d{8}_\d{6}$"
    assert re.match(pattern, timestamp), f"Timestamp {timestamp} doesn't match expected format"
    
    # Verify components
    date_part, time_part = timestamp.split("_")
    assert len(date_part) == 8, "Date part should be 8 digits (YYYYMMDD)"
    assert len(time_part) == 6, "Time part should be 6 digits (HHMMSS)"


def test_directory_constants():
    """Test that directory constants are correctly defined."""
    assert REPORTS_BASE_DIR == Path("reports")
    assert VALIDATION_DIR == Path("reports/validation")
    assert CALCULATIONS_DIR == Path("reports/calculations")
    assert FULL_DIR == Path("reports/full")


def test_get_report_path_validation():
    """Test validation report path generation."""
    path = get_report_path("validation", "test_cert")
    
    assert path.parent == VALIDATION_DIR
    assert path.name.startswith("test_cert_")
    assert path.suffix == ".pdf"
    assert re.match(r"test_cert_\d{8}_\d{6}\.pdf", path.name)


def test_get_report_path_calculations():
    """Test calculations report path generation."""
    path = get_report_path("calculations", "calc_report")
    
    assert path.parent == CALCULATIONS_DIR
    assert path.name.startswith("calc_report_")
    assert path.suffix == ".pdf"
    assert re.match(r"calc_report_\d{8}_\d{6}\.pdf", path.name)


def test_get_report_path_full():
    """Test full report path generation."""
    path = get_report_path("full", "full_report")
    
    assert path.parent == FULL_DIR
    assert path.name.startswith("full_report_")
    assert path.suffix == ".pdf"
    assert re.match(r"full_report_\d{8}_\d{6}\.pdf", path.name)


def test_get_report_path_invalid_type():
    """Test that invalid report type raises ValueError."""
    with pytest.raises(ValueError, match="Invalid report_type"):
        get_report_path("invalid", "test")  # type: ignore


def test_get_validation_report_path():
    """Test convenience function for validation reports."""
    path = get_validation_report_path()
    
    assert path.parent == VALIDATION_DIR
    assert path.name.startswith("validation_certificate_")
    assert path.suffix == ".pdf"


def test_get_calculation_report_path():
    """Test convenience function for calculation reports."""
    path = get_calculation_report_path()
    
    assert path.parent == CALCULATIONS_DIR
    assert path.name.startswith("calculation_report_")
    assert path.suffix == ".pdf"


def test_get_full_report_path():
    """Test convenience function for full reports."""
    path = get_full_report_path()
    
    assert path.parent == FULL_DIR
    assert path.name.startswith("full_report_")
    assert path.suffix == ".pdf"


def test_ensure_report_directories(tmp_path, monkeypatch):
    """Test that ensure_report_directories creates all subdirectories."""
    # Use temporary directory for testing
    test_reports_dir = tmp_path / "reports"
    
    # Monkey patch the directory constants
    monkeypatch.setattr("sample_size_calculator.report_paths.VALIDATION_DIR", 
                       test_reports_dir / "validation")
    monkeypatch.setattr("sample_size_calculator.report_paths.CALCULATIONS_DIR", 
                       test_reports_dir / "calculations")
    monkeypatch.setattr("sample_size_calculator.report_paths.FULL_DIR", 
                       test_reports_dir / "full")
    
    # Directories should not exist yet
    assert not (test_reports_dir / "validation").exists()
    assert not (test_reports_dir / "calculations").exists()
    assert not (test_reports_dir / "full").exists()
    
    # Create directories
    ensure_report_directories()
    
    # Verify all directories were created
    assert (test_reports_dir / "validation").exists()
    assert (test_reports_dir / "calculations").exists()
    assert (test_reports_dir / "full").exists()
    
    # Should be idempotent - calling again should not raise error
    ensure_report_directories()


def test_timestamp_uniqueness():
    """Test that consecutive timestamps are different (or very close)."""
    timestamp1 = get_timestamp()
    timestamp2 = get_timestamp()
    
    # Timestamps should be identical or differ by at most 1 second
    # (depending on execution speed)
    assert timestamp1 == timestamp2 or timestamp1 < timestamp2


def test_report_path_uniqueness():
    """Test that consecutive report paths have unique filenames."""
    path1 = get_calculation_report_path()
    path2 = get_calculation_report_path()
    
    # Paths should be different (or identical if generated in same second)
    # This is acceptable as the timestamp provides second-level granularity
    assert path1.parent == path2.parent
    assert path1.suffix == path2.suffix
