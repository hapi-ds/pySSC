"""PDF report generation using ReportLab.

This module provides functionality to generate PDF reports for user calculations
and validation certificates using ReportLab with Flowable paragraphs to prevent
text overflow.
"""

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from sample_size_calculator.models import CalculationReport, ValidationCertificate
from sample_size_calculator.report_paths import (
    ensure_report_directories,
    get_calculation_report_path,
    get_validation_report_path,
    save_report,
)


class ReportGenerator:
    """Generates PDF reports using ReportLab."""

    @staticmethod
    def generate_user_report(report_data: CalculationReport) -> tuple[bytes, Path]:
        """Generate user calculation report PDF and save to reports directory.

        Args:
            report_data: CalculationReport model containing all report information

        Returns:
            Tuple of (PDF as bytes for download, Path to saved report file)

        Requirements:
            27.1, 27.2, 27.3, 27.4, 27.5, 27.6, 28.2, 29.2, 29.3, 29.5, 30.1
        """
        # Ensure report directories exist
        ensure_report_directories()
        # Create a BytesIO buffer to hold the PDF
        buffer = BytesIO()

        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=1 * inch,
            bottomMargin=0.75 * inch,
        )

        # Container for the 'Flowable' objects
        story = []

        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles["Title"]
        heading_style = styles["Heading2"]
        normal_style = styles["Normal"]

        # Create custom styles for better formatting
        bold_style = ParagraphStyle(
            "Bold",
            parent=normal_style,
            fontName="Helvetica-Bold",
        )

        # Title
        story.append(Paragraph("Sample Size Calculator", title_style))
        story.append(Paragraph("Calculation Report", heading_style))
        story.append(Spacer(1, 0.2 * inch))

        # Timestamp (Requirement 27.2)
        story.append(
            Paragraph(f"<b>Report Generated:</b> {report_data.timestamp}", normal_style)
        )
        story.append(Spacer(1, 0.1 * inch))

        # Module
        story.append(
            Paragraph(f"<b>Analysis Module:</b> {report_data.module}", normal_style)
        )
        story.append(Spacer(1, 0.2 * inch))

        # Engine Hash and Validation State (Requirements 28.2, 29.2, 29.3, 29.5)
        story.append(Paragraph("Engine Integrity Verification", heading_style))
        story.append(Spacer(1, 0.1 * inch))

        # Display engine hash
        story.append(
            Paragraph(f"<b>Engine Hash:</b> {report_data.engine_hash}", normal_style)
        )
        story.append(Spacer(1, 0.05 * inch))

        # Display validation state prominently
        validation_text = (
            "VALIDATED STATE: YES"
            if report_data.validation_state
            else "VALIDATED STATE: NO - UNVERIFIED CHANGE"
        )
        validation_color = "green" if report_data.validation_state else "red"
        validation_para = Paragraph(
            f'<b><font color="{validation_color}">{validation_text}</font></b>',
            bold_style,
        )
        story.append(validation_para)
        story.append(Spacer(1, 0.2 * inch))

        # Statistical Method Path (Requirement 27.5)
        story.append(Paragraph("Statistical Method", heading_style))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(report_data.method_path, normal_style))
        story.append(Spacer(1, 0.2 * inch))

        # User Inputs (Requirement 27.3)
        story.append(Paragraph("Input Parameters", heading_style))
        story.append(Spacer(1, 0.1 * inch))

        # Create input table using Flowable paragraphs
        input_data = []
        for key, value in report_data.inputs.items():
            # Format the key to be more readable
            formatted_key = key.replace("_", " ").title()
            # Use Paragraph for values to prevent overflow
            input_data.append(
                [
                    Paragraph(f"<b>{formatted_key}</b>", normal_style),
                    Paragraph(str(value), normal_style),
                ]
            )

        if input_data:
            input_table = Table(input_data, colWidths=[2.5 * inch, 4 * inch])
            input_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        (
                            "ROWBACKGROUNDS",
                            (0, 0),
                            (-1, -1),
                            [colors.white, colors.lightgrey],
                        ),
                    ]
                )
            )
            story.append(input_table)
        story.append(Spacer(1, 0.2 * inch))

        # Calculated Results (Requirement 27.4)
        story.append(Paragraph("Calculated Results", heading_style))
        story.append(Spacer(1, 0.1 * inch))

        # Create results table with professional formatting (Bug 9 fix)
        # Use 2-column table: Parameter, Value
        result_data = [
            # Header row
            [
                Paragraph("<b>Parameter</b>", bold_style),
                Paragraph("<b>Value</b>", bold_style),
            ]
        ]

        # Add data rows
        for key, value in report_data.results.items():
            formatted_key = key.replace("_", " ").title()

            if isinstance(value, float):
                value_str = f"{value:.4f}".rstrip("0").rstrip(".")
            elif isinstance(value, dict):
                value_str = ", ".join(f"{k}: {v}" for k, v in value.items())
            else:
                value_str = str(value)

            result_data.append(
                [
                    Paragraph(formatted_key, normal_style),
                    Paragraph(value_str, normal_style),
                ]
            )

        if len(result_data) > 1:  # More than just header
            result_table = Table(result_data, colWidths=[250, 200])
            result_table.setStyle(
                TableStyle(
                    [
                        # Header row styling
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 11),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        # Data rows styling
                        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                        (
                            "ALIGN",
                            (0, 1),
                            (0, -1),
                            "LEFT",
                        ),
                        (
                            "ALIGN",
                            (1, 1),
                            (1, -1),
                            "RIGHT",
                        ),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -1), 10),
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
            story.append(result_table)
        story.append(Spacer(1, 0.2 * inch))

        # Footer note
        story.append(Spacer(1, 0.3 * inch))
        footer_text = (
            "This report was generated by the Sample Size Calculator application. "
            "The validation state indicates whether the calculation engine has been "
            "formally validated and remains unchanged since validation."
        )
        story.append(Paragraph(footer_text, normal_style))

        # Build the PDF with page numbers
        doc.build(
            story,
            onFirstPage=ReportGenerator._add_page_number,
            onLaterPages=ReportGenerator._add_page_number,
        )

        # Get the PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Save to reports directory (Requirement 27.1, 30.1)
        report_path = get_calculation_report_path()
        saved_path = save_report(pdf_bytes, report_path)
        
        # Sign the PDF with hash for tamper detection
        try:
            signature = PDFSignature.sign_pdf(pdf_bytes, report_data.engine_hash)
            PDFSignature.save_signature(saved_path, signature)
        except Exception:
            # Signature failure should not prevent report generation
            pass

        return pdf_bytes, saved_path

    @staticmethod
    def generate_validation_certificate(
        cert_data: ValidationCertificate,
        coverage_metrics: dict | None = None,
    ) -> tuple[bytes, Path]:
        """Generate validation certificate PDF with separate IQ/OQ/PQ chapters.

        Args:
            cert_data: ValidationCertificate model containing validation information
            coverage_metrics: Optional dictionary containing URS coverage metrics

        Returns:
            Tuple of (PDF as bytes for download, Path to saved report file)
        """
        # Ensure report directories exist
        ensure_report_directories()

        # Create a BytesIO buffer to hold the PDF
        buffer = BytesIO()

        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=1 * inch,
            bottomMargin=0.75 * inch,
        )

        # Container for the 'Flowable' objects
        story = []

        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles["Title"]
        heading_style = styles["Heading2"]
        heading3_style = styles["Heading3"]
        normal_style = styles["Normal"]

        # ===== TITLE PAGE =====
        story.append(Paragraph("Sample Size Calculator", title_style))
        story.append(Paragraph("Validation Certificate", heading_style))
        story.append(Spacer(1, 0.3 * inch))

        # Test Execution Date
        story.append(
            Paragraph(
                f"<b>Test Execution Date:</b> {cert_data.test_date}", normal_style
            )
        )
        story.append(Spacer(1, 0.1 * inch))

        # Tester Name
        story.append(
            Paragraph(f"<b>Tester Name:</b> {cert_data.tester_name}", normal_style)
        )
        story.append(Spacer(1, 0.2 * inch))

        # System Information
        story.append(Paragraph("System Information", heading3_style))
        story.append(Spacer(1, 0.1 * inch))

        sys_info_data = []
        for key, value in cert_data.system_info.items():
            formatted_key = key.replace("_", " ").title()
            sys_info_data.append(
                [
                    Paragraph(f"<b>{formatted_key}</b>", normal_style),
                    Paragraph(str(value), normal_style),
                ]
            )

        if sys_info_data:
            sys_info_table = Table(sys_info_data, colWidths=[2.5 * inch, 4 * inch])
            sys_info_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        (
                            "ROWBACKGROUNDS",
                            (0, 0),
                            (-1, -1),
                            [colors.white, colors.lightgrey],
                        ),
                    ]
                )
            )
            story.append(sys_info_table)

        story.append(Spacer(1, 0.2 * inch))

        # Validated Hash
        story.append(Paragraph("Validated Calculation Engine", heading3_style))
        story.append(Spacer(1, 0.1 * inch))
        story.append(
            Paragraph(
                f"<b>Validated Hash:</b> {cert_data.validated_hash}", normal_style
            )
        )

        # Page break before chapters
        story.append(PageBreak())

        # ===== HELPER FUNCTION TO GROUP TEST RESULTS BY TEST_ID =====
        def group_test_results_by_test_id(results: list[dict]) -> list[dict]:
            """Group test results by test_id, combining multiple URS IDs."""
            grouped = {}
            for result in results:
                test_id = result.get("test_id", "N/A")
                if test_id not in grouped:
                    grouped[test_id] = {
                        "test_id": test_id,
                        "urs_ids": [],
                        "status": result.get("status", "N/A"),
                    }
                urs_id = result.get("urs_id", "N/A")
                if urs_id not in grouped[test_id]["urs_ids"]:
                    grouped[test_id]["urs_ids"].append(urs_id)

            # Convert back to list format with combined URS IDs
            return [
                {
                    "test_id": data["test_id"],
                    "urs_id": ", ".join(data["urs_ids"]),
                    "status": data["status"],
                }
                for data in grouped.values()
            ]

        # ===== SEPARATE TEST RESULTS BY SUITE =====
        iq_results_raw = [
            r for r in cert_data.test_results if "test_iq.py" in r.get("test_id", "")
        ]
        oq_results_raw = [
            r for r in cert_data.test_results if "test_oq.py" in r.get("test_id", "")
        ]
        pq_results_raw = [
            r for r in cert_data.test_results if "test_pq.py" in r.get("test_id", "")
        ]

        # Group results to combine multiple URS IDs per test
        iq_results = group_test_results_by_test_id(iq_results_raw)
        oq_results = group_test_results_by_test_id(oq_results_raw)
        pq_results = group_test_results_by_test_id(pq_results_raw)

        # ===== CHAPTER 1: IQ RESULTS =====
        story.append(
            Paragraph("CHAPTER 1: INSTALLATION QUALIFICATION (IQ)", heading_style)
        )
        story.append(Spacer(1, 0.2 * inch))

        if iq_results:
            # IQ Test Results Table
            iq_data = [
                [
                    Paragraph("<b>URS ID</b>", normal_style),
                    Paragraph("<b>Test ID</b>", normal_style),
                    Paragraph("<b>Status</b>", normal_style),
                ]
            ]

            for test_result in iq_results:
                test_id = test_result.get("test_id", "N/A")
                urs_id = test_result.get("urs_id", "N/A")
                status = test_result.get("status", "N/A")

                # Color code the status
                if status.upper() in ["PASS", "PASSED"]:
                    status_text = f'<font color="green"><b>{status}</b></font>'
                elif status.upper() in ["FAIL", "FAILED"]:
                    status_text = f'<font color="red"><b>{status}</b></font>'
                else:
                    status_text = status

                iq_data.append(
                    [
                        Paragraph(str(urs_id), normal_style),
                        Paragraph(str(test_id), normal_style),
                        Paragraph(status_text, normal_style),
                    ]
                )

            iq_table = Table(iq_data, colWidths=[2 * inch, 2.5 * inch, 2 * inch])
            iq_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
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
            story.append(iq_table)
            story.append(Spacer(1, 0.2 * inch))

            # IQ Summary
            iq_passed = sum(
                1
                for r in iq_results
                if r.get("status", "").upper() in ["PASS", "PASSED"]
            )
            iq_failed = len(iq_results) - iq_passed
            iq_urs_ids = set()
            for r in iq_results:
                urs_id_str = r.get("urs_id", "")
                for urs_id in urs_id_str.split(", "):
                    if urs_id and urs_id != "N/A":
                        iq_urs_ids.add(urs_id)

            story.append(Paragraph("<b>IQ Summary:</b>", normal_style))
            story.append(Spacer(1, 0.05 * inch))
            story.append(Paragraph(f"Total Tests: {len(iq_results)}", normal_style))
            story.append(Paragraph(f"Passed: {iq_passed}", normal_style))
            story.append(Paragraph(f"Failed: {iq_failed}", normal_style))
            story.append(
                Paragraph(
                    f"URS Coverage: {', '.join(sorted(iq_urs_ids))}", normal_style
                )
            )
        else:
            story.append(Paragraph("No IQ tests found.", normal_style))

        # Page break before next chapter
        story.append(PageBreak())

        # ===== CHAPTER 2: OQ RESULTS =====
        story.append(
            Paragraph("CHAPTER 2: OPERATIONAL QUALIFICATION (OQ)", heading_style)
        )
        story.append(Spacer(1, 0.2 * inch))

        if oq_results:
            # OQ Test Results Table
            oq_data = [
                [
                    Paragraph("<b>URS ID</b>", normal_style),
                    Paragraph("<b>Test ID</b>", normal_style),
                    Paragraph("<b>Status</b>", normal_style),
                ]
            ]

            for test_result in oq_results:
                test_id = test_result.get("test_id", "N/A")
                urs_id = test_result.get("urs_id", "N/A")
                status = test_result.get("status", "N/A")

                # Color code the status
                if status.upper() in ["PASS", "PASSED"]:
                    status_text = f'<font color="green"><b>{status}</b></font>'
                elif status.upper() in ["FAIL", "FAILED"]:
                    status_text = f'<font color="red"><b>{status}</b></font>'
                else:
                    status_text = status

                oq_data.append(
                    [
                        Paragraph(str(urs_id), normal_style),
                        Paragraph(str(test_id), normal_style),
                        Paragraph(status_text, normal_style),
                    ]
                )

            oq_table = Table(oq_data, colWidths=[2 * inch, 2.5 * inch, 2 * inch])
            oq_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
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
            story.append(oq_table)
            story.append(Spacer(1, 0.2 * inch))

            # OQ Summary
            oq_passed = sum(
                1
                for r in oq_results
                if r.get("status", "").upper() in ["PASS", "PASSED"]
            )
            oq_failed = len(oq_results) - oq_passed
            oq_urs_ids = set()
            for r in oq_results:
                urs_id_str = r.get("urs_id", "")
                for urs_id in urs_id_str.split(", "):
                    if urs_id and urs_id != "N/A":
                        oq_urs_ids.add(urs_id)

            story.append(Paragraph("<b>OQ Summary:</b>", normal_style))
            story.append(Spacer(1, 0.05 * inch))
            story.append(Paragraph(f"Total Tests: {len(oq_results)}", normal_style))
            story.append(Paragraph(f"Passed: {oq_passed}", normal_style))
            story.append(Paragraph(f"Failed: {oq_failed}", normal_style))
            story.append(
                Paragraph(
                    f"URS Coverage: {', '.join(sorted(oq_urs_ids))}", normal_style
                )
            )
        else:
            story.append(Paragraph("No OQ tests found.", normal_style))

        # Page break before next chapter
        story.append(PageBreak())

        # ===== CHAPTER 3: PQ RESULTS =====
        story.append(
            Paragraph("CHAPTER 3: PERFORMANCE QUALIFICATION (PQ)", heading_style)
        )
        story.append(Spacer(1, 0.2 * inch))

        if pq_results:
            # PQ Test Results Table
            pq_data = [
                [
                    Paragraph("<b>URS ID</b>", normal_style),
                    Paragraph("<b>Test ID</b>", normal_style),
                    Paragraph("<b>Status</b>", normal_style),
                ]
            ]

            for test_result in pq_results:
                test_id = test_result.get("test_id", "N/A")
                urs_id = test_result.get("urs_id", "N/A")
                status = test_result.get("status", "N/A")

                # Color code the status
                if status.upper() in ["PASS", "PASSED"]:
                    status_text = f'<font color="green"><b>{status}</b></font>'
                elif status.upper() in ["FAIL", "FAILED"]:
                    status_text = f'<font color="red"><b>{status}</b></font>'
                else:
                    status_text = status

                pq_data.append(
                    [
                        Paragraph(str(urs_id), normal_style),
                        Paragraph(str(test_id), normal_style),
                        Paragraph(status_text, normal_style),
                    ]
                )

            pq_table = Table(pq_data, colWidths=[2 * inch, 2.5 * inch, 2 * inch])
            pq_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
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
            story.append(pq_table)
            story.append(Spacer(1, 0.2 * inch))

            # PQ Summary
            pq_passed = sum(
                1
                for r in pq_results
                if r.get("status", "").upper() in ["PASS", "PASSED"]
            )
            pq_failed = len(pq_results) - pq_passed
            pq_urs_ids = set()
            for r in pq_results:
                urs_id_str = r.get("urs_id", "")
                for urs_id in urs_id_str.split(", "):
                    if urs_id and urs_id != "N/A":
                        pq_urs_ids.add(urs_id)

            story.append(Paragraph("<b>PQ Summary:</b>", normal_style))
            story.append(Spacer(1, 0.05 * inch))
            story.append(Paragraph(f"Total Tests: {len(pq_results)}", normal_style))
            story.append(Paragraph(f"Passed: {pq_passed}", normal_style))
            story.append(Paragraph(f"Failed: {pq_failed}", normal_style))
            story.append(
                Paragraph(
                    f"URS Coverage: {', '.join(sorted(pq_urs_ids))}", normal_style
                )
            )
        else:
            story.append(Paragraph("No PQ tests found.", normal_style))

        # Page break before PDF validation results
        story.append(PageBreak())
        
        # ===== CHAPTER 3.5: PDF VALIDATION RESULTS =====
        story.append(Paragraph("CHAPTER 3.5: PDF VALIDATION RESULTS", heading_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Check if we have PDF test results (from validation_runner)
        pdf_test_results = cert_data.pdf_test_results if hasattr(cert_data, 'pdf_test_results') and cert_data.pdf_test_results else []
        
        if pdf_test_results:
            story.append(Paragraph("PDF Report Content Validation Tests", heading3_style))
            story.append(Spacer(1, 0.1 * inch))
            
            # Extract PDF test results
            pdf_iq = [r for r in pdf_test_results if "test_iq" in r.get("test_id", "")]
            pdf_oq = [r for r in pdf_test_results if "test_oq" in r.get("test_id", "")]
            pdf_pq_pdf = [r for r in pdf_test_results if "test_pq" in r.get("test_id", "") and "pdf" in r.get("test_id", "").lower()]
            
            total_pdf_tests = len(pdf_iq) + len(pdf_oq) + len(pdf_pq_pdf)
            pdf_passed = sum(1 for r in pdf_test_results if r.get("status", "").upper() in ["PASS", "PASSED"])
            pdf_failed = total_pdf_tests - pdf_passed
            
            story.append(Paragraph(f"<b>PDF Test Summary:</b>", normal_style))
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph(f"Total Tests: {total_pdf_tests}", normal_style))
            story.append(Paragraph(f"Passed: {pdf_passed}", normal_style))
            story.append(Paragraph(f"Failed: {pdf_failed}", normal_style))
            
            if total_pdf_tests > 0:
                # PDF test results table
                pdf_data = [
                    [
                        Paragraph("<b>Test ID</b>", normal_style),
                        Paragraph("<b>URS ID</b>", normal_style),
                        Paragraph("<b>Status</b>", normal_style),
                    ]
                ]
                
                for result in pdf_test_results:
                    test_id = result.get("test_id", "N/A")
                    urs_id = result.get("urs_id", "N/A")
                    status = result.get("status", "N/A")
                    
                    # Color code the status
                    if str(status).upper() in ["PASS", "PASSED"]:
                        status_text = f'<font color="green"><b>{status}</b></font>'
                    elif str(status).upper() in ["FAIL", "FAILED"]:
                        status_text = f'<font color="red"><b>{status}</b></font>'
                    else:
                        status_text = status
                    
                    pdf_data.append(
                        [
                            Paragraph(str(test_id), normal_style),
                            Paragraph(str(urs_id), normal_style),
                            Paragraph(status_text, normal_style),
                        ]
                    )
                
                pdf_table = Table(pdf_data, colWidths=[3 * inch, 2 * inch, 1.5 * inch])
                pdf_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 9),
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
                story.append(pdf_table)
        else:
            story.append(Paragraph("No PDF validation tests were run.", normal_style))
        
        story.append(Spacer(1, 0.3 * inch))
        
        # Page break before summary chapter
        story.append(PageBreak())

        # ===== CHAPTER 4: VALIDATION SUMMARY =====
        story.append(Paragraph("CHAPTER 4: VALIDATION SUMMARY", heading_style))
        story.append(Spacer(1, 0.2 * inch))

        # Overall test results (use grouped results for accurate count)
        total_tests = len(iq_results) + len(oq_results) + len(pq_results)
        total_passed = (
            sum(
                1
                for r in iq_results
                if r.get("status", "").upper() in ["PASS", "PASSED"]
            )
            + sum(
                1
                for r in oq_results
                if r.get("status", "").upper() in ["PASS", "PASSED"]
            )
            + sum(
                1
                for r in pq_results
                if r.get("status", "").upper() in ["PASS", "PASSED"]
            )
        )
        total_failed = total_tests - total_passed
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        story.append(Paragraph("<b>Overall Test Results:</b>", heading3_style))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(f"Total Tests: {total_tests}", normal_style))
        story.append(Paragraph(f"Passed: {total_passed}", normal_style))
        story.append(Paragraph(f"Failed: {total_failed}", normal_style))
        story.append(Paragraph(f"Success Rate: {success_rate:.1f}%", normal_style))
        story.append(Spacer(1, 0.3 * inch))

        # Coverage Summary Section (if coverage metrics provided)
        if coverage_metrics:
            story.append(Paragraph("<b>URS Coverage Summary:</b>", heading3_style))
            story.append(Spacer(1, 0.1 * inch))

            # Overall coverage metrics
            coverage_data = [
                [
                    Paragraph("<b>Metric</b>", normal_style),
                    Paragraph("<b>Value</b>", normal_style),
                ]
            ]

            coverage_data.append(
                [
                    Paragraph("Total URS Requirements", normal_style),
                    Paragraph(
                        str(coverage_metrics.get("total_requirements", 0)),
                        normal_style,
                    ),
                ]
            )
            coverage_data.append(
                [
                    Paragraph("Covered by Tests", normal_style),
                    Paragraph(
                        str(coverage_metrics.get("covered_requirements", 0)),
                        normal_style,
                    ),
                ]
            )
            coverage_data.append(
                [
                    Paragraph("Coverage Percentage", normal_style),
                    Paragraph(
                        f"{coverage_metrics.get('coverage_percentage', 0):.1f}%",
                        normal_style,
                    ),
                ]
            )

            coverage_table = Table(coverage_data, colWidths=[3 * inch, 3.5 * inch])
            coverage_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
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
            story.append(coverage_table)

            # Uncovered requirements (if any)
            uncovered_ids = coverage_metrics.get("uncovered_ids", [])
            if uncovered_ids:
                story.append(Spacer(1, 0.2 * inch))
                story.append(
                    Paragraph(
                        "<b>Uncovered Requirements:</b>",
                        normal_style,
                    )
                )
                story.append(Spacer(1, 0.05 * inch))

                uncovered_text = ", ".join(uncovered_ids)
                story.append(Paragraph(uncovered_text, normal_style))

            # Coverage by category
            coverage_by_category = coverage_metrics.get("coverage_by_category", {})
            if coverage_by_category:
                story.append(Spacer(1, 0.3 * inch))
                story.append(Paragraph("<b>Coverage by Category:</b>", heading3_style))
                story.append(Spacer(1, 0.1 * inch))

                category_data = [
                    [
                        Paragraph("<b>Category</b>", normal_style),
                        Paragraph("<b>Total</b>", normal_style),
                        Paragraph("<b>Covered</b>", normal_style),
                        Paragraph("<b>Coverage %</b>", normal_style),
                    ]
                ]

                for category, metrics in coverage_by_category.items():
                    category_data.append(
                        [
                            Paragraph(category, normal_style),
                            Paragraph(str(metrics.get("total", 0)), normal_style),
                            Paragraph(str(metrics.get("covered", 0)), normal_style),
                            Paragraph(
                                f"{metrics.get('percentage', 0):.1f}%", normal_style
                            ),
                        ]
                    )

                category_table = Table(
                    category_data,
                    colWidths=[2 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch],
                )
                category_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 9),
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
                story.append(category_table)

        story.append(Spacer(1, 0.3 * inch))

        # Overall validation status
        validation_status = "✓ PASSED" if total_failed == 0 else "✗ FAILED"
        status_color = "green" if total_failed == 0 else "red"
        story.append(
            Paragraph(
                f'<b>Validation Status:</b> <font color="{status_color}"><b>{validation_status}</b></font>',
                heading3_style,
            )
        )
        story.append(Spacer(1, 0.2 * inch))

        # Certification Statement
        cert_statement = (
            "This certificate confirms that the Sample Size Calculator "
            "application has completed Installation Qualification (IQ), "
            "Operational Qualification (OQ), and Performance Qualification (PQ) "
            "testing. The calculation engine hash has been validated and recorded "
            "for future verification."
        )
        story.append(Paragraph(cert_statement, normal_style))

        # Build the PDF with page numbers
        doc.build(
            story,
            onFirstPage=ReportGenerator._add_page_number,
            onLaterPages=ReportGenerator._add_page_number,
        )

        # Get the PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Save to reports directory
        report_path = get_validation_report_path()
        save_report(pdf_bytes, report_path)

        return pdf_bytes, report_path

    @staticmethod
    def _add_page_number(canvas, doc) -> None:
        """Add page numbers to the footer of each page.

        Args:
            canvas: ReportLab canvas object
            doc: ReportLab document object
        """
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.saveState()
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(7.5 * inch, 0.5 * inch, text)
        canvas.restoreState()
