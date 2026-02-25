"""Integration tests for reports directory structure.

Tests that the reports directory structure is properly set up with correct
permissions for report generation.

Requirements: 27.1, 30.1
"""


import pytest

from sample_size_calculator.report_paths import (
    CALCULATIONS_DIR,
    FULL_DIR,
    REPORTS_BASE_DIR,
    VALIDATION_DIR,
    ensure_report_directories,
    get_calculation_report_path,
    get_full_report_path,
    get_validation_report_path,
)


def test_reports_base_directory_exists():
    """Test that the base reports directory exists."""
    assert REPORTS_BASE_DIR.exists(), "Reports base directory should exist"
    assert REPORTS_BASE_DIR.is_dir(), "Reports base should be a directory"


def test_subdirectories_exist():
    """Test that all required subdirectories exist."""
    # Ensure directories are created
    ensure_report_directories()
    
    assert VALIDATION_DIR.exists(), "Validation directory should exist"
    assert VALIDATION_DIR.is_dir(), "Validation should be a directory"
    
    assert CALCULATIONS_DIR.exists(), "Calculations directory should exist"
    assert CALCULATIONS_DIR.is_dir(), "Calculations should be a directory"
    
    assert FULL_DIR.exists(), "Full reports directory should exist"
    assert FULL_DIR.is_dir(), "Full should be a directory"


def test_directory_write_permissions():
    """Test that all subdirectories have write permissions."""
    ensure_report_directories()
    
    # Test write permission by creating a temporary file in each directory
    test_dirs = [VALIDATION_DIR, CALCULATIONS_DIR, FULL_DIR]
    
    for test_dir in test_dirs:
        test_file = test_dir / "test_write_permission.tmp"
        
        try:
            # Attempt to write a test file
            test_file.write_text("test")
            assert test_file.exists(), f"Should be able to write to {test_dir}"
            
            # Clean up
            test_file.unlink()
        except PermissionError:
            pytest.fail(f"No write permission for {test_dir}")


def test_report_path_generation_creates_valid_paths():
    """Test that generated report paths are valid and writable."""
    ensure_report_directories()
    
    # Generate paths
    validation_path = get_validation_report_path()
    calculation_path = get_calculation_report_path()
    full_path = get_full_report_path()
    
    # Verify paths are in correct directories
    assert validation_path.parent == VALIDATION_DIR
    assert calculation_path.parent == CALCULATIONS_DIR
    assert full_path.parent == FULL_DIR
    
    # Verify parent directories exist
    assert validation_path.parent.exists()
    assert calculation_path.parent.exists()
    assert full_path.parent.exists()


def test_readme_exists():
    """Test that README.md exists in reports directory."""
    readme_path = REPORTS_BASE_DIR / "README.md"
    assert readme_path.exists(), "README.md should exist in reports directory"
    
    # Verify it contains expected content
    content = readme_path.read_text()
    assert "validation/" in content
    assert "calculations/" in content
    assert "full/" in content
    assert "timestamp" in content.lower()


def test_gitkeep_files_exist():
    """Test that .gitkeep files exist in all subdirectories."""
    ensure_report_directories()
    
    assert (VALIDATION_DIR / ".gitkeep").exists(), "validation/.gitkeep should exist"
    assert (CALCULATIONS_DIR / ".gitkeep").exists(), "calculations/.gitkeep should exist"
    assert (FULL_DIR / ".gitkeep").exists(), "full/.gitkeep should exist"


def test_directory_structure_matches_requirements():
    """Test that directory structure matches requirements 27.1 and 30.1."""
    ensure_report_directories()
    
    # Requirement 27.1: User calculation reports
    assert CALCULATIONS_DIR.exists(), "Calculations directory required for Req 27.1"
    
    # Requirement 30.1: Validation certificates
    assert VALIDATION_DIR.exists(), "Validation directory required for Req 30.1"
    
    # Full reports for comprehensive documentation
    assert FULL_DIR.exists(), "Full reports directory should exist"


def test_ensure_report_directories_is_idempotent():
    """Test that calling ensure_report_directories multiple times is safe."""
    # Call multiple times
    ensure_report_directories()
    ensure_report_directories()
    ensure_report_directories()
    
    # Should still have all directories
    assert VALIDATION_DIR.exists()
    assert CALCULATIONS_DIR.exists()
    assert FULL_DIR.exists()
