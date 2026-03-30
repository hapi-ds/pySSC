"""PDF Report Content Validation Tests.

These tests validate that PDF reports contain correct calculated values,
not just UI interactions. They use parameterized inputs and verify
specific expected values in generated PDF reports.
"""

import re
from io import BytesIO
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect
from pypdf import PdfReader

MODULE_A_TEST_CASES = [
    pytest.param(
        {
            "confidence": 95.0,
            "reliability": 95.0,
            "allowable_failures": 0,
            "expected_sample_size": 59,
        },
        id="module_a_c95_r95_c0",
    ),
    pytest.param(
        {
            "confidence": 90.0,
            "reliability": 80.0,
            "allowable_failures": 0,
            "expected_sample_size": 11,
        },
        id="module_a_c95_r80_c0",
    ),
    pytest.param(
        {
            "confidence": 95.0,
            "reliability": 95.0,
            "allowable_failures": 1,
            "expected_sample_size": 93,
        },
        id="module_a_c95_r95_c1",
    ),
    pytest.param(
        {
            "confidence": 95.0,
            "reliability": 98.0,
            "allowable_failures": 0,
            "expected_sample_size": 149,
        },
        id="module_a_c95_r98_c0",
    ),
    pytest.param(
        {
            "confidence": 95.0,
            "reliability": 98.0,
            "allowable_failures": 1,
            "expected_sample_size": 236,
        },
        id="module_a_c95_r98_c1",
    ),
    pytest.param(
        {
            "confidence": 95.0,
            "reliability": 98.0,
            "allowable_failures": 2,
            "expected_sample_size": 313,
        },
        id="module_a_c95_r98_c2",
    ),
    pytest.param(
        {
            "confidence": 95.0,
            "reliability": 98.0,
            "allowable_failures": 3,
            "expected_sample_size": 386,
        },
        id="module_a_c95_r98_c3",
    ),
    pytest.param(
        {
            "confidence": 95.0,
            "reliability": 99.0,
            "allowable_failures": 0,
            "expected_sample_size": 299,
        },
        id="module_a_c95_r99_c0",
    ),
    pytest.param(
        {
            "confidence": 95.0,
            "reliability": 99.0,
            "allowable_failures": 1,
            "expected_sample_size": 473,
        },
        id="module_a_c95_r99_c1",
    ),
    pytest.param(
        {
            "confidence": 95.0,
            "reliability": 99.0,
            "allowable_failures": 2,
            "expected_sample_size": 628,
        },
        id="module_a_c95_r99_c2",
    ),
    pytest.param(
        {
            "confidence": 95.0,
            "reliability": 99.0,
            "allowable_failures": 3,
            "expected_sample_size": 773,
        },
        id="module_a_c95_r99_c3",
    ),
]


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract all text from a PDF byte stream."""
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        return "".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        pytest.fail(f"Failed to parse PDF: {e}")


@pytest.mark.pq
@pytest.mark.urs("URS-REP-01")
class TestModuleAPDFValidation:
    @pytest.mark.parametrize("test_case", MODULE_A_TEST_CASES)
    def test_module_a_pdf_contains_correct_sample_size(
        self,
        page: Page,
        tmp_path: Path,
        test_case: dict,
    ):
        """Test Module A PDF report contains the correct sample size."""
        base_url = "http://localhost:8080"

        page.goto(base_url)
        page.wait_for_load_state("networkidle")

        module_a_tab = page.locator('text="Module Attribute"').first
        module_a_tab.click()
        page.wait_for_timeout(500)

        confidence_input = page.locator('input[aria-label*="Confidence"]').first
        confidence_input.fill(str(test_case["confidence"]))

        reliability_input = page.locator('input[aria-label*="Reliability"]').first
        reliability_input.fill(str(test_case["reliability"]))

        allowable_failures_input = page.locator('input[aria-label*="Allowable"]').first
        allowable_failures_input.fill(str(test_case["allowable_failures"]))

        calculate_button = page.locator('button:has-text("Calculate")').first
        calculate_button.click()
        page.wait_for_timeout(1000)

        report_button = page.locator(
            'button:has-text("Generate"), button:has-text("Report")'
        ).first
        expect(report_button).to_be_enabled(timeout=3000)

        with page.expect_download(timeout=10000) as download_info:
            report_button.click()

        download = download_info.value
        pdf_path = tmp_path / "report.pdf"
        download.save_as(pdf_path)
        pdf_bytes = pdf_path.read_bytes()
        pdf_text = extract_text_from_pdf(pdf_bytes)

        assert str(test_case["expected_sample_size"]) in pdf_text, (
            f"PDF should contain sample size {test_case['expected_sample_size']}"
        )


# ============================================================================
# Module V PDF Validation Tests
# ============================================================================

MODULE_V_TEST_CASES = [
    pytest.param(
        {
            "spec_type": "Two-Sided",
            "lsl": 9.9,
            "usl": 10.1,
            "confidence": 95.0,
            "reliability": 95.0,
            "pilot_data": [10.015, 9.996, 10.019, 10.046, 9.993, 10.022, 10.005, 9.997, 9.991, 9.956, 9.978, 9.986],
            "Required Sample Size": 7,
            "Pass_Fail": "Pass",
        },
        id="module_v_normal_two_sided_pass",
    ),
    pytest.param(
        {
            "spec_type": "One-Sided",
            "lsl": 9.5,
            "usl": None,
            "confidence": 95.0,
            "reliability": 95.0,
            "pilot_data": [10.015, 9.996, 10.019, 10.046, 9.993, 10.022, 10.005, 9.997, 9.991, 9.956],
            "Required Sample Size": 3,
            "Pass_Fail": "Pass",
        },
        id="module_v_normal_one_sided",
    ),
]


@pytest.mark.pq
@pytest.mark.urs("URS-REP-01")
class TestModuleVPDFValidation:
    @pytest.mark.parametrize("test_case", MODULE_V_TEST_CASES)
    def test_module_v_pdf_contains_confidence_reliability(
        self,
        page: Page,
        tmp_path: Path,
        test_case: dict,
    ):
        """Test Module V PDF report contains input parameters."""
        base_url = "http://localhost:8080"

        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        module_v_tab = page.locator('text="Module Variable"').first
        module_v_tab.click()
        page.wait_for_timeout(500)

        spec_type_radio = page.locator(
            f'.q-radio:has-text("{test_case["spec_type"]}")'
        ).first
        spec_type_radio.click()

        page.locator('input[aria-label*="LSL"]').fill(str(test_case["lsl"]))
        if test_case["usl"] is not None:
            page.locator('input[aria-label*="USL"]').fill(str(test_case["usl"]))

        page.locator('input[aria-label*="Confidence"]').fill(
            str(test_case["confidence"])
        )
        page.locator('input[aria-label*="Reliability"]').fill(
            str(test_case["reliability"])
        )

        pilot_data_str = ", ".join(str(x) for x in test_case["pilot_data"])
        page.locator(
            'textarea[aria-label*="Pilot"], textarea[placeholder*="data"]'
        ).first.fill(pilot_data_str)

        page.locator('button:has-text("Analyze")').first.click()
        page.wait_for_timeout(2000)
        page.locator(
            'button:has-text("Process"), button:has-text("Normality")'
        ).first.click()
        page.wait_for_timeout(2000)
        page.locator(
            'button:has-text("Required"), button:has-text("required")'
        ).first.click()
        page.wait_for_timeout(2000)

        # Phase 4
        page.locator(
            'button:has-text("Tolerance"), button:has-text("Tolerance")'
        ).first.click()
        page.wait_for_timeout(2000)

        report_button = page.locator(
            'button:has-text("Generate"), button:has-text("Report")'
        ).first
        expect(report_button).to_be_enabled(timeout=3000)
        with page.expect_download(timeout=10000) as download_info:
            report_button.click()

        download = download_info.value
        pdf_path = tmp_path / "report.pdf"
        download.save_as(pdf_path)
        pdf_bytes = pdf_path.read_bytes()
        pdf_text = extract_text_from_pdf(pdf_bytes)

        # Verify PDF contains Pass/Fail result
        pass_fail = test_case.get("Pass_Fail")
        assert f"Pass Fail\n{pass_fail}" in pdf_text, (
            f"PDF should contain pass/fail result {test_case['Pass_Fail']}"
        )

        # Verify PDF contains confidence and reliability values
        assert str(test_case["confidence"]) in pdf_text, (
            f"PDF should contain confidence {test_case['confidence']}"
        )
        assert str(test_case["reliability"]) in pdf_text, (
            f"PDF should contain reliability {test_case['reliability']}"
        )
        
        # Verify specific values from Calculated Results table
        required_sample_size = test_case.get("Required Sample Size")
        # need more flexible check because of possible line breaks
        pattern = rf"Required\s+Sample\s+Size\s+{required_sample_size}"

        if required_sample_size is not None:
            assert re.search(pattern, pdf_text), (
                f"PDF should contain 'Required Sample Size' with value {required_sample_size}"
            )
