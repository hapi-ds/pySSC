"""Property-based tests for VTM generation.

This module contains property-based tests using Hypothesis to verify
the correctness and completeness of Verification Traceability Matrix generation.
"""

import tempfile
from pathlib import Path

import pandas as pd
from hypothesis import given
from hypothesis import strategies as st

from src.sample_size_calculator.vtm_generator import VTMGenerator


class TestVTMGeneration:
    """Property-based tests for VTM generation functionality."""

    @given(
        num_test_results=st.integers(min_value=1, max_value=50),
    )
    def test_property_31_vtm_completeness(
        self,
        num_test_results: int,
    ) -> None:
        """Property 31: Verification Traceability Matrix Completeness.

        **Validates: Requirements 34.1, 34.2, 34.3, 34.5**

        For any set of test results, the generated VTM must include:
        - URS ID for each requirement (34.1)
        - Test ID for each test case (34.2)
        - Test result (passed/failed) for each test case (34.3)
        - All test results in structured format (34.5)
        """
        # Create test results
        test_results = []
        for i in range(num_test_results):
            test_results.append(
                {
                    "urs_id": f"REQ-{i + 1}",
                    "requirement": f"Requirement {i + 1} description",
                    "test_id": f"TEST-{i + 1}",
                    "result": "PASSED" if i % 2 == 0 else "FAILED",
                }
            )

        # Generate VTM
        vtm = VTMGenerator.generate_vtm(test_results)

        # Verify VTM is a DataFrame
        assert isinstance(vtm, pd.DataFrame), "VTM should be a pandas DataFrame"

        # Requirement 34.1: Verify URS_ID column exists and has all entries
        assert "URS_ID" in vtm.columns, "VTM should have URS_ID column"
        assert len(vtm) == num_test_results, (
            f"VTM should have {num_test_results} rows, got {len(vtm)}"
        )
        assert vtm["URS_ID"].notna().all(), "All URS_ID entries should be non-null"

        # Requirement 34.2: Verify Test_ID column exists and has all entries
        assert "Test_ID" in vtm.columns, "VTM should have Test_ID column"
        assert vtm["Test_ID"].notna().all(), "All Test_ID entries should be non-null"

        # Requirement 34.3: Verify Result column exists and has all entries
        assert "Result" in vtm.columns, "VTM should have Result column"
        assert vtm["Result"].notna().all(), "All Result entries should be non-null"

        # Requirement 34.1: Verify Requirement column exists
        assert "Requirement" in vtm.columns, "VTM should have Requirement column"

        # Verify column order (34.5 - structured format)
        expected_columns = ["URS_ID", "Requirement", "Test_ID", "Result"]
        assert list(vtm.columns) == expected_columns, (
            f"VTM columns should be {expected_columns}, got {list(vtm.columns)}"
        )

        # Verify all URS IDs are present
        for i in range(num_test_results):
            expected_urs_id = f"REQ-{i + 1}"
            assert expected_urs_id in vtm["URS_ID"].values, (
                f"VTM should include URS ID: {expected_urs_id}"
            )

        # Verify all Test IDs are present
        for i in range(num_test_results):
            expected_test_id = f"TEST-{i + 1}"
            assert expected_test_id in vtm["Test_ID"].values, (
                f"VTM should include Test ID: {expected_test_id}"
            )

        # Verify all results are valid
        valid_results = ["PASSED", "FAILED"]
        assert vtm["Result"].isin(valid_results).all(), (
            f"All results should be in {valid_results}"
        )

    @given(
        num_test_results=st.integers(min_value=1, max_value=20),
    )
    def test_property_31_vtm_csv_export(
        self,
        num_test_results: int,
    ) -> None:
        """Property 31: VTM CSV Export (additional validation).

        **Validates: Requirements 34.4**

        The VTM should be exportable to CSV format and the exported
        file should contain all the data.
        """
        # Create test results
        test_results = []
        for i in range(num_test_results):
            test_results.append(
                {
                    "urs_id": f"REQ-{i + 1}",
                    "requirement": f"Requirement {i + 1}",
                    "test_id": f"TEST-{i + 1}",
                    "result": "PASSED" if i % 3 != 0 else "FAILED",
                }
            )

        # Generate VTM
        vtm = VTMGenerator.generate_vtm(test_results)

        # Export to CSV in a temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "vtm.csv"

            # Export VTM
            VTMGenerator.export_vtm_csv(vtm, csv_path)

            # Verify file was created
            assert csv_path.exists(), "CSV file should be created"

            # Read the CSV back
            vtm_from_csv = pd.read_csv(csv_path)

            # Verify data integrity
            assert len(vtm_from_csv) == num_test_results, (
                f"CSV should have {num_test_results} rows"
            )
            assert list(vtm_from_csv.columns) == list(vtm.columns), (
                "CSV should have same columns as original VTM"
            )

            # Verify all URS IDs are present in CSV
            for i in range(num_test_results):
                expected_urs_id = f"REQ-{i + 1}"
                assert expected_urs_id in vtm_from_csv["URS_ID"].values, (
                    f"CSV should include URS ID: {expected_urs_id}"
                )

    @given(
        num_test_results=st.integers(min_value=1, max_value=30),
    )
    def test_property_31_vtm_pdf_integration(
        self,
        num_test_results: int,
    ) -> None:
        """Property 31: VTM PDF Integration (additional validation).

        **Validates: Requirements 34.4, 34.5**

        The VTM should be integrable into PDF reports using ReportLab
        without errors, even with varying amounts of data.
        """
        # Create test results
        test_results = []
        for i in range(num_test_results):
            test_results.append(
                {
                    "urs_id": f"REQ-{i + 1}",
                    "requirement": f"Requirement {i + 1} with some description text",
                    "test_id": f"TEST-{i + 1}",
                    "result": "PASSED" if i % 2 == 0 else "FAILED",
                }
            )

        # Generate VTM
        vtm = VTMGenerator.generate_vtm(test_results)

        # Create a story list for PDF
        story = []

        # Add VTM to PDF story - should not raise an exception
        try:
            VTMGenerator.add_vtm_to_pdf(story, vtm)
        except Exception as e:
            raise AssertionError(f"Adding VTM to PDF should not fail: {e}") from e

        # Verify story was modified
        assert len(story) > 0, "Story should have VTM elements added"

        # Verify story contains expected elements
        # Should have at least: heading, spacer, table, spacer
        assert len(story) >= 3, "Story should have at least heading, table, and spacers"

    @given(
        num_passed=st.integers(min_value=0, max_value=20),
        num_failed=st.integers(min_value=0, max_value=20),
    )
    def test_property_31_vtm_result_tracking(
        self,
        num_passed: int,
        num_failed: int,
    ) -> None:
        """Property 31: VTM Result Tracking (additional validation).

        **Validates: Requirements 34.3**

        The VTM should correctly track and display pass/fail results
        for all test cases.
        """
        # Skip if no tests
        if num_passed == 0 and num_failed == 0:
            return

        # Create test results with mixed pass/fail
        test_results = []
        for i in range(num_passed):
            test_results.append(
                {
                    "urs_id": f"REQ-PASS-{i + 1}",
                    "test_id": f"TEST-PASS-{i + 1}",
                    "result": "PASSED",
                }
            )
        for i in range(num_failed):
            test_results.append(
                {
                    "urs_id": f"REQ-FAIL-{i + 1}",
                    "test_id": f"TEST-FAIL-{i + 1}",
                    "result": "FAILED",
                }
            )

        # Generate VTM
        vtm = VTMGenerator.generate_vtm(test_results)

        # Verify total count
        assert len(vtm) == num_passed + num_failed, (
            f"VTM should have {num_passed + num_failed} rows"
        )

        # Verify passed count
        passed_count = (vtm["Result"] == "PASSED").sum()
        assert passed_count == num_passed, (
            f"VTM should have {num_passed} PASSED results, got {passed_count}"
        )

        # Verify failed count
        failed_count = (vtm["Result"] == "FAILED").sum()
        assert failed_count == num_failed, (
            f"VTM should have {num_failed} FAILED results, got {failed_count}"
        )

    @given(
        num_test_results=st.integers(min_value=1, max_value=10),
    )
    def test_property_31_vtm_handles_missing_fields(
        self,
        num_test_results: int,
    ) -> None:
        """Property 31: VTM Handles Missing Fields (additional validation).

        **Validates: Requirements 34.1, 34.2, 34.3**

        The VTM should handle test results with missing optional fields
        gracefully, using default values where appropriate.
        """
        # Create test results with some missing fields
        test_results = []
        for i in range(num_test_results):
            result = {
                "urs_id": f"REQ-{i + 1}",
                "test_id": f"TEST-{i + 1}",
            }

            # Randomly omit requirement field
            if i % 2 == 0:
                result["requirement"] = f"Requirement {i + 1}"

            # Randomly use 'status' instead of 'result'
            if i % 3 == 0:
                result["status"] = "PASSED"
            else:
                result["result"] = "FAILED"

            test_results.append(result)

        # Generate VTM - should not raise an exception
        try:
            vtm = VTMGenerator.generate_vtm(test_results)
        except Exception as e:
            raise AssertionError(
                f"VTM generation should handle missing fields: {e}"
            ) from e

        # Verify VTM was created
        assert isinstance(vtm, pd.DataFrame), "VTM should be a DataFrame"
        assert len(vtm) == num_test_results, f"VTM should have {num_test_results} rows"

        # Verify all required columns exist
        assert "URS_ID" in vtm.columns, "VTM should have URS_ID column"
        assert "Test_ID" in vtm.columns, "VTM should have Test_ID column"
        assert "Result" in vtm.columns, "VTM should have Result column"
        assert "Requirement" in vtm.columns, "VTM should have Requirement column"

    @given(
        num_test_results=st.integers(min_value=1, max_value=100),
    )
    def test_property_31_vtm_scalability(
        self,
        num_test_results: int,
    ) -> None:
        """Property 31: VTM Scalability (additional validation).

        **Validates: Requirements 34.5**

        The VTM generation should handle large numbers of test results
        efficiently without errors.
        """
        # Create many test results
        test_results = []
        for i in range(num_test_results):
            test_results.append(
                {
                    "urs_id": f"REQ-{i + 1:04d}",
                    "requirement": f"Requirement {i + 1} with detailed description text",
                    "test_id": f"TEST-{i + 1:04d}",
                    "result": "PASSED" if i % 5 != 0 else "FAILED",
                }
            )

        # Generate VTM - should complete without errors
        try:
            vtm = VTMGenerator.generate_vtm(test_results)
        except Exception as e:
            raise AssertionError(
                f"VTM generation should handle {num_test_results} results: {e}"
            ) from e

        # Verify VTM was created correctly
        assert len(vtm) == num_test_results, f"VTM should have {num_test_results} rows"

        # Verify data integrity
        assert vtm["URS_ID"].notna().all(), "All URS_ID entries should be non-null"
        assert vtm["Test_ID"].notna().all(), "All Test_ID entries should be non-null"
        assert vtm["Result"].notna().all(), "All Result entries should be non-null"

        # Verify no duplicates in the index
        assert not vtm.index.duplicated().any(), "VTM should not have duplicate indices"
