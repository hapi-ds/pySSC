"""Installation Qualification (IQ) Tests.

This module contains tests that verify the correct installation of the Sample Size
Calculator application, including dependency verification and version checking.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.iq
@pytest.mark.urs("31.2")
def test_uv_lock_exists_and_valid():
    """Verify uv.lock file exists and has correct format.
    
    URS 31.2: THE System SHALL maintain a uv.lock file with hash-based 
    dependency locking.
    """
    lock_file = Path("uv.lock")
    assert lock_file.exists(), "uv.lock file must exist"
    
    # Verify file is not empty
    assert lock_file.stat().st_size > 0, "uv.lock file must not be empty"
    
    # Verify file contains expected sections
    content = lock_file.read_text()
    assert "[[package]]" in content, "uv.lock must contain package definitions"


@pytest.mark.iq
@pytest.mark.urs("31.3")
def test_uv_sync_installs_without_conflicts():
    """Verify uv sync installs dependencies without conflicts.
    
    URS 31.3: WHEN running uv sync, THE System SHALL install dependencies 
    without conflicts.
    """
    result = subprocess.run(
        ["uv", "sync", "--frozen"],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    assert result.returncode == 0, (
        f"uv sync failed with return code {result.returncode}\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )
    
    # Verify no conflict messages in output
    output = result.stdout + result.stderr
    assert "conflict" not in output.lower(), "Dependency conflicts detected"
    assert "error" not in output.lower(), "Errors detected during sync"


@pytest.mark.iq
@pytest.mark.urs("31.4")
def test_scipy_version():
    """Verify scipy version 1.x.x is installed.
    
    URS 31.4: THE Validation_Suite SHALL verify that scipy version 1.x.x 
    is installed.
    """
    import scipy
    
    version = scipy.__version__
    major_version = int(version.split('.')[0])
    
    assert major_version >= 1, (
        f"scipy version must be 1.x.x or higher, found {version}"
    )


@pytest.mark.iq
@pytest.mark.urs("31.5")
def test_required_dependencies_present():
    """Verify all required dependencies are present.
    
    URS 31.5: THE Validation_Suite SHALL verify that all required 
    dependencies are present.
    """
    required_packages = [
        "nicegui",
        "pydantic",
        "reportlab",
        "numpy",
        "hypothesis",
        "pytest",
        "playwright",
        "scipy",
        "pandas",
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    assert not missing_packages, (
        f"Missing required packages: {', '.join(missing_packages)}"
    )


@pytest.mark.iq
@pytest.mark.urs("31.5")
def test_python_version():
    """Verify Python version meets requirements.
    
    URS 31.5: THE Validation_Suite SHALL verify that all required 
    dependencies are present (including Python version).
    """
    version_info = sys.version_info
    
    assert version_info.major == 3, "Python 3.x required"
    assert version_info.minor >= 11, (
        f"Python 3.11 or higher required, found {version_info.major}.{version_info.minor}"
    )


@pytest.mark.iq
@pytest.mark.urs("31.2")
def test_project_structure():
    """Verify required project directories and files exist.
    
    URS 31.2: THE System SHALL maintain proper project structure.
    """
    required_paths = [
        Path("src/sample_size_calculator"),
        Path("tests"),
        Path("logs"),
        Path("pyproject.toml"),
        Path("uv.lock"),
    ]
    
    missing_paths = [p for p in required_paths if not p.exists()]
    
    assert not missing_paths, (
        f"Missing required paths: {', '.join(str(p) for p in missing_paths)}"
    )


@pytest.mark.iq
@pytest.mark.urs("32.2")
def test_pytest_markers_configured():
    """Verify pytest markers are properly configured.
    
    URS 32.2: THE Validation_Suite SHALL use pytest markers linking each 
    test to specific URS IDs.
    """
    # Read pyproject.toml to verify markers are configured
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml must exist"
    
    content = pyproject_path.read_text()
    
    # Verify IQ/OQ/PQ markers are defined
    assert 'markers = [' in content, "pytest markers section must exist"
    assert '"iq:' in content, "IQ marker must be defined"
    assert '"oq:' in content, "OQ marker must be defined"
    assert '"pq:' in content, "PQ marker must be defined"
    assert '"urs(' in content or '"urs:' in content, "URS marker must be defined"
