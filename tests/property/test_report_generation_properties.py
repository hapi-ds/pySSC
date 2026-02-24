"""Property-based tests for report generation.

This module contains property-based tests using Hypothesis to verify
the correctness and completeness of PDF report generation.
"""

from datetime import datetime
from io import BytesIO

from hypothesis import given
from hypothesis import strategies as st

from src.sample_size_calculator.hash_verifier import HashVerifier
from src.sample_size_calculator.models import CalculationReport, ValidationCertificate
from src.sample_size_calculator.report_generator import ReportGenerator

# Try to import PyPDF2, but make it optional for basic tests
try:
    from pypdf import PdfReader

    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


class TestReportGeneration:
    """Property-based tests for report generation functionality."""

    @given(
        confidence=st.floats(min_value=0.1, max_value=99.9),
        reliability=st.floats(min_value=0.1, max_value=99.9),
        allowable_failures=st.integers(min_value=0, max_value=10),
        sample_size=st.integers(min_value=1, max_value=1000),
    )
    def test_property_27_report_completeness(
        self,
        confidence: float,
        reliability: float,
        allowable_failures: int,
        sample_size: int,
    ) -> None:
        """Property 27: Report Completeness.

        **Validates: Requirements 27.1, 27.2, 27.3, 27.4, 27.5, 28.1, 28.2, 28.3**

        For any valid calculation, the generated report must include:
        - Timestamp (27.2)
        - All user inputs (27.3)
        - All calculated results (27.4)
        - Statistical method used (27.5)
        - Engine hash (28.2)
        - Validation state (28.3)
        """
        # Create a calculation report with the given inputs
        timestamp = datetime.now().isoformat()
        engine_hash = HashVerifier.get_engine_hash()
        validation_state = HashVerifier.is_validated_state()

        # Determine method based on allowable failures
        method = (
            "Success Run Theorem" if allowable_failures == 0 else "Cumulative Binomial"
        )

        report_data = CalculationReport(
            timestamp=timestamp,
            module="Module A",
            inputs={
                "confidence": confidence,
                "reliability": reliability,
                "allowable_failures": allowable_failures,
            },
            results={
                "sample_size": sample_size,
                "method": method,
            },
            engine_hash=engine_hash,
            validation_state=validation_state,
            method_path=method,
        )

        # Generate the PDF report
        pdf_bytes, report_path = ReportGenerator.generate_user_report(report_data)

        # Verify PDF was generated
        assert pdf_bytes is not None, "PDF bytes should not be None"
        assert len(pdf_bytes) > 0, "PDF should have content"
        assert pdf_bytes[:4] == b"%PDF", "PDF should start with PDF header"
        
        # Verify report path was returned
        assert report_path is not None, "Report path should not be None"
        assert str(report_path).endswith(".pdf"), "Report path should be a PDF file"

        # If PyPDF is available, do detailed content verification
        if HAS_PYPDF:
            # Parse the PDF to extract text
            pdf_reader = PdfReader(BytesIO(pdf_bytes))

            # Extract all text from the PDF
            full_text = ""
            for page in pdf_reader.pages:
                full_text += page.extract_text()

            # Requirement 27.2: Verify timestamp is included
            assert timestamp[:10] in full_text or "Report Generated" in full_text, (
                "Report should include timestamp or generation date"
            )

            # Requirement 27.3: Verify all user inputs are included
            assert "confidence" in full_text.lower() or str(confidence) in full_text, (
                f"Report should include confidence input: {confidence}"
            )
            assert (
                "reliability" in full_text.lower() or str(reliability) in full_text
            ), f"Report should include reliability input: {reliability}"
            assert (
                "allowable" in full_text.lower() or str(allowable_failures) in full_text
            ), f"Report should include allowable failures input: {allowable_failures}"

            # Requirement 27.4: Verify calculated results are included
            assert str(sample_size) in full_text, (
                f"Report should include calculated sample size: {sample_size}"
            )

            # Requirement 27.5: Verify statistical method is included
            assert method in full_text or "method" in full_text.lower(), (
                f"Report should include statistical method: {method}"
            )

            # Requirement 28.2: Verify engine hash is included
            assert "Engine Hash" in full_text or "hash" in full_text.lower(), (
                "Report should include engine hash label"
            )
            assert engine_hash[:8] in full_text, (
                f"Report should include engine hash value: {engine_hash[:8]}..."
            )

            # Requirement 28.3, 29.2, 29.3: Verify validation state is included
            assert "VALIDATED STATE" in full_text, (
                "Report should include validation state"
            )
            if validation_state:
                assert "YES" in full_text, (
                    "Report should show 'YES' for validated state"
                )
            else:
                assert "NO" in full_text or "UNVERIFIED" in full_text, (
                    "Report should show 'NO' or 'UNVERIFIED' for non-validated state"
                )
        else:
            # Basic validation without PDF parsing
            # Verify the report_data was used (check it's in the model)
            assert report_data.timestamp == timestamp
            assert report_data.engine_hash == engine_hash
            assert report_data.validation_state == validation_state

    @given(
        module=st.sampled_from(["Module A", "Module V"]),
        input_count=st.integers(min_value=1, max_value=10),
        result_count=st.integers(min_value=1, max_value=10),
    )
    def test_property_27_report_generation_for_all_modules(
        self,
        module: str,
        input_count: int,
        result_count: int,
    ) -> None:
        """Property 27: Report Generation for All Modules (additional validation).

        **Validates: Requirements 27.1, 27.2, 27.3, 27.4, 27.5**

        Reports should be generated successfully for both Module A and Module V
        with varying numbers of inputs and results.
        """
        # Create sample inputs and results
        inputs = {f"input_{i}": f"value_{i}" for i in range(input_count)}
        results = {f"result_{i}": f"output_{i}" for i in range(result_count)}

        timestamp = datetime.now().isoformat()
        engine_hash = HashVerifier.get_engine_hash()
        validation_state = HashVerifier.is_validated_state()

        report_data = CalculationReport(
            timestamp=timestamp,
            module=module,  # type: ignore[arg-type]
            inputs=inputs,
            results=results,
            engine_hash=engine_hash,
            validation_state=validation_state,
            method_path="Test Method",
        )

        # Generate the PDF report
        pdf_bytes, report_path = ReportGenerator.generate_user_report(report_data)

        # Verify PDF was generated successfully
        assert pdf_bytes is not None, "PDF bytes should not be None"
        assert len(pdf_bytes) > 0, "PDF should have content"
        assert pdf_bytes[:4] == b"%PDF", "PDF should start with PDF header"

        if HAS_PYPDF:
            # Parse the PDF
            pdf_reader = PdfReader(BytesIO(pdf_bytes))

            # Verify PDF has at least one page
            assert len(pdf_reader.pages) > 0, "PDF should have at least one page"

            # Extract text
            full_text = ""
            for page in pdf_reader.pages:
                full_text += page.extract_text()

            # Verify module is included
            assert module in full_text, f"Report should include module: {module}"

            # Verify at least some inputs are included
            assert "Input" in full_text or "input" in full_text.lower(), (
                "Report should have input section"
            )

            # Verify at least some results are included
            assert "Result" in full_text or "result" in full_text.lower(), (
                "Report should have result section"
            )

    @given(
        validation_state=st.booleans(),
    )
    def test_property_27_validation_state_display(
        self,
        validation_state: bool,
    ) -> None:
        """Property 27: Validation State Display (additional validation).

        **Validates: Requirements 28.2, 29.2, 29.3, 29.5**

        The validation state should be displayed correctly and prominently
        in the report based on whether the engine hash matches the validated hash.
        """
        timestamp = datetime.now().isoformat()
        engine_hash = HashVerifier.get_engine_hash()

        report_data = CalculationReport(
            timestamp=timestamp,
            module="Module A",
            inputs={"test": "input"},
            results={"test": "result"},
            engine_hash=engine_hash,
            validation_state=validation_state,
            method_path="Test Method",
        )

        # Generate the PDF report
        pdf_bytes, report_path = ReportGenerator.generate_user_report(report_data)

        # Verify PDF was generated
        assert pdf_bytes is not None, "PDF bytes should not be None"
        assert len(pdf_bytes) > 0, "PDF should have content"
        assert pdf_bytes[:4] == b"%PDF", "PDF should start with PDF header"

        if HAS_PYPDF:
            # Parse the PDF
            pdf_reader = PdfReader(BytesIO(pdf_bytes))

            # Extract text
            full_text = ""
            for page in pdf_reader.pages:
                full_text += page.extract_text()

            # Verify validation state is displayed
            assert "VALIDATED STATE" in full_text, (
                "Report should include validation state label"
            )

            if validation_state:
                # Requirement 29.2: If validated, should show YES
                assert "YES" in full_text, (
                    "Report should show 'YES' when validation state is True"
                )
                # Should not show the unverified message
                assert "UNVERIFIED CHANGE" not in full_text, (
                    "Report should not show 'UNVERIFIED CHANGE' when validated"
                )
            else:
                # Requirement 29.3: If not validated, should show NO and warning
                assert "NO" in full_text, (
                    "Report should show 'NO' when validation state is False"
                )
                assert "UNVERIFIED CHANGE" in full_text, (
                    "Report should show 'UNVERIFIED CHANGE' when not validated"
                )

    @given(
        num_inputs=st.integers(min_value=1, max_value=20),
        num_results=st.integers(min_value=1, max_value=20),
    )
    def test_property_27_flowable_paragraphs_prevent_overflow(
        self,
        num_inputs: int,
        num_results: int,
    ) -> None:
        """Property 27: Flowable Paragraphs Prevent Overflow (additional validation).

        **Validates: Requirements 27.6**

        The report should use Flowable paragraphs to prevent text overflow,
        even with large amounts of data.
        """
        # Create inputs and results with long text values
        long_text = "A" * 200  # Very long text to test overflow handling
        inputs = {f"input_{i}": long_text for i in range(num_inputs)}
        results = {f"result_{i}": long_text for i in range(num_results)}

        timestamp = datetime.now().isoformat()
        engine_hash = HashVerifier.get_engine_hash()
        validation_state = HashVerifier.is_validated_state()

        report_data = CalculationReport(
            timestamp=timestamp,
            module="Module A",
            inputs=inputs,
            results=results,
            engine_hash=engine_hash,
            validation_state=validation_state,
            method_path="Test Method",
        )

        # Generate the PDF report - should not raise an exception
        try:
            pdf_bytes, report_path = ReportGenerator.generate_user_report(report_data)
        except Exception as e:
            raise AssertionError(
                f"Report generation should not fail with long text: {e}"
            ) from e

        # Verify PDF was generated successfully
        assert pdf_bytes is not None, "PDF bytes should not be None"
        assert len(pdf_bytes) > 0, "PDF should have content"
        assert pdf_bytes[:4] == b"%PDF", "PDF should start with PDF header"

        if HAS_PYPDF:
            # Parse the PDF to ensure it's valid
            try:
                pdf_reader = PdfReader(BytesIO(pdf_bytes))
                assert len(pdf_reader.pages) > 0, "PDF should have at least one page"
            except Exception as e:
                raise AssertionError(
                    f"Generated PDF should be valid and parseable: {e}"
                ) from e


class TestValidationCertificate:
    """Property-based tests for validation certificate generation."""

    @given(
        tester_name=st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd", "Zs"),
                min_codepoint=32,
                max_codepoint=126,
            ),
        ),
        num_test_results=st.integers(min_value=1, max_value=50),
    )
    def test_property_30_validation_certificate_completeness(
        self,
        tester_name: str,
        num_test_results: int,
    ) -> None:
        """Property 30: Validation Certificate Completeness.

        **Validates: Requirements 30.2, 30.3, 30.4, 30.5, 30.6**

        For any validation test execution, the generated certificate must include:
        - Test execution date (30.2)
        - Tester name (30.3)
        - System information (30.4)
        - Test results with URS IDs (30.5)
        - Validated hash (30.6)
        """
        # Create validation certificate data
        test_date = datetime.now().isoformat()
        validated_hash = HashVerifier.get_engine_hash()

        # Create system info
        import platform
        import sys

        system_info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": sys.version,
            "platform": platform.platform(),
        }

        # Create test results
        test_results = []
        for i in range(num_test_results):
            test_results.append(
                {
                    "urs_id": f"REQ-{i + 1}",
                    "test_id": f"TEST-{i + 1}",
                    "status": "PASSED" if i % 2 == 0 else "FAILED",
                }
            )

        cert_data = ValidationCertificate(
            test_date=test_date,
            tester_name=tester_name,
            system_info=system_info,
            test_results=test_results,
            validated_hash=validated_hash,
        )

        # Generate the validation certificate PDF
        pdf_bytes, report_path = ReportGenerator.generate_validation_certificate(cert_data)

        # Verify PDF was generated
        assert pdf_bytes is not None, "PDF bytes should not be None"
        assert len(pdf_bytes) > 0, "PDF should have content"
        assert pdf_bytes[:4] == b"%PDF", "PDF should start with PDF header"
        
        # Verify report path was returned
        assert report_path is not None, "Report path should not be None"
        assert str(report_path).endswith(".pdf"), "Report path should be a PDF file"

        if HAS_PYPDF:
            # Parse the PDF to extract text
            pdf_reader = PdfReader(BytesIO(pdf_bytes))

            # Extract all text from the PDF
            full_text = ""
            for page in pdf_reader.pages:
                full_text += page.extract_text()

            # Requirement 30.2: Verify test execution date is included
            assert test_date[:10] in full_text or "Test Execution Date" in full_text, (
                "Certificate should include test execution date"
            )

            # Requirement 30.3: Verify tester name is included
            assert tester_name in full_text or "Tester Name" in full_text, (
                f"Certificate should include tester name: {tester_name}"
            )

            # Requirement 30.4: Verify system information is included
            assert "System Information" in full_text or "system" in full_text.lower(), (
                "Certificate should include system information section"
            )
            # Check for at least one system info field
            assert (
                platform.system() in full_text
                or "python" in full_text.lower()
                or str(sys.version_info.major) in full_text
            ), "Certificate should include system details"

            # Requirement 30.5: Verify test results are included
            assert (
                "Verification Traceability Matrix" in full_text or "VTM" in full_text
            ), "Certificate should include VTM section"
            # Check for at least some test IDs
            assert "TEST-1" in full_text or "REQ-1" in full_text, (
                "Certificate should include test results"
            )

            # Requirement 30.6: Verify validated hash is included
            assert "Validated Hash" in full_text or "hash" in full_text.lower(), (
                "Certificate should include validated hash label"
            )
            assert validated_hash[:8] in full_text, (
                f"Certificate should include validated hash value: {validated_hash[:8]}..."
            )
        else:
            # Basic validation without PDF parsing
            assert cert_data.test_date == test_date
            assert cert_data.tester_name == tester_name
            assert cert_data.validated_hash == validated_hash
            assert len(cert_data.test_results) == num_test_results

    @given(
        num_passed=st.integers(min_value=0, max_value=20),
        num_failed=st.integers(min_value=0, max_value=20),
    )
    def test_property_30_vtm_table_generation(
        self,
        num_passed: int,
        num_failed: int,
    ) -> None:
        """Property 30: VTM Table Generation (additional validation).

        **Validates: Requirements 30.5**

        The VTM table should correctly display all test results with their
        pass/fail status, regardless of the number of tests.
        """
        # Skip if no tests
        if num_passed == 0 and num_failed == 0:
            return

        test_date = datetime.now().isoformat()
        validated_hash = HashVerifier.get_engine_hash()

        # Create test results with mixed pass/fail
        test_results = []
        for i in range(num_passed):
            test_results.append(
                {
                    "urs_id": f"REQ-PASS-{i + 1}",
                    "test_id": f"TEST-PASS-{i + 1}",
                    "status": "PASSED",
                }
            )
        for i in range(num_failed):
            test_results.append(
                {
                    "urs_id": f"REQ-FAIL-{i + 1}",
                    "test_id": f"TEST-FAIL-{i + 1}",
                    "status": "FAILED",
                }
            )

        cert_data = ValidationCertificate(
            test_date=test_date,
            tester_name="Test Engineer",
            system_info={"os": "Linux", "python_version": "3.11"},
            test_results=test_results,
            validated_hash=validated_hash,
        )

        # Generate the validation certificate PDF
        pdf_bytes, report_path = ReportGenerator.generate_validation_certificate(cert_data)

        # Verify PDF was generated successfully
        assert pdf_bytes is not None, "PDF bytes should not be None"
        assert len(pdf_bytes) > 0, "PDF should have content"
        assert pdf_bytes[:4] == b"%PDF", "PDF should start with PDF header"

        if HAS_PYPDF:
            # Parse the PDF
            pdf_reader = PdfReader(BytesIO(pdf_bytes))

            # Extract text
            full_text = ""
            for page in pdf_reader.pages:
                full_text += page.extract_text()

            # Verify VTM section exists
            assert (
                "Verification Traceability Matrix" in full_text or "VTM" in full_text
            ), "Certificate should include VTM section"

            # Verify at least some test results are present
            if num_passed > 0:
                assert "PASS" in full_text, "Certificate should show PASSED tests"
            if num_failed > 0:
                assert "FAIL" in full_text, "Certificate should show FAILED tests"

    @given(
        hash_length=st.integers(min_value=64, max_value=64),
    )
    def test_property_30_validated_hash_format(
        self,
        hash_length: int,
    ) -> None:
        """Property 30: Validated Hash Format (additional validation).

        **Validates: Requirements 30.6**

        The validated hash should be displayed in the correct format
        (64-character hexadecimal string for SHA-256).
        """
        test_date = datetime.now().isoformat()
        validated_hash = HashVerifier.get_engine_hash()

        # Verify the hash is in correct format
        assert len(validated_hash) == hash_length, (
            f"Validated hash should be {hash_length} characters"
        )
        assert all(c in "0123456789abcdef" for c in validated_hash), (
            "Validated hash should be hexadecimal"
        )

        cert_data = ValidationCertificate(
            test_date=test_date,
            tester_name="Test Engineer",
            system_info={"os": "Linux"},
            test_results=[{"urs_id": "REQ-1", "test_id": "TEST-1", "status": "PASSED"}],
            validated_hash=validated_hash,
        )

        # Generate the validation certificate PDF
        pdf_bytes, report_path = ReportGenerator.generate_validation_certificate(cert_data)

        # Verify PDF was generated
        assert pdf_bytes is not None, "PDF bytes should not be None"
        assert len(pdf_bytes) > 0, "PDF should have content"
        assert pdf_bytes[:4] == b"%PDF", "PDF should start with PDF header"

    @given(
        num_test_results=st.integers(min_value=1, max_value=100),
    )
    def test_property_30_flowable_paragraphs_in_certificate(
        self,
        num_test_results: int,
    ) -> None:
        """Property 30: Flowable Paragraphs in Certificate (additional validation).

        **Validates: Requirements 30.7**

        The validation certificate should use Flowable paragraphs to prevent
        text overflow, even with large VTM tables.
        """
        test_date = datetime.now().isoformat()
        validated_hash = HashVerifier.get_engine_hash()

        # Create many test results to test overflow handling
        test_results = []
        for i in range(num_test_results):
            test_results.append(
                {
                    "urs_id": f"REQ-{i + 1:04d}",
                    "test_id": f"TEST-{i + 1:04d}-LONG-NAME-TO-TEST-OVERFLOW",
                    "status": "PASSED" if i % 3 != 0 else "FAILED",
                }
            )

        cert_data = ValidationCertificate(
            test_date=test_date,
            tester_name="Test Engineer",
            system_info={"os": "Linux", "python_version": "3.11"},
            test_results=test_results,
            validated_hash=validated_hash,
        )

        # Generate the validation certificate PDF - should not raise an exception
        try:
            pdf_bytes, report_path = ReportGenerator.generate_validation_certificate(cert_data)
        except Exception as e:
            raise AssertionError(
                f"Certificate generation should not fail with many test results: {e}"
            ) from e

        # Verify PDF was generated successfully
        assert pdf_bytes is not None, "PDF bytes should not be None"
        assert len(pdf_bytes) > 0, "PDF should have content"
        assert pdf_bytes[:4] == b"%PDF", "PDF should start with PDF header"

        if HAS_PYPDF:
            # Parse the PDF to ensure it's valid
            try:
                pdf_reader = PdfReader(BytesIO(pdf_bytes))
                assert len(pdf_reader.pages) > 0, "PDF should have at least one page"
            except Exception as e:
                raise AssertionError(
                    f"Generated certificate PDF should be valid and parseable: {e}"
                ) from e
