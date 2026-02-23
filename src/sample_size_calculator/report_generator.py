"""PDF report generation using ReportLab.

This module provides functionality to generate PDF reports for user calculations
and validation certificates using ReportLab with Flowable paragraphs to prevent
text overflow.
"""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from sample_size_calculator.models import CalculationReport, ValidationCertificate


class ReportGenerator:
    """Generates PDF reports using ReportLab."""

    @staticmethod
    def generate_user_report(report_data: CalculationReport) -> bytes:
        """Generate user calculation report PDF.

        Args:
            report_data: CalculationReport model containing all report information

        Returns:
            PDF as bytes for download

        Requirements:
            27.1, 27.2, 27.3, 27.4, 27.5, 27.6, 28.2, 29.2, 29.3, 29.5
        """
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

        # Create results table using Flowable paragraphs
        result_data = []
        for key, value in report_data.results.items():
            # Format the key to be more readable
            formatted_key = key.replace("_", " ").title()
            # Use Paragraph for values to prevent overflow
            result_data.append(
                [
                    Paragraph(f"<b>{formatted_key}</b>", normal_style),
                    Paragraph(str(value), normal_style),
                ]
            )

        if result_data:
            result_table = Table(result_data, colWidths=[2.5 * inch, 4 * inch])
            result_table.setStyle(
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

        return pdf_bytes

    @staticmethod
    def generate_validation_certificate(cert_data: ValidationCertificate) -> bytes:
        """Generate validation certificate PDF.

        Args:
            cert_data: ValidationCertificate model containing validation information

        Returns:
            PDF as bytes for download

        Requirements:
            30.1, 30.2, 30.3, 30.4, 30.5, 30.6, 30.7
        """
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

        # Title
        story.append(Paragraph("Sample Size Calculator", title_style))
        story.append(Paragraph("Validation Certificate", heading_style))
        story.append(Spacer(1, 0.2 * inch))

        # Test Execution Date (Requirement 30.2)
        story.append(
            Paragraph(
                f"<b>Test Execution Date:</b> {cert_data.test_date}", normal_style
            )
        )
        story.append(Spacer(1, 0.1 * inch))

        # Tester Name (Requirement 30.3)
        story.append(
            Paragraph(f"<b>Tester Name:</b> {cert_data.tester_name}", normal_style)
        )
        story.append(Spacer(1, 0.2 * inch))

        # System Information (Requirement 30.4)
        story.append(Paragraph("System Information", heading_style))
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

        # Validated Hash (Requirement 30.6)
        story.append(Paragraph("Validated Calculation Engine", heading_style))
        story.append(Spacer(1, 0.1 * inch))
        story.append(
            Paragraph(
                f"<b>Validated Hash:</b> {cert_data.validated_hash}", normal_style
            )
        )
        story.append(Spacer(1, 0.2 * inch))

        # Test Results with VTM (Requirement 30.5)
        story.append(Paragraph("Verification Traceability Matrix", heading_style))
        story.append(Spacer(1, 0.1 * inch))

        # Create VTM table using Flowable paragraphs
        vtm_data = [
            [
                Paragraph("<b>URS ID</b>", normal_style),
                Paragraph("<b>Test ID</b>", normal_style),
                Paragraph("<b>Status</b>", normal_style),
            ]
        ]

        for test_result in cert_data.test_results:
            urs_id = test_result.get("urs_id", "N/A")
            test_id = test_result.get("test_id", "N/A")
            status = test_result.get("status", "N/A")

            # Color code the status
            if status.upper() in ["PASS", "PASSED"]:
                status_text = f'<font color="green"><b>{status}</b></font>'
            elif status.upper() in ["FAIL", "FAILED"]:
                status_text = f'<font color="red"><b>{status}</b></font>'
            else:
                status_text = status

            vtm_data.append(
                [
                    Paragraph(str(urs_id), normal_style),
                    Paragraph(str(test_id), normal_style),
                    Paragraph(status_text, normal_style),
                ]
            )

        if len(vtm_data) > 1:  # More than just header
            vtm_table = Table(vtm_data, colWidths=[2 * inch, 2.5 * inch, 2 * inch])
            vtm_table.setStyle(
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
            story.append(vtm_table)
        story.append(Spacer(1, 0.3 * inch))

        # Certification Statement
        cert_statement = (
            "This certificate confirms that the Sample Size Calculator "
            "application has successfully completed Installation "
            "Qualification (IQ), Operational Qualification (OQ), and "
            "Performance Qualification (PQ) testing. The calculation "
            "engine hash has been validated and recorded for future "
            "verification."
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

        return pdf_bytes

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
