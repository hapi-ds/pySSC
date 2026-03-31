"""Unit tests for pdf_report module."""

from pathlib import Path

from sample_size_calculator.pdf_report import NumberedCanvas, PDFReportTemplate


class TestNumberedCanvas:
    """Test NumberedCanvas page numbering functionality."""

    def test_init_sets_up_canvas(self, tmp_path):
        output_path = tmp_path / "test.pdf"
        canvas = NumberedCanvas(str(output_path))
        
        assert canvas is not None
        assert hasattr(canvas, "_codes")
        assert isinstance(canvas._codes, list)

    def test_showpage_adds_to_codes(self, tmp_path):
        output_path = tmp_path / "test.pdf"
        canvas = NumberedCanvas(str(output_path))
        initial_codes_count = len(canvas._codes)
        
        canvas.showPage()
        
        assert len(canvas._codes) > initial_codes_count

    def test_save_adds_page_numbering(self, tmp_path):
        output_path = tmp_path / "test.pdf"
        
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate
        
        doc = SimpleDocTemplate(str(output_path), pagesize=A4)
        
        story = []
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph
        
        styles = getSampleStyleSheet()
        story.append(Paragraph("Test Page 1", styles["Normal"]))
        
        doc.build(story, canvasmaker=NumberedCanvas)
        
        assert output_path.exists()
        file_size = output_path.stat().st_size
        assert file_size > 0
        pdf_content = output_path.read_bytes()
        assert pdf_content[:4] == b"%PDF"

    def test_save_with_multiple_pages(self, tmp_path):
        output_path = tmp_path / "test_multi_page.pdf"
        
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import PageBreak, SimpleDocTemplate
        
        doc = SimpleDocTemplate(str(output_path), pagesize=A4)
        
        story = []
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph
        
        styles = getSampleStyleSheet()
        story.append(Paragraph("Page 1", styles["Normal"]))
        story.append(PageBreak())
        story.append(Paragraph("Page 2", styles["Normal"]))
        
        doc.build(story, canvasmaker=NumberedCanvas)
        
        assert output_path.exists()
        pdf_content = output_path.read_bytes()
        assert b"page" in pdf_content.lower()


class TestPDFReportTemplate:
    """Test PDFReportTemplate report generation functionality."""

    def test_init_sets_properties(self):
        template = PDFReportTemplate(
            title="Test Title",
            subtitle="Test Subtitle",
            author="Test Author",
        )
        
        assert template.title == "Test Title"
        assert template.subtitle == "Test Subtitle"
        assert template.author == "Test Author"

    def test_init_with_defaults(self):
        template = PDFReportTemplate()
        
        assert template.title == "Sample Size Calculator"
        assert template.subtitle == ""
        assert template.author == "Sample Size Calculator"

    def test_create_standard_header_no_title(self, tmp_path):
        template = PDFReportTemplate(title="", subtitle="", author="")
        header_elements = template.create_standard_header()
        
        assert isinstance(header_elements, list)

    def test_create_standard_header_with_subtitle(self, tmp_path):
        template = PDFReportTemplate(
            title="Main Title",
            subtitle="Detailed Subtitle",
            author="Author Name",
        )
        
        header_elements = template.create_standard_header()
        
        assert isinstance(header_elements, list)
        assert len(header_elements) > 0

    def test_create_standard_footer(self):
        template = PDFReportTemplate(title="Test Title", subtitle="Test Subtitle")
        footer_elements = template.create_standard_footer()
        
        assert isinstance(footer_elements, list)
        assert len(footer_elements) > 0

    def test_generate_report_basic(self, tmp_path):
        output_path = tmp_path / "basic_report.pdf"
        
        template = PDFReportTemplate(title="Basic Report")
        
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph
        
        styles = getSampleStyleSheet()
        elements = [Paragraph("Test Content", styles["Normal"])]
        
        pdf_bytes, saved_path = template.generate_report(elements, str(output_path))
        
        assert output_path.exists()
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"
        assert saved_path == str(output_path)

    def test_generate_report_with_multiple_elements(self, tmp_path):
        output_path = tmp_path / "multi_element_report.pdf"
        
        template = PDFReportTemplate(title="Multi-Element Report")
        
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, Spacer
        
        styles = getSampleStyleSheet()
        elements = [
            Paragraph("Header", styles["Heading1"]),
            Spacer(1, 20),
            Paragraph("Content Line 1", styles["Normal"]),
            Spacer(1, 20),
            Paragraph("Content Line 2", styles["Normal"]),
        ]
        
        pdf_bytes, saved_path = template.generate_report(elements, str(output_path))
        
        assert output_path.exists()
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_report_empty_elements(self, tmp_path):
        output_path = tmp_path / "empty_report.pdf"
        
        template = PDFReportTemplate(title="Empty Report")
        
        elements = []
        
        pdf_bytes, saved_path = template.generate_report(elements, str(output_path))
        
        assert output_path.exists()
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_report_large_content(self, tmp_path):
        output_path = tmp_path / "large_report.pdf"
        
        template = PDFReportTemplate(title="Large Report")
        
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph
        
        styles = getSampleStyleSheet()
        elements = [Paragraph(f"Content Line {i}", styles["Normal"]) for i in range(100)]
        
        pdf_bytes, saved_path = template.generate_report(elements, str(output_path))
        
        assert output_path.exists()
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_report_preserves_output_path(self, tmp_path):
        output_path = tmp_path / "path_test.pdf"
        
        template = PDFReportTemplate(title="Path Test")
        
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph
        
        styles = getSampleStyleSheet()
        elements = [Paragraph("Test", styles["Normal"])]
        
        pdf_bytes, saved_path = template.generate_report(elements, str(output_path))
        
        assert saved_path == str(output_path)
        assert Path(saved_path).exists()
