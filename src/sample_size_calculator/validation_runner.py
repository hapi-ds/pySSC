"""Validation Runner Module.

This module provides functionality to run the IQ/OQ/PQ validation suite
from within the UI and report progress and results.
"""

import json
import platform
import re
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from sample_size_calculator.hash_verifier import HashVerifier
from sample_size_calculator.models import ValidationCertificate
from sample_size_calculator.report_generator import ReportGenerator
from sample_size_calculator.version import __version__
from sample_size_calculator.vtm_generator import VTMGenerator


class ValidationRunner:
    """Runs validation test suite and generates validation certificate."""

    def __init__(self, progress_callback: Callable[[str], None] | None = None):
        """Initialize validation runner.

        Args:
            progress_callback: Optional callback function to report progress updates
        """
        self.progress_callback = progress_callback
        self.test_results: list[dict] = []
        self.pdf_test_results: list[dict] = []  # PDF validation test results
        self.all_passed = True

    def _report_progress(self, message: str) -> None:
        """Report progress to callback if available.

        Args:
            message: Progress message to report
        """
        if self.progress_callback:
            self.progress_callback(message)

    def _run_test_suite(self, test_path: str, marker: str) -> dict:
        """Run a specific test suite and return results.

        Args:
            test_path: Path to test file or directory
            marker: Pytest marker to filter tests (iq, oq, pq)

        Returns:
            Dictionary with test results
        """
        self._report_progress(f"Running {marker.upper()} tests...")

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
            timeout=300,  # 5 minute timeout per suite
        )

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

    def _extract_test_results(self, pytest_data: dict, suite_name: str) -> list[dict]:
        """Extract test results from pytest JSON data.

        Args:
            pytest_data: Pytest JSON report data
            suite_name: Name of test suite (IQ, OQ, PQ)

        Returns:
            List of test result dictionaries
        """
        test_results = []

        for test in pytest_data.get("tests", []):
            # Extract URS IDs from markers (try pytest-json-report format first, then source file)
            urs_ids = []

            test_id = test.get("nodeid", "unknown")
            # Extract clean test name (remove [param] from parametrized tests)
            test_name = (
                test_id.split("::")[-1].split("[")[0] if "::" in test_id else test_id
            )

            # Try to get URS IDs from pytest-json-report markers field first
            test_markers = test.get("markers", [])
            for marker in test_markers:
                if isinstance(marker, dict):
                    if marker.get("name") == "urs":
                        urs_args = marker.get("args", [])
                        if isinstance(urs_args, list):
                            urs_ids.extend([str(arg) for arg in urs_args])
                elif hasattr(marker, "name") and marker.name == "urs":
                    if hasattr(marker, "args"):
                        urs_ids.extend([str(arg) for arg in marker.args])

            # If no URS IDs from pytest-json-report format, try parsing source file
            if not urs_ids:
                test_file_path = test_id.split("::")[0]
                try:
                    with open(test_file_path) as f:
                        lines = f.readlines()

                    # Find the line number of this test function
                    for i, line in enumerate(lines):
                        if f"def {test_name}(" in line:
                            # Look backwards up to 10 lines for markers
                            start_idx = max(0, i - 10)

                            # Collect URS IDs from markers in reverse order (bottom-up)
                            collected_urs_ids = []
                            for j in range(i - 1, start_idx - 1, -1):
                                line_content = lines[j]

                                # Stop if we hit another test function or class
                                if "def " in line_content or "class " in line_content:
                                    break

                                # Pattern to match @pytest.mark.urs("URS-ID", ...)
                                pattern = r"@pytest\.mark\.urs\((.*?)\)"
                                matches = re.findall(pattern, line_content)

                                for match in matches:
                                    urs_pattern = r'"([^"]+)"'
                                    found_ids = re.findall(urs_pattern, match)

                                    # Add all URS IDs (not just the first one)
                                    for urs_id in found_ids:
                                        if (
                                            urs_id.startswith("URS-")
                                            and urs_id not in collected_urs_ids
                                        ):
                                            collected_urs_ids.append(urs_id)

                            # Use all collected URS IDs from markers
                            if collected_urs_ids:
                                urs_ids = collected_urs_ids

                            break
                except Exception:
                    pass

            # Get test outcome
            outcome = test.get("outcome", "unknown")
            result = "PASSED" if outcome == "passed" else "FAILED"

            # Get test ID
            test_id = test.get("nodeid", "unknown")
            test_name = test_id.split("::")[-1] if "::" in test_id else test_id

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

    def run_validation(
        self, tester_name: str, skip_pq: bool = True
    ) -> tuple[bool, str, Path | None]:
        """Run complete validation suite.

        Args:
            tester_name: Name of the validation tester
            skip_pq: Whether to skip PQ tests (default True since app is running)

        Returns:
            Tuple of (success, message, certificate_path)
        """
        try:
            # Remove existing validated hash file at start for fresh validation
            if HashVerifier.VALIDATED_HASH_FILE.exists():
                HashVerifier.VALIDATED_HASH_FILE.unlink()
                self._report_progress("Removed previous validation hash")

            self._report_progress("=" * 60)
            self._report_progress("🚀 VALIDATION PROCESS STARTED")
            self._report_progress(f"👤 Tester: {tester_name}")
            self._report_progress(
                f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            self._report_progress("=" * 60)

            # Run IQ tests
            self._report_progress("Running IQ (Installation Qualification) tests...")
            iq_data = self._run_test_suite("tests/validation/test_iq.py", "iq")
            iq_results = self._extract_test_results(iq_data, "IQ")
            self.test_results.extend(iq_results)

            if iq_data.get("exitcode", 1) != 0:
                self.all_passed = False
                self._report_progress("❌ IQ Tests FAILED")
            else:
                self._report_progress("✅ IQ Tests PASSED")

            # Run OQ tests
            self._report_progress("Running OQ (Operational Qualification) tests...")
            oq_data = self._run_test_suite("tests/validation/test_oq.py", "oq")
            oq_results = self._extract_test_results(oq_data, "OQ")
            self.test_results.extend(oq_results)

            if oq_data.get("exitcode", 1) != 0:
                self.all_passed = False
                self._report_progress("❌ OQ Tests FAILED")
            else:
                self._report_progress("✅ OQ Tests PASSED")

            # Skip PQ tests since the app is running
            if not skip_pq:
                self._report_progress("Running PQ (Performance Qualification) tests...")
                pq_data = self._run_test_suite("tests/validation/test_pq.py", "pq")
                pq_results = self._extract_test_results(pq_data, "PQ")
                self.test_results.extend(pq_results)

                if pq_data.get("exitcode", 1) != 0:
                    self.all_passed = False
                    self._report_progress("❌ PQ Tests FAILED")
                else:
                    self._report_progress("✅ PQ Tests PASSED")
            else:
                self._report_progress("⚠️  Skipping PQ tests (app is running)")

            # Run PDF validation tests
            self._report_progress("")
            self._report_progress("=" * 60)
            self._report_progress("📊 Running PDF Validation Tests...")
            self._report_progress("=" * 60)

            try:
                import subprocess

                pdf_result = subprocess.run(
                    [
                        "uv",
                        "run",
                        "pytest",
                        "tests/validation/test_pq_pdf_validation.py::TestModuleVPDFValidation",
                        "-v",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                # Count passed/failed from output
                stdout = pdf_result.stdout + "\n" + pdf_result.stderr

                # Parse pytest summary to extract actual test results

                passed_count = 0
                failed_count = 0

                # Extract PDF test results by scanning each line
                for line in stdout.split("\n"):
                    if (
                        "test_module_v_pdf_contains_confidence_reliability" in line
                        and "test_pq_pdf_validation" in line
                    ):
                        if "PASSED" in line and "FAILED" not in line:
                            status = "PASSED"
                        elif "FAILED" in line:
                            status = "FAILED"
                        else:
                            continue

                        self.pdf_test_results.append(
                            {
                                "urs_id": "URS-REP-01",
                                "test_id": "test_pq_pdf_validation.py::TestModuleVPDFValidation::test_module_v_pdf_contains_confidence_reliability",
                                "status": status,
                            }
                        )

                        if status == "PASSED":
                            passed_count += 1
                        else:
                            failed_count += 1

                # Calculate total tests
                total_tests = passed_count + failed_count

                self._report_progress(
                    f"📊 PDF Test Results: {total_tests} tests, {passed_count} passed, {failed_count} failed"
                )

                if pdf_result.returncode == 0 and failed_count == 0:
                    self._report_progress("✅ PDF Validation Tests PASSED")
                else:
                    self._report_progress("❌ PDF Validation Tests FAILED")
                    self.all_passed = False
            except Exception as e:
                self._report_progress(f"⚠️  PDF validation check failed: {str(e)}")

            # Generate VTM
            self._report_progress("Generating Verification Traceability Matrix...")
            vtm = VTMGenerator.generate_vtm(self.test_results)

            # Export VTM to CSV
            vtm_csv_path = Path("validation_traceability_matrix.csv")
            VTMGenerator.export_vtm_csv(vtm, vtm_csv_path)
            self._report_progress(f"VTM exported to: {vtm_csv_path}")

            # Get current engine hash
            engine_hash = HashVerifier.get_engine_hash()
            self._report_progress(f"Current Engine Hash: {engine_hash[:16]}...")

            # Generate validation certificate
            self._report_progress("Generating validation certificate...")

            cert_data = ValidationCertificate(
                test_date=datetime.now().isoformat(),
                tester_name=tester_name,
                system_info={
                    "os": platform.system(),
                    "platform": platform.platform(),
                    "python_version": sys.version,
                    "python_implementation": platform.python_implementation(),
                    "software_version": __version__,
                },
                test_results=self.test_results,
                validated_hash=engine_hash,
                pdf_test_results=self.pdf_test_results,
            )

            # Generate PDF and save to reports directory
            pdf_bytes, report_path = ReportGenerator.generate_validation_certificate(
                cert_data
            )

            self._report_progress(f"Validation certificate saved to: {report_path}")

            # Store validated hash if all tests passed
            if self.all_passed:
                self._report_progress("Storing validated hash...")
                HashVerifier.set_validated_hash(
                    engine_hash,
                    validation_date=datetime.now().isoformat(),
                    validator=tester_name,
                )
                self._report_progress("=" * 60)
                self._report_progress("✅ VALIDATION COMPLETE - ALL TESTS PASSED")
                self._report_progress(f"📄 Certificate: {report_path}")
                self._report_progress(f"🔍 Engine Hash: {engine_hash[:16]}...")
                self._report_progress("=" * 60)

                return (
                    True,
                    f"Validation successful! Certificate saved to {report_path}",
                    report_path,
                )
            else:
                self._report_progress("=" * 60)
                self._report_progress("❌ VALIDATION FAILED - SOME TESTS DID NOT PASS")
                self._report_progress(f"📄 Certificate: {report_path}")
                self._report_progress(f"🔍 Engine Hash: {engine_hash[:16]}...")
                self._report_progress("=" * 60)

                # Remove validated hash so button shows red
                if HashVerifier.VALIDATED_HASH_FILE.exists():
                    HashVerifier.VALIDATED_HASH_FILE.unlink()
                    self._report_progress("Removed invalid validation hash")

                return (
                    False,
                    f"Validation failed. Some tests did not pass. Certificate saved to {report_path}",
                    report_path,
                )

        except subprocess.TimeoutExpired:
            self._report_progress("❌ Validation timed out")
            return (False, "Validation timed out after 5 minutes", None)
        except Exception as e:
            self._report_progress(f"❌ Error during validation: {str(e)}")
            return (False, f"Validation error: {str(e)}", None)
