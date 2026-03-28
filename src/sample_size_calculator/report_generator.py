"""PDF report generation using ReportLab with page numbering."""

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
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
from sample_size_calculator.version import __version__


class NumberedCanvas(canvas.Canvas):
    """Canvas subclass that tracks pages and displays 'page x of y' format."""

    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._codes = []

    def showPage(self):
        self._codes.append({"code": self._code, "stack": self._codeStack})
        self._startPage()

    def save(self):
        """Add page info to each page (page x of y)"""
        self._pageNumber = 0
        for code in self._codes:
            self._code = code["code"]
            self._codeStack = code["stack"]
            self.setFont("Helvetica", 7)
            self.drawRightString(200 * mm, 20 * mm,
                "page %(this)i of %(total)i" % {
                   'this': self._pageNumber + 1,
                   'total': len(self._codes),
                }
            )
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)


class ReportGenerator:
    """Generates PDF reports using ReportLab with page numbering."""

    @staticmethod
    def generate_user_report(report_data: CalculationReport) -> tuple[bytes, Path]:
        """Generate user calculation report PDF."""
        ensure_report_directories()
        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        story = []
        styles = getSampleStyleSheet()
        title_style = styles["Title"]
        heading_style = styles["Heading2"]
        normal_style = styles["Normal"]

        bold_style = ParagraphStyle("Bold", parent=normal_style, fontName="Helvetica-Bold")

        story.append(Paragraph("Sample Size Calculator", title_style))
        story.append(Paragraph("Calculation Report", heading_style))
        story.append(Spacer(1, 6 * mm))

        story.append(Paragraph(f"<b>Report Generated:</b> {report_data.timestamp}", normal_style))
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(f"<b>Analysis Module:</b> {report_data.module}", normal_style))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(f"<b>Software Version:</b> v{report_data.version}", normal_style))
        story.append(Spacer(1, 6 * mm))

        story.append(Paragraph("Engine Integrity Verification", heading_style))
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(f"<b>Engine Hash:</b> {report_data.engine_hash}", normal_style))
        story.append(Spacer(1, 2 * mm))

        validation_text = (
            "VALIDATED STATE: YES"
            if report_data.validation_state
            else "VALIDATED STATE: NO - UNVERIFIED CHANGE"
        )
        validation_color = "green" if report_data.validation_state else "red"
        story.append(Paragraph(f'<b><font color="{validation_color}">{validation_text}</font></b>', bold_style))
        story.append(Spacer(1, 6 * mm))

        story.append(Paragraph("Statistical Method", heading_style))
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(report_data.method_path, normal_style))
        story.append(Spacer(1, 6 * mm))

        story.append(Paragraph("Input Parameters", heading_style))
        story.append(Spacer(1, 3 * mm))

        input_data = []
        for key, value in report_data.inputs.items():
            formatted_key = key.replace("_", " ").title()
            input_data.append([Paragraph(f"<b>{formatted_key}</b>", normal_style), Paragraph(str(value), normal_style)])

        if input_data:
            input_table = Table(input_data, colWidths=[100, 150])
            input_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(input_table)
        story.append(Spacer(1, 6 * mm))

        story.append(Paragraph("Calculated Results", heading_style))
        story.append(Spacer(1, 3 * mm))

        result_data = [[Paragraph("<b>Parameter</b>", bold_style), Paragraph("<b>Value</b>", bold_style)]]
        for key, value in report_data.results.items():
            formatted_key = key.replace("_", " ").title()
            if isinstance(value, float):
                value_str = f"{value:.4f}".rstrip("0").rstrip(".")
            elif isinstance(value, dict):
                value_str = ", ".join(f"{k}: {v}" for k, v in value.items())
            else:
                value_str = str(value)
            result_data.append([Paragraph(formatted_key, normal_style), Paragraph(value_str, normal_style)])

        if len(result_data) > 1:
            result_table = Table(result_data, colWidths=[100, 150])
            result_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(result_table)
        story.append(Spacer(1, 6 * mm))

        story.append(Paragraph("This report was generated by the Sample Size Calculator application.", normal_style))

        doc.build(story, canvasmaker=NumberedCanvas)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        report_path = get_calculation_report_path()
        saved_path = save_report(pdf_bytes, report_path)

        try:
            from sample_size_calculator.pdf_signature import PDFSignature
            signature = PDFSignature.sign_pdf(pdf_bytes, report_data.engine_hash)
            PDFSignature.save_signature(saved_path, signature)
        except Exception:
            pass

        return pdf_bytes, saved_path

    @staticmethod
    def generate_validation_certificate(
        cert_data: ValidationCertificate,
        coverage_metrics: dict | None = None,
    ) -> tuple[bytes, Path]:
        """Generate validation certificate PDF."""
        ensure_report_directories()
        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        story = []
        styles = getSampleStyleSheet()
        title_style = styles["Title"]
        heading_style = styles["Heading2"]
        heading3_style = styles["Heading3"]
        normal_style = styles["Normal"]

        story.append(Paragraph("Sample Size Calculator", title_style))
        story.append(Paragraph("Validation Certificate", heading_style))
        story.append(Spacer(1, 9 * mm))

        story.append(Paragraph(f"<b>Test Execution Date:</b> {cert_data.test_date}", normal_style))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(f"<b>Software Version:</b> v{__version__}", normal_style))
        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph(f"<b>Tester Name:</b> {cert_data.tester_name}", normal_style))
        story.append(Spacer(1, 6 * mm))

        story.append(Paragraph("System Information", heading3_style))
        story.append(Spacer(1, 3 * mm))

        sys_info_data = []
        for key, value in cert_data.system_info.items():
            formatted_key = key.replace("_", " ").title()
            sys_info_data.append([Paragraph(f"<b>{formatted_key}</b>", normal_style), Paragraph(str(value), normal_style)])

        if sys_info_data:
            sys_info_table = Table(sys_info_data, colWidths=[100, 150])
            sys_info_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(sys_info_table)

        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph("Validated Calculation Engine", heading3_style))
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(f"<b>Validated Hash:</b> {cert_data.validated_hash}", normal_style))

        def group_test_results_by_test_id(results):
            grouped = {}
            for result in results:
                test_id = result.get("test_id", "N/A")
                if test_id not in grouped:
                    grouped[test_id] = {"test_id": test_id, "urs_ids": [], "status": result.get("status", "N/A")}
                urs_id = result.get("urs_id", "N/A")
                if urs_id not in grouped[test_id]["urs_ids"]:
                    grouped[test_id]["urs_ids"].append(urs_id)
            return [{"test_id": data["test_id"], "urs_id": ", ".join(data["urs_ids"]), "status": data["status"]} for data in grouped.values()]

        iq_results = group_test_results_by_test_id([r for r in cert_data.test_results if "test_iq.py" in r.get("test_id", "")])
        oq_results = group_test_results_by_test_id([r for r in cert_data.test_results if "test_oq.py" in r.get("test_id", "")])
        pq_results = group_test_results_by_test_id([r for r in cert_data.test_results if "test_pq.py" in r.get("test_id", "")])

        story.append(PageBreak())
        story.append(Paragraph("CHAPTER 1: INSTALLATION QUALIFICATION (IQ)", heading_style))
        story.append(Spacer(1, 6 * mm))

        if iq_results:
            iq_data = [[Paragraph("<b>URS ID</b>", normal_style), Paragraph("<b>Test ID</b>", normal_style), Paragraph("<b>Status</b>", normal_style)]]
            for test_result in iq_results:
                status = test_result.get("status", "N/A")
                if status.upper() in ["PASS", "PASSED"]:
                    status_text = f'<font color="green"><b>{status}</b></font>'
                elif status.upper() in ["FAIL", "FAILED"]:
                    status_text = f'<font color="red"><b>{status}</b></font>'
                else:
                    status_text = status
                iq_data.append([Paragraph(test_result.get("urs_id", ""), normal_style), Paragraph(test_result.get("test_id", ""), normal_style), Paragraph(status_text, normal_style)])

            iq_table = Table(iq_data, colWidths=[80, 100, 60])
            iq_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(iq_table)
        else:
            story.append(Paragraph("No IQ tests found.", normal_style))

        story.append(PageBreak())
        story.append(Paragraph("CHAPTER 2: OPERATIONAL QUALIFICATION (OQ)", heading_style))
        story.append(Spacer(1, 6 * mm))

        if oq_results:
            oq_data = [[Paragraph("<b>URS ID</b>", normal_style), Paragraph("<b>Test ID</b>", normal_style), Paragraph("<b>Status</b>", normal_style)]]
            for test_result in oq_results:
                status = test_result.get("status", "N/A")
                if status.upper() in ["PASS", "PASSED"]:
                    status_text = f'<font color="green"><b>{status}</b></font>'
                elif status.upper() in ["FAIL", "FAILED"]:
                    status_text = f'<font color="red"><b>{status}</b></font>'
                else:
                    status_text = status
                oq_data.append([Paragraph(test_result.get("urs_id", ""), normal_style), Paragraph(test_result.get("test_id", ""), normal_style), Paragraph(status_text, normal_style)])

            oq_table = Table(oq_data, colWidths=[80, 100, 60])
            oq_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(oq_table)
        else:
            story.append(Paragraph("No OQ tests found.", normal_style))

        story.append(PageBreak())
        story.append(Paragraph("CHAPTER 3: PERFORMANCE QUALIFICATION (PQ)", heading_style))
        story.append(Spacer(1, 6 * mm))

        if pq_results:
            pq_data = [[Paragraph("<b>URS ID</b>", normal_style), Paragraph("<b>Test ID</b>", normal_style), Paragraph("<b>Status</b>", normal_style)]]
            for test_result in pq_results:
                status = test_result.get("status", "N/A")
                if status.upper() in ["PASS", "PASSED"]:
                    status_text = f'<font color="green"><b>{status}</b></font>'
                elif status.upper() in ["FAIL", "FAILED"]:
                    status_text = f'<font color="red"><b>{status}</b></font>'
                else:
                    status_text = status
                pq_data.append([Paragraph(test_result.get("urs_id", ""), normal_style), Paragraph(test_result.get("test_id", ""), normal_style), Paragraph(status_text, normal_style)])

            pq_table = Table(pq_data, colWidths=[80, 100, 60])
            pq_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(pq_table)
        else:
            story.append(Paragraph("No PQ tests found.", normal_style))

        total_tests = len(iq_results) + len(oq_results) + len(pq_results)
        total_passed = sum(1 for r in iq_results + oq_results + pq_results if r.get("status", "").upper() in ["PASS", "PASSED"])
        total_failed = total_tests - total_passed

        story.append(PageBreak())
        story.append(Paragraph("CHAPTER 4: VALIDATION SUMMARY", heading_style))
        story.append(Spacer(1, 6 * mm))

        story.append(Paragraph("<b>Overall Test Results:</b>", normal_style))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(f"Total Tests: {total_tests}", normal_style))
        story.append(Paragraph(f"Passed: {total_passed}", normal_style))
        story.append(Paragraph(f"Failed: {total_failed}", normal_style))

        validation_status = "PASSED" if total_failed == 0 else "FAILED"
        status_color = "green" if total_failed == 0 else "red"
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(f'<b>Validation Status:</b> <font color="{status_color}"><b>{validation_status}</b></font>', heading3_style))

        doc.build(story, canvasmaker=NumberedCanvas)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        report_path = get_validation_report_path()
        save_report(pdf_bytes, report_path)

        return pdf_bytes, report_path
