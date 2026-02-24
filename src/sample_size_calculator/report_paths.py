"""Report path management utilities.

This module provides utilities for managing report file paths with timestamp-based
naming conventions. It ensures consistent naming across all report types and handles
directory structure for the reports system.

Requirements: 27.1, 30.1
"""

from datetime import datetime
from pathlib import Path
from typing import Literal

# Base reports directory
REPORTS_BASE_DIR = Path("reports")

# Subdirectories for different report types
VALIDATION_DIR = REPORTS_BASE_DIR / "validation"
CALCULATIONS_DIR = REPORTS_BASE_DIR / "calculations"
FULL_DIR = REPORTS_BASE_DIR / "full"

ReportType = Literal["validation", "calculations", "full"]


def get_timestamp() -> str:
    """Generate timestamp string for report filenames.
    
    Returns:
        Timestamp in format YYYYMMDD_HHMMSS (e.g., "20240315_143022")
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_report_path(report_type: ReportType, prefix: str = "report") -> Path:
    """Generate a timestamped report file path.
    
    Args:
        report_type: Type of report ("validation", "calculations", or "full")
        prefix: Filename prefix (default: "report")
        
    Returns:
        Path object for the report file with timestamp-based naming
        
    Examples:
        >>> get_report_path("validation", "validation_certificate")
        Path('reports/validation/validation_certificate_20240315_143022.pdf')
        
        >>> get_report_path("calculations", "calculation_report")
        Path('reports/calculations/calculation_report_20240315_143022.pdf')
    """
    timestamp = get_timestamp()
    filename = f"{prefix}_{timestamp}.pdf"
    
    if report_type == "validation":
        return VALIDATION_DIR / filename
    elif report_type == "calculations":
        return CALCULATIONS_DIR / filename
    elif report_type == "full":
        return FULL_DIR / filename
    else:
        raise ValueError(f"Invalid report_type: {report_type}")


def ensure_report_directories() -> None:
    """Ensure all report subdirectories exist with proper permissions.
    
    Creates the reports directory structure if it doesn't exist:
    - reports/validation/
    - reports/calculations/
    - reports/full/
    
    This function is idempotent and safe to call multiple times.
    """
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    CALCULATIONS_DIR.mkdir(parents=True, exist_ok=True)
    FULL_DIR.mkdir(parents=True, exist_ok=True)


def get_validation_report_path() -> Path:
    """Get path for a new validation certificate report.
    
    Returns:
        Path for validation certificate with timestamp
        
    Example:
        Path('reports/validation/validation_certificate_20240315_143022.pdf')
    """
    return get_report_path("validation", "validation_certificate")


def get_calculation_report_path() -> Path:
    """Get path for a new calculation report.
    
    Returns:
        Path for calculation report with timestamp
        
    Example:
        Path('reports/calculations/calculation_report_20240315_143022.pdf')
    """
    return get_report_path("calculations", "calculation_report")


def get_full_report_path() -> Path:
    """Get path for a new comprehensive full report.
    
    Returns:
        Path for full report with timestamp
        
    Example:
        Path('reports/full/full_report_20240315_143022.pdf')
    """
    return get_report_path("full", "full_report")
