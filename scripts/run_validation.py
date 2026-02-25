#!/usr/bin/env python3
"""Validation Suite Runner.

This script runs the complete IQ/OQ/PQ validation suite, collects test results,
generates a Verification Traceability Matrix (VTM), creates a validation certificate
PDF, and stores the validated hash.

Usage:
    uv run python scripts/run_validation.py --tester "John Doe"
"""

import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ruff: noqa: E402

# Add project root to Python path to enable imports from scripts directory
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sample_size_calculator.hash_verifier import HashVerifier
from sample_size_calculator.models import ValidationCertificate
from sample_size_calculator.report_generator import ReportGenerator
from sample_size_calculator.vtm_generator import VTMGenerator
from scripts.calculate_coverage import calculate_coverage, print_coverage_report


def run_test_suite(test_path: str, marker: str) -> dict:
    """Run a specific test suite and return results.
    Args:
        test_path: Path to test file or directory
        marker: Pytest marker to filter tests (iq, oq, pq)
    Returns:
        Dictionary with test results
    """
    print(f"\n{'=' * 60}")
    print(f"Running {marker.upper()} Tests: {test_path}")
    print(f"{'=' * 60}\n")

    # Run pytest with JSON report
    result = subprocess.run(
        [
            "uv",
            "run",
            "pytest",
            test_path,
            "-m",
            marker,
            "-v",
            "--tb=short",
            "--json-report",
            f"--json-report-file=test_results_{marker}.json",
        ],
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    # Load JSON report
    json_path = Path(f"test_results_{marker}.json")
    if json_path.exists():
        with open(json_path) as f:
            return json.load(f)
    else:
        # Fallback if JSON report not available
        return {
            "tests": [],
            "summary": {"passed": 0, "failed": 0, "total": 0},
            "exitcode": result.returncode,
        }


def extract_test_results(pytest_data: dict, suite_name: str) -> list[dict]:
    """Extract test results from pytest JSON data.

    Args:
        pytest_data: Pytest JSON report data
        suite_name: Name of test suite (IQ, OQ, PQ)

    Returns:
        List of test result dictionaries
    """
    test_results = []

    for test in pytest_data.get("tests", []):
        # Get test outcome
        outcome = test.get("outcome", "unknown")
        result = "PASSED" if outcome == "passed" else "FAILED"

        # Get test ID
        test_id = test.get("nodeid", "unknown")
        test_name = test_id.split("::")[-1] if "::" in test_id else test_id

        # Extract URS IDs by parsing the test file
        urs_ids = extract_urs_from_test_file(test_id)

        # Create entry for each URS ID
        if urs_ids:
            for urs_id in urs_ids:
                test_results.append(
                    {
                        "urs_id": urs_id,
                        "requirement": f"{suite_name} - {test_name}",
                        "test_id": test_id,
                        "result": result,
                        "status": result,
                    }
                )
        else:
            test_results.append(
                {
                    "urs_id": "N/A",
                    "requirement": f"{suite_name} - {test_name}",
                    "test_id": test_id,
                    "result": result,
                    "status": result,
                }
            )

    return test_results


def extract_urs_from_test_file(nodeid: str) -> list[str]:
    """Extract URS IDs from test source code.

    Args:
        nodeid: Pytest node ID (e.g., "tests/validation/test_iq.py::test_name")

    Returns:
        List of URS IDs found in the test decorators
    """
    import re

    # Parse nodeid to get file path and line number (if available)
    if "::" not in nodeid:
        return []

    parts = nodeid.split("::", 1)
    file_path = parts[0]
    test_name = parts[1] if len(parts) > 1 else ""

    try:
        with open(file_path) as f:
            lines = f.readlines()

        # Find the test function line by searching for def test_name(
        test_line_num = None
        for i, line in enumerate(lines):
            if f"def {test_name}(" in line:
                test_line_num = i + 1
                break

        if test_line_num is None:
            return []

        # Look backwards up to 10 lines from the test function for markers
        start_idx = max(0, test_line_num - 10)
        collected_urs_ids = []

        for j in range(test_line_num - 1, start_idx - 1, -1):
            line_content = lines[j]

            # Stop if we hit another function definition or class
            if "def " in line_content and f"def {test_name}(" not in line_content:
                break

            # Pattern to match @pytest.mark.urs("URS-ID", ...)
            pattern = r"@pytest\.mark\.urs\((.*?)\)"
            matches = re.findall(pattern, line_content)

            for match in matches:
                urs_pattern = r'"([^"]+)"'
                found_ids = re.findall(urs_pattern, match)

                # Only add IDs that look like URS IDs
                for urs_id in found_ids:
                    if urs_id.startswith("URS-") and urs_id not in collected_urs_ids:
                        collected_urs_ids.append(urs_id)

        return collected_urs_ids if collected_urs_ids else []
    except Exception as e:
        print(f"Warning: Could not extract URS IDs from {file_path}: {e}")
        return []


def main():
    """Run validation suite and generate validation certificate."""
    parser = argparse.ArgumentParser(
        description="Run IQ/OQ/PQ validation suite and generate certificate"
    )
    parser.add_argument("--tester", required=True, help="Name of the validation tester")
    parser.add_argument(
        "--output", default="validation_certificate.pdf", help="Output PDF filename"
    )
    parser.add_argument(
        "--skip-pq",
        action="store_true",
        help="Skip PQ tests (requires running application)",
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("VALIDATION SUITE EXECUTION")
    print("=" * 60)
    print(f"Tester: {args.tester}")
    print(f"Date: {datetime.now().isoformat()}")
    print(f"Python: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print("=" * 60)

    # Run test suites
    all_test_results = []
    all_passed = True

    # Run IQ tests
    iq_data = run_test_suite("tests/validation/test_iq.py", "iq")
    iq_results = extract_test_results(iq_data, "IQ")
    all_test_results.extend(iq_results)

    if iq_data.get("exitcode", 1) != 0:
        all_passed = False
        print("\n❌ IQ Tests FAILED")
    else:
        print("\n✅ IQ Tests PASSED")

    # Run OQ tests
    oq_data = run_test_suite("tests/validation/test_oq.py", "oq")
    oq_results = extract_test_results(oq_data, "OQ")
    all_test_results.extend(oq_results)

    if oq_data.get("exitcode", 1) != 0:
        all_passed = False
        print("\n❌ OQ Tests FAILED")
    else:
        print("\n✅ OQ Tests PASSED")

    # Run PQ tests (optional, requires running app)
    if not args.skip_pq:
        print("\n⚠️  PQ tests require the application to be running.")
        print("Please ensure the app is running at http://localhost:8080")
        print("Press Enter to continue or Ctrl+C to skip PQ tests...")
        try:
            input()
        except KeyboardInterrupt:
            print("\nSkipping PQ tests")
            args.skip_pq = True

    if not args.skip_pq:
        pq_data = run_test_suite("tests/validation/test_pq.py", "pq")
        pq_results = extract_test_results(pq_data, "PQ")
        all_test_results.extend(pq_results)

        if pq_data.get("exitcode", 1) != 0:
            all_passed = False
            print("\n❌ PQ Tests FAILED")
        else:
            print("\n✅ PQ Tests PASSED")

    # Generate VTM
    print("\n" + "=" * 60)
    print("Generating Verification Traceability Matrix...")
    print("=" * 60)

    # Calculate URS coverage
    print("\n" + "=" * 60)
    print("Calculating URS Coverage...")
    print("=" * 60)

    coverage_metrics = calculate_coverage(
        urs_document_path="requirements/02_URS_SampleSizeCalculator.md",
        test_files=[
            "tests/validation/test_iq.py",
            "tests/validation/test_oq.py",
            "tests/validation/test_pq.py",
        ],
    )

    # Print coverage report to console
    print_coverage_report(coverage_metrics)

    # Save coverage metrics to JSON file for future reference
    coverage_json_path = Path("validation_coverage_metrics.json")
    with open(coverage_json_path, "w") as f:
        json.dump(coverage_metrics, f, indent=2)
    print(f"✅ Coverage metrics saved to: {coverage_json_path}")

    # Generate VTM with coverage metrics
    vtm = VTMGenerator.generate_vtm(all_test_results, coverage_metrics)

    # Export VTM to CSV with coverage metrics
    vtm_csv_path = Path("validation_traceability_matrix.csv")
    VTMGenerator.export_vtm_csv(vtm, vtm_csv_path, coverage_metrics)
    print(f"✅ VTM exported to: {vtm_csv_path}")

    # Display VTM summary
    print(f"\nTotal test cases: {len(vtm)}")
    print(f"Passed: {len(vtm[vtm['Result'] == 'PASSED'])}")
    print(f"Failed: {len(vtm[vtm['Result'] == 'FAILED'])}")

    # Get current engine hash
    engine_hash = HashVerifier.get_engine_hash()
    print(f"\nCurrent Engine Hash: {engine_hash}")

    # Generate validation certificate
    print("\n" + "=" * 60)
    print("Generating Validation Certificate...")
    print("=" * 60)

    cert_data = ValidationCertificate(
        test_date=datetime.now().isoformat(),
        tester_name=args.tester,
        system_info={
            "os": platform.system(),
            "platform": platform.platform(),
            "python_version": sys.version,
            "python_implementation": platform.python_implementation(),
        },
        test_results=all_test_results,
        validated_hash=engine_hash,
    )

    # Generate PDF and save to reports directory with coverage metrics
    pdf_bytes, report_path = ReportGenerator.generate_validation_certificate(
        cert_data, coverage_metrics
    )

    # Note: The report is already saved by the generator, but we also save to the specified output path
    output_path = Path(args.output)
    output_path.write_bytes(pdf_bytes)
    print(f"✅ Validation certificate saved to: {output_path}")
    print(f"✅ Also saved to reports directory: {report_path}")

    # Store validated hash if all tests passed
    if all_passed:
        print("\n" + "=" * 60)
        print("Storing Validated Hash...")
        print("=" * 60)

        HashVerifier.set_validated_hash(engine_hash)
        print(f"✅ Validated hash stored: {engine_hash}")
        print("\n🎉 VALIDATION COMPLETE - ALL TESTS PASSED")
    else:
        print("\n" + "=" * 60)
        print("⚠️  VALIDATION INCOMPLETE - SOME TESTS FAILED")
        print("=" * 60)
        print("Validated hash NOT stored due to test failures.")
        print("Please fix failing tests and re-run validation.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("VALIDATION ARTIFACTS")
    print("=" * 60)
    print(f"- Validation Certificate: {output_path}")
    print(f"- VTM CSV: {vtm_csv_path}")
    print("- Validated Hash: config/validated_hash.json")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
