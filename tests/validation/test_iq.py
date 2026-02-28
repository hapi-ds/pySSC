"""Installation Qualification (IQ) Tests.

This module contains tests that verify the correct installation of the Sample Size
Calculator application, including dependency verification and version checking.
"""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.iq
@pytest.mark.urs("URS-IQ-01")
def test_uv_lock_exists_and_valid():
    """Verify uv.lock file exists and has correct format.

    URS-IQ-01: Dependencies must be strictly version-locked using a
    hash-based lockfile.

    SRS (requirements.md) 31.2: THE System SHALL maintain a uv.lock file with hash-based
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
@pytest.mark.urs("URS-IQ-01")
def test_uv_sync_installs_without_conflicts():
    """Verify uv sync installs dependencies without conflicts.

    URS-IQ-01: Dependencies must be strictly version-locked using a
    hash-based lockfile.

    SRS (requirements.md) 31.3: WHEN running uv sync, THE System SHALL install dependencies
    without conflicts.
    """
    result = subprocess.run(
        ["uv", "sync", "--frozen"], capture_output=True, text=True, timeout=120
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
@pytest.mark.urs("URS-IQ-01")
def test_scipy_version():
    """Verify scipy version 1.x.x is installed.

    URS-IQ-01: Dependencies must be strictly version-locked using a
    hash-based lockfile.

    SRS (requirements.md) 31.4: THE Validation_Suite SHALL verify that scipy version 1.x.x
    is installed.
    """
    import scipy

    version = scipy.__version__
    major_version = int(version.split(".")[0])

    assert major_version >= 1, f"scipy version must be 1.x.x or higher, found {version}"


@pytest.mark.iq
@pytest.mark.urs("URS-IQ-01")
def test_required_dependencies_present():
    """Verify all required dependencies are present.

    URS-IQ-01: Dependencies must be strictly version-locked using a
    hash-based lockfile.

    SRS (requirements.md) 31.5: THE Validation_Suite SHALL verify that all required
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
@pytest.mark.urs("URS-IQ-01")
def test_python_version():
    """Verify Python version meets requirements.

    URS-IQ-01: Dependencies must be strictly version-locked using a
    hash-based lockfile.

    SRS (requirements.md) 31.5: THE Validation_Suite SHALL verify that all required
    dependencies are present (including Python version).
    """
    version_info = sys.version_info

    assert version_info.major == 3, "Python 3.x required"
    assert version_info.minor >= 11, (
        f"Python 3.11 or higher required, found {version_info.major}.{version_info.minor}"
    )


@pytest.mark.iq
@pytest.mark.urs("URS-IQ-01")
def test_project_structure():
    """Verify required project directories and files exist.

    URS-IQ-01: Dependencies must be strictly version-locked using a
    hash-based lockfile.

    SRS (requirements.md) 31.2: THE System SHALL maintain proper project structure.
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
@pytest.mark.urs("URS-IQ-01")
def test_pytest_markers_configured():
    """Verify pytest markers are properly configured.

    URS-IQ-01: Dependencies must be strictly version-locked using a
    hash-based lockfile.

    SRS (requirements.md) 32.2: THE Validation_Suite SHALL use pytest markers linking each
    test to specific URS IDs.
    """
    # Read pyproject.toml to verify markers are configured
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml must exist"

    content = pyproject_path.read_text()

    # Verify IQ/OQ/PQ markers are defined
    assert "markers = [" in content, "pytest markers section must exist"
    assert '"iq:' in content, "IQ marker must be defined"
    assert '"oq:' in content, "OQ marker must be defined"
    assert '"pq:' in content, "PQ marker must be defined"
    assert '"urs(' in content or '"urs:' in content, "URS marker must be defined"


@pytest.mark.iq
@pytest.mark.urs("URS-REP-02")
def test_hash_verifier_module_present():
    """Verify hash verification module is present and importable.

    URS-REP-02: Validation State Reference: The User Calculation Report must
    display the SHA-256 Hash of the current calculation engine file
    (calculations.py).
    """
    from sample_size_calculator.hash_verifier import (
        HashVerifier,
        get_engine_hash,
        get_validated_hash,
        is_validated_state,
        set_validated_hash,
    )

    assert callable(get_engine_hash), "get_engine_hash should be callable"
    assert callable(get_validated_hash), "get_validated_hash should be callable"
    assert callable(set_validated_hash), "set_validated_hash should be callable"
    assert callable(is_validated_state), "is_validated_state should be callable"


@pytest.mark.iq
@pytest.mark.urs("URS-REP-02")
def test_engine_hash_calculation():
    """Test that engine hash is calculated correctly.

    URS-REP-02: Validation State Reference: The User Calculation Report must
    display the SHA-256 Hash of the current calculation engine file
    (calculations.py).
    """
    from sample_size_calculator.hash_verifier import get_engine_hash

    hash_result = get_engine_hash()

    assert isinstance(hash_result, str), "Hash should be a string"
    assert len(hash_result) == 64, "SHA-256 hash should be 64 characters"
    assert all(c in "0123456789abcdef" for c in hash_result), (
        "Hash should contain only hexadecimal characters"
    )


@pytest.mark.iq
@pytest.mark.urs("URS-REP-02")
def test_hash_idempotence():
    """Test that hash calculation is idempotent.

    URS-REP-02: Validation State Reference: The User Calculation Report must
    display the SHA-256 Hash of the current calculation engine file
    (calculations.py).
    """
    from sample_size_calculator.hash_verifier import get_engine_hash

    results = [get_engine_hash() for _ in range(5)]

    assert all(r == results[0] for r in results), "Hash calculation must be idempotent"


@pytest.mark.iq
@pytest.mark.urs("URS-REP-01")
def test_report_generator_module_present():
    """Verify report generator module is present and importable.

    URS-REP-01: User Calculation Report: The system shall generate
    a downloadable PDF report summarizing the current session.

    """
    from sample_size_calculator.report_generator import (
        CalculationReport,
        ReportGenerator,
        ValidationCertificate,
    )

    assert callable(CalculationReport), "CalculationReport should be a class"
    assert callable(ValidationCertificate), "ValidationCertificate should be a class"


@pytest.mark.iq
@pytest.mark.urs("URS-VTM-01")
def test_vtm_generator_module_present():
    """Verify VTM generator module is present and importable.

    URS-VTM-01: The VTM must include the URS ID AND corresponding text

    """
    from sample_size_calculator.vtm_generator import (
        VTMGenerator,
    )

    assert callable(VTMGenerator), "VTMGenerator should be a class"
    assert callable(VTMGenerator.generate_vtm), "generate_vtm should be callable"


@pytest.mark.iq
@pytest.mark.urs("URS-IQ-01")
def test_all_validation_modules_importable():
    """Test that all validation framework modules are importable.

    URS-IQ-01: Dependencies must be strictly version-locked using a
    hash-based lockfile.
    """
    required_modules = [
        "sample_size_calculator.calculations",
        "sample_size_calculator.models",
        "sample_size_calculator.transformations",
        "sample_size_calculator.tolerance",
        "sample_size_calculator.normality",
        "sample_size_calculator.outliers",
        "sample_size_calculator.hash_verifier",
        "sample_size_calculator.audit_logger",
        "sample_size_calculator.validation_runner",
        "sample_size_calculator.report_generator",
        "sample_size_calculator.vtm_generator",
    ]

    missing_modules = []

    for module in required_modules:
        try:
            __import__(module)
        except ImportError as e:
            missing_modules.append(f"{module}: {e}")

    assert not missing_modules, f"Missing required validation modules:\n" + "\n".join(
        missing_modules
    )


# ============================================================================
# URS-VTM Tests (Verification Traceability Matrix) - IQ
# ============================================================================


@pytest.mark.iq
@pytest.mark.urs("URS-VTM-01", "URS-VTM-02", "URS-VTM-03")
def test_vtm_structure_requirements():
    """Test that VTM meets URS-VTM-01, URS-VTM-02, and URS-VTM-03 requirements.

    URS-VTM-01: The VTM must include the URS ID AND corresponding text
    URS-VTM-02: The VTM must include the test id
    URS-VTM-03: The VTM must include the test result

    SRS 28.1: THE Verification_Traceability_Matrix SHALL include the URS_ID field
    SRS 28.2: THE Verification_Traceability_Matrix SHALL include the Requirement text
    SRS 28.3: THE Verification_Traceability_Matrix SHALL include the Test_ID field
    SRS 28.4: THE Verification_Traceability_Matrix SHALL include the Result field
    """
    from sample_size_calculator.vtm_generator import VTMGenerator

    # Create test results with required fields
    test_results = [
        {
            "urs_id": "URS-IQ-01",
            "requirement": "Installation Qualification (IQ): Dependencies must be strictly version-locked using a hash-based lockfile.",
            "test_id": "tests/validation/test_iq.py::test_uv_lock_exists_and_valid",
            "result": "PASSED",
        },
        {
            "urs_id": "URS-VTM-02",
            "requirement": "The VTM must include the test id",
            "test_id": "tests/validation/test_iq.py::test_vtm_structure_requirements",
            "result": "PASSED",
        },
    ]

    # Generate VTM
    vtm = VTMGenerator.generate_vtm(test_results, {})

    # Verify required columns exist
    required_columns = ["URS_ID", "Requirement", "Test_ID", "Result"]
    for col in required_columns:
        assert col in vtm.columns, f"VTM must contain column: {col}"

    # Verify URS IDs are present
    urs_ids = vtm["URS_ID"].tolist()
    assert "URS-IQ-01" in urs_ids, "VTM must include URS-IQ-01"
    assert "URS-VTM-02" in urs_ids, "VTM must include URS-VTM-02"

    # Verify Test_IDs are present
    test_ids = vtm["Test_ID"].tolist()
    assert "tests/validation/test_iq.py::test_uv_lock_exists_and_valid" in test_ids, (
        "VTM must include test IDs"
    )
    assert "tests/validation/test_iq.py::test_vtm_structure_requirements" in test_ids, (
        "VTM must include this test's ID"
    )

    # Verify Results are present
    results = vtm["Result"].tolist()
    assert "PASSED" in results, "VTM must include test results"
