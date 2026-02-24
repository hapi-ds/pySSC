"""Full comprehensive report generation module.

This module generates comprehensive PDF reports that combine:
- Sample size calculation report (current calculation)
- Latest validation reports (IQ/OQ/PQ certificates)
- Audit trail logs (filtered for current session)
- Calculator signature (engine hash and validation state)

Requirements: 27.1, 28.2, 29.2, 30.1, 38.16
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

from sample_size_calculator.hash_verifier import HashVerifier
from sample_size_calculator.models import CalculationReport


class FullReportGenerator:
    """Generates comprehensive full reports combining all aspects of a calculation session."""

    @staticmethod
    def generate_full_report(
        calculation_report: CalculationReport,
        session_id: str,
        log_dir: str = "logs",
        validation_reports_dir: str = "reports/validation",
    ) -> bytes:
        """Generate comprehensive full report PDF.

        Combines:
        - Current calculation report
        - Latest validation certificates
        - Audit trail logs for the session
        - Calculator signature (engine hash and validation state)

        Args:
            calculation_report: CalculationReport model with current calculation
            session_id: User session identifier for filtering logs
            log_dir: Directory containing audit log files
            validation_reports_dir: Directory containing validation certificates

        Returns:
            PDF as bytes for download

        Requirements:
            27.1, 28.2, 29.2, 30.1, 38.16
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
        heading_style = styles["Heading1"]
        heading2_style = styles["Heading2"]
        normal_style = styles["Normal"]

        # Create custom styles
        bold_style = ParagraphStyle(
            "Bold",
            parent=normal_style,
            fontName="Helvetica-Bold",
        )

        # ===== TITLE PAGE =====
        story.append(Paragraph("Sample Size Calculator", title_style))
        story.append(Paragraph("Comprehensive Full Report", heading_style))
        story.append(Spacer(1, 0.3 * inch))

        # Report metadata
        story.append(
            Paragraph(
                f"<b>Report Generated:</b> {calculation_report.timestamp}",
                normal_style,
            )
        )
        story.append(Paragraph(f"<b>Session ID:</b> {session_id}", normal_style))
        story.append(Spacer(1, 0.2 * inch))

        # ===== TABLE OF CONTENTS =====
        story.append(Paragraph("Table of Contents", heading2_style))
        story.append(Spacer(1, 0.1 * inch))

        toc_items = [
            "1. Calculator Signature",
            "2. Current Calculation Report",
            "3. Validation Status",
            "4. Audit Trail (Session Logs)",
        ]

        for item in toc_items:
            story.append(Paragraph(item, normal_style))
            story.append(Spacer(1, 0.05 * inch))

        story.append(PageBreak())

        # ===== SECTION 1: CALCULATOR SIGNATURE =====
        story.append(Paragraph("1. Calculator Signature", heading_style))
        story.append(Spacer(1, 0.2 * inch))

        # Engine hash and validation state
        engine_hash = HashVerifier.get_engine_hash()
        validation_state = HashVerifier.is_validated_state()

        story.append(Paragraph("Engine Integrity Verification", heading2_style))
        story.append(Spacer(1, 0.1 * inch))

        story.append(Paragraph(f"<b>Engine Hash:</b> {engine_hash}", normal_style))
        story.append(Spacer(1, 0.05 * inch))

        # Display validation state prominently
        validation_text = (
            "VALIDATED STATE: YES"
            if validation_state
            else "VALIDATED STATE: NO - UNVERIFIED CHANGE"
        )
        validation_color = "green" if validation_state else "red"
        validation_para = Paragraph(
            f'<b><font color="{validation_color}">{validation_text}</font></b>',
            bold_style,
        )
        story.append(validation_para)
        story.append(Spacer(1, 0.1 * inch))

        # Validated hash comparison
        validated_hash = HashVerifier.get_validated_hash()
        if validated_hash:
            story.append(
                Paragraph(f"<b>Validated Hash:</b> {validated_hash}", normal_style)
            )
            if engine_hash == validated_hash:
                story.append(
                    Paragraph(
                        '<font color="green">✓ Engine hash matches validated hash</font>',
                        normal_style,
                    )
                )
            else:
                story.append(
                    Paragraph(
                        '<font color="red">✗ Engine hash does NOT match validated hash</font>',
                        normal_style,
                    )
                )
        else:
            story.append(
                Paragraph(
                    '<font color="orange">⚠ No validated hash on record</font>',
                    normal_style,
                )
            )

        story.append(PageBreak())

        # ===== SECTION 2: CURRENT CALCULATION REPORT =====
        story.append(Paragraph("2. Current Calculation Report", heading_style))
        story.append(Spacer(1, 0.2 * inch))

        # Module and timestamp
        story.append(
            Paragraph(
                f"<b>Analysis Module:</b> {calculation_report.module}", normal_style
            )
        )
        story.append(
            Paragraph(
                f"<b>Calculation Time:</b> {calculation_report.timestamp}",
                normal_style,
            )
        )
        story.append(Spacer(1, 0.2 * inch))

        # Statistical method
        story.append(Paragraph("Statistical Method", heading2_style))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(calculation_report.method_path, normal_style))
        story.append(Spacer(1, 0.2 * inch))

        # Input parameters
        story.append(Paragraph("Input Parameters", heading2_style))
        story.append(Spacer(1, 0.1 * inch))

        input_data = []
        for key, value in calculation_report.inputs.items():
            formatted_key = key.replace("_", " ").title()
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

        # Calculated results
        story.append(Paragraph("Calculated Results", heading2_style))
        story.append(Spacer(1, 0.1 * inch))

        result_data = [
            [
                Paragraph("<b>Parameter</b>", bold_style),
                Paragraph("<b>Value</b>", bold_style),
                Paragraph("<b>Unit</b>", bold_style),
            ]
        ]

        for key, value in calculation_report.results.items():
            formatted_key = key.replace("_", " ").title()
            value_str = str(value)
            unit = ""

            result_data.append(
                [
                    Paragraph(formatted_key, normal_style),
                    Paragraph(value_str, normal_style),
                    Paragraph(unit, normal_style),
                ]
            )

        if len(result_data) > 1:
            result_table = Table(result_data, colWidths=[200, 150, 100])
            result_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 11),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                        ("ALIGN", (0, 1), (0, -1), "LEFT"),
                        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                        ("ALIGN", (2, 1), (2, -1), "LEFT"),
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

        story.append(PageBreak())

        # ===== SECTION 3: VALIDATION STATUS =====
        story.append(Paragraph("3. Validation Status", heading_style))
        story.append(Spacer(1, 0.2 * inch))

        # Check for latest validation certificate
        validation_cert_info = FullReportGenerator._get_latest_validation_info(
            validation_reports_dir
        )

        if validation_cert_info:
            story.append(
                Paragraph(
                    f"<b>Latest Validation Certificate:</b> {validation_cert_info['filename']}",
                    normal_style,
                )
            )
            story.append(
                Paragraph(
                    f"<b>Validation Date:</b> {validation_cert_info['date']}",
                    normal_style,
                )
            )
            story.append(Spacer(1, 0.1 * inch))
            story.append(
                Paragraph(
                    "The system has been validated according to IQ/OQ/PQ protocols. "
                    "See the validation certificate in the reports/validation/ directory "
                    "for complete test results and traceability matrix.",
                    normal_style,
                )
            )
        else:
            story.append(
                Paragraph(
                    '<font color="orange">⚠ No validation certificates found</font>',
                    normal_style,
                )
            )
            story.append(Spacer(1, 0.1 * inch))
            story.append(
                Paragraph(
                    "No validation certificates were found in the reports/validation/ directory. "
                    "Please run the full validation suite (IQ/OQ/PQ) to generate a validation certificate.",
                    normal_style,
                )
            )

        story.append(PageBreak())

        # ===== SECTION 4: AUDIT TRAIL =====
        story.append(Paragraph("4. Audit Trail (Session Logs)", heading_style))
        story.append(Spacer(1, 0.2 * inch))

        story.append(
            Paragraph(
                f"<b>Session ID:</b> {session_id}",
                normal_style,
            )
        )
        story.append(Spacer(1, 0.1 * inch))

        # Retrieve session logs
        session_logs = FullReportGenerator._get_session_logs(session_id, log_dir)

        if session_logs:
            story.append(
                Paragraph(
                    f"Found {len(session_logs)} log entries for this session:",
                    normal_style,
                )
            )
            story.append(Spacer(1, 0.1 * inch))

            # Create log table
            log_data = [
                [
                    Paragraph("<b>Timestamp</b>", bold_style),
                    Paragraph("<b>Event Type</b>", bold_style),
                    Paragraph("<b>Details</b>", bold_style),
                ]
            ]

            for log_entry in session_logs[:50]:  # Limit to first 50 entries
                log_data.append(
                    [
                        Paragraph(log_entry["timestamp"], normal_style),
                        Paragraph(log_entry["event_type"], normal_style),
                        Paragraph(log_entry["details"], normal_style),
                    ]
                )

            log_table = Table(log_data, colWidths=[1.5 * inch, 1.5 * inch, 3.5 * inch])
            log_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                        ("ALIGN", (0, 1), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -1), 9),
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
            story.append(log_table)

            if len(session_logs) > 50:
                story.append(Spacer(1, 0.1 * inch))
                story.append(
                    Paragraph(
                        f"<i>Note: Showing first 50 of {len(session_logs)} log entries. "
                        "See audit.log file for complete session history.</i>",
                        normal_style,
                    )
                )
        else:
            story.append(
                Paragraph(
                    '<font color="orange">⚠ No log entries found for this session</font>',
                    normal_style,
                )
            )
            story.append(Spacer(1, 0.1 * inch))
            story.append(
                Paragraph(
                    "No audit log entries were found for this session ID. "
                    "This may indicate that logging is not properly configured or "
                    "the session ID is incorrect.",
                    normal_style,
                )
            )

        # Footer
        story.append(Spacer(1, 0.3 * inch))
        footer_text = (
            "This comprehensive report combines the current calculation, validation status, "
            "and audit trail for complete QMS documentation. All sections are timestamped "
            "and traceable to the calculation engine hash for integrity verification."
        )
        story.append(Paragraph(footer_text, normal_style))

        # Build the PDF with page numbers
        doc.build(
            story,
            onFirstPage=FullReportGenerator._add_page_number,
            onLaterPages=FullReportGenerator._add_page_number,
        )

        # Get the PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    @staticmethod
    def _get_latest_validation_info(
        validation_reports_dir: str,
    ) -> dict[str, str] | None:
        """Get information about the latest validation certificate.

        Args:
            validation_reports_dir: Directory containing validation certificates

        Returns:
            Dictionary with 'filename' and 'date' keys, or None if no certificates found
        """
        validation_dir = Path(validation_reports_dir)

        if not validation_dir.exists():
            return None

        # Find all PDF files in validation directory
        pdf_files = list(validation_dir.glob("*.pdf"))

        if not pdf_files:
            return None

        # Sort by modification time (most recent first)
        latest_file = max(pdf_files, key=lambda p: p.stat().st_mtime)

        # Extract date from filename if possible (format: validation_certificate_YYYYMMDD_HHMMSS.pdf)
        filename = latest_file.name
        date_str = "Unknown"

        if "_" in filename:
            parts = filename.split("_")
            if len(parts) >= 3:
                # Try to parse date from filename
                try:
                    date_part = parts[-2]  # YYYYMMDD
                    time_part = parts[-1].replace(".pdf", "")  # HHMMSS
                    date_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
                except (IndexError, ValueError):
                    # Fall back to file modification time
                    from datetime import datetime

                    mtime = latest_file.stat().st_mtime
                    date_str = datetime.fromtimestamp(mtime).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

        return {"filename": filename, "date": date_str}

    @staticmethod
    def _get_session_logs(session_id: str, log_dir: str) -> list[dict[str, str]]:
        """Retrieve and parse audit log entries for a specific session.

        Args:
            session_id: User session identifier
            log_dir: Directory containing audit log files

        Returns:
            List of dictionaries with 'timestamp', 'event_type', and 'details' keys
        """
        log_path = Path(log_dir) / "audit.log"

        if not log_path.exists():
            return []

        session_logs = []

        try:
            with open(log_path, encoding="utf-8") as f:
                for line in f:
                    # Check if line contains the session ID
                    if session_id in line:
                        # Parse log line
                        # Format: [TIMESTAMP] [LEVEL] [SESSION_ID] [EVENT_TYPE] {context_json}
                        parsed = FullReportGenerator._parse_log_line(line)
                        if parsed:
                            session_logs.append(parsed)
        except Exception:
            # If there's any error reading logs, return empty list
            return []

        return session_logs

    @staticmethod
    def _parse_log_line(line: str) -> dict[str, str] | None:
        """Parse a single audit log line.

        Args:
            line: Raw log line string

        Returns:
            Dictionary with 'timestamp', 'event_type', and 'details' keys, or None if parsing fails
        """
        try:
            # Extract components using string parsing
            # Format: [TIMESTAMP] [LEVEL] [SESSION_ID] [EVENT_TYPE] {context_json}

            # Find the positions of brackets
            parts = line.split("] [")

            if len(parts) < 4:
                return None

            # Extract timestamp (remove leading '[')
            timestamp = parts[0].strip("[")

            # Extract event type (from 4th bracket pair)
            event_type_part = parts[3]
            # Split on '] ' to separate event_type from context
            event_type_split = event_type_part.split("] ", 1)

            if len(event_type_split) < 2:
                return None

            event_type = event_type_split[0]
            context_json = event_type_split[1]

            # Try to parse JSON context for better details
            import json

            try:
                context = json.loads(context_json)
                # Extract relevant details from context
                details_parts = []

                # Add calc_type if present
                if "calc_type" in context:
                    details_parts.append(f"Calc: {context['calc_type']}")

                # Add button_id if present
                if "button_id" in context:
                    details_parts.append(f"Button: {context['button_id']}")

                # Add field_id if present
                if "field_id" in context:
                    details_parts.append(f"Field: {context['field_id']}")

                # Add method if present
                if "method" in context:
                    details_parts.append(f"Method: {context['method']}")

                # Add error_message if present
                if "error_message" in context:
                    details_parts.append(f"Error: {context['error_message']}")

                # If no specific details, use first few keys
                if not details_parts:
                    for key in list(context.keys())[:3]:
                        if key != "timestamp":
                            details_parts.append(f"{key}: {context[key]}")

                details = (
                    ", ".join(details_parts) if details_parts else context_json[:100]
                )

            except json.JSONDecodeError:
                # If JSON parsing fails, use raw context
                details = context_json[:100]

            return {
                "timestamp": timestamp,
                "event_type": event_type,
                "details": details,
            }

        except Exception:
            return None

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
