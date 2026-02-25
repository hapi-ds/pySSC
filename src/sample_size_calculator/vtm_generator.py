"""Verification Traceability Matrix (VTM) generation.

This module provides functionality to generate VTM tables that link requirements
to test cases and their results for QMS compliance and validation documentation.
"""

from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle


class VTMGenerator:
    """Generates Verification Traceability Matrix for validation documentation."""

    @staticmethod
    def generate_vtm(test_results: list[dict], coverage_metrics: dict | None = None) -> pd.DataFrame:
        """Generate VTM from test results.

        Args:
            test_results: List of test result dictionaries with keys:
                - urs_id: URS requirement ID
                - requirement: Requirement text (optional)
                - test_id: Test case ID
                - result: Test result (PASS/FAIL)
            coverage_metrics: Optional dictionary containing URS coverage metrics with keys:
                - total_requirements: Total number of URS requirements
                - covered_requirements: Number of requirements covered by tests
                - uncovered_requirements: Number of requirements not covered
                - coverage_percentage: Percentage of requirements covered
                - uncovered_ids: List of URS IDs not covered by any test
                - coverage_by_category: Coverage breakdown by category
                - coverage_by_suite: Coverage breakdown by test suite

        Returns:
            DataFrame with columns: URS_ID, Requirement, Test_ID, Result

        Requirements:
            34.1, 34.2, 34.3, 34.5
        """
        # Extract data from test results
        vtm_data = []

        for test_result in test_results:
            urs_id = test_result.get("urs_id", "N/A")
            requirement = test_result.get("requirement", "")
            test_id = test_result.get("test_id", "N/A")
            result = test_result.get("result", test_result.get("status", "N/A"))

            vtm_data.append(
                {
                    "URS_ID": urs_id,
                    "Requirement": requirement,
                    "Test_ID": test_id,
                    "Result": result,
                }
            )

        # Create DataFrame
        vtm_df = pd.DataFrame(vtm_data)

        # Ensure columns are in the correct order
        column_order = ["URS_ID", "Requirement", "Test_ID", "Result"]
        vtm_df = vtm_df[column_order]

        return vtm_df

    @staticmethod
    def export_vtm_csv(
        vtm: pd.DataFrame, filepath: str | Path, coverage_metrics: dict | None = None
    ) -> None:
        """Export VTM to CSV file with optional coverage summary.

        Args:
            vtm: VTM DataFrame
            filepath: Path to output CSV file
            coverage_metrics: Optional dictionary containing URS coverage metrics

        Requirements:
            34.4
        """
        filepath = Path(filepath)

        # Ensure parent directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # If coverage metrics provided, add summary header
        if coverage_metrics:
            with open(filepath, "w") as f:
                # Write coverage summary as comments
                f.write("# VTM Coverage Summary\n")
                f.write(
                    f"# Total URS Requirements: {coverage_metrics.get('total_requirements', 0)}\n"
                )
                f.write(
                    f"# Covered by Tests: {coverage_metrics.get('covered_requirements', 0)}\n"
                )
                f.write(
                    f"# Coverage Percentage: {coverage_metrics.get('coverage_percentage', 0):.1f}%\n"
                )

                uncovered_ids = coverage_metrics.get("uncovered_ids", [])
                if uncovered_ids:
                    f.write(f"# Uncovered Requirements: {', '.join(uncovered_ids)}\n")

                f.write("#\n")
                f.write("# Coverage by Category:\n")
                coverage_by_category = coverage_metrics.get("coverage_by_category", {})
                for category, metrics in coverage_by_category.items():
                    f.write(
                        f"#   {category}: {metrics.get('covered', 0)}/{metrics.get('total', 0)} "
                        f"({metrics.get('percentage', 0):.1f}%)\n"
                    )
                f.write("#\n")

            # Append VTM data
            vtm.to_csv(filepath, mode="a", index=False)
        else:
            # Export to CSV without coverage summary
            vtm.to_csv(filepath, index=False)

    @staticmethod
    def add_vtm_to_pdf(story: list, vtm: pd.DataFrame) -> None:
        """Add VTM table to PDF report story.

        Args:
            story: ReportLab story list to append VTM table to
            vtm: VTM DataFrame to add to the PDF

        Requirements:
            34.4, 34.5

        Note:
            This method modifies the story list in place by appending
            VTM table elements.
        """
        # Get styles
        styles = getSampleStyleSheet()
        heading_style = styles["Heading2"]
        normal_style = styles["Normal"]

        # Add VTM section heading
        story.append(Paragraph("Verification Traceability Matrix", heading_style))
        story.append(Spacer(1, 0.1 * 72))  # 0.1 inch spacer

        # Convert DataFrame to table data using Flowable paragraphs
        table_data = []

        # Add header row
        header_row = [
            Paragraph("<b>URS ID</b>", normal_style),
            Paragraph("<b>Requirement</b>", normal_style),
            Paragraph("<b>Test ID</b>", normal_style),
            Paragraph("<b>Result</b>", normal_style),
        ]
        table_data.append(header_row)

        # Add data rows
        for _, row in vtm.iterrows():
            # Color code the result
            result = str(row["Result"])
            if result.upper() in ["PASS", "PASSED"]:
                result_text = f'<font color="green"><b>{result}</b></font>'
            elif result.upper() in ["FAIL", "FAILED"]:
                result_text = f'<font color="red"><b>{result}</b></font>'
            else:
                result_text = result

            data_row = [
                Paragraph(str(row["URS_ID"]), normal_style),
                Paragraph(str(row["Requirement"]), normal_style),
                Paragraph(str(row["Test_ID"]), normal_style),
                Paragraph(result_text, normal_style),
            ]
            table_data.append(data_row)

        # Create table with appropriate column widths
        # Total width: 6.5 inches (letter size with 0.75 inch margins)
        col_widths = [1.0 * 72, 2.5 * 72, 1.5 * 72, 1.0 * 72]  # in points

        vtm_table = Table(table_data, colWidths=col_widths)

        # Apply table style
        vtm_table.setStyle(
            TableStyle(
                [
                    # Header row styling
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    # Data rows styling
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.lightgrey],
                    ),
                ]
            )
        )

        # Add table to story
        story.append(vtm_table)
        story.append(Spacer(1, 0.2 * 72))  # 0.2 inch spacer

    @staticmethod
    def generate_vtm_from_pytest_results(pytest_json_path: str | Path) -> pd.DataFrame:
        """Generate VTM from pytest JSON report.

        Args:
            pytest_json_path: Path to pytest JSON report file

        Returns:
            VTM DataFrame

        Note:
            This is a helper method for integration with pytest validation suite.
            Requires pytest-json-report plugin.
        """
        import json

        pytest_json_path = Path(pytest_json_path)

        if not pytest_json_path.exists():
            raise FileNotFoundError(f"Pytest JSON report not found: {pytest_json_path}")

        # Load pytest JSON report
        with open(pytest_json_path) as f:
            pytest_data = json.load(f)

        # Extract test results
        test_results = []

        for test in pytest_data.get("tests", []):
            # Extract URS ID from test markers if available
            urs_ids = []
            for marker in test.get("markers", []):
                if marker.get("name") == "urs":
                    urs_ids.extend(marker.get("args", []))

            # Get test outcome
            outcome = test.get("outcome", "unknown")
            result = "PASSED" if outcome == "passed" else "FAILED"

            # Get test ID (nodeid)
            test_id = test.get("nodeid", "unknown")

            # Create entry for each URS ID
            if urs_ids:
                for urs_id in urs_ids:
                    test_results.append(
                        {
                            "urs_id": urs_id,
                            "test_id": test_id,
                            "result": result,
                        }
                    )
            else:
                # No URS marker, add with N/A
                test_results.append(
                    {
                        "urs_id": "N/A",
                        "test_id": test_id,
                        "result": result,
                    }
                )

        # Generate VTM
        return VTMGenerator.generate_vtm(test_results)
