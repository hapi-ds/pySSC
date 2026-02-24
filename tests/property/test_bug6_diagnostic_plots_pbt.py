"""Property-based tests for Bug 6: Normality diagnostic plots displayed.

This module contains property-based tests that verify Bug 6 fix works correctly
across a wide range of inputs. Bug 6 was about missing normality diagnostic plots
(Q-Q, P-P, I-MR) in Phase 2 normality testing.

**Property 1: Expected Behavior** - Normality Diagnostic Plots Displayed

For any Phase 2 normality testing event, the fixed UI SHALL display Q-Q plot,
P-P plot, and I-MR chart alongside the Shapiro-Wilk p-value to help users assess
normality visually.

**Validates: Requirement 2.6**
"""

import base64

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.sample_size_calculator.ui_controller import UIController


class TestBug6DiagnosticPlotsProperty:
    """Property-based tests for Bug 6: Normality diagnostic plots displayed.
    
    **Validates: Requirement 2.6**
    """

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=5,
            max_size=100,
        ),
    )
    @settings(deadline=5000, max_examples=100)
    def test_qq_plot_generation_property(self, data: list[float]) -> None:
        """Property 1: Q-Q plot is generated for all datasets.
        
        This property-based test generates random datasets and verifies that
        the _generate_qq_plot method produces a valid base64-encoded PNG image
        for all inputs.
        
        **Validates: Requirement 2.6**
        """
        # Create UIController instance
        controller = UIController()
        
        # Execute: Generate Q-Q plot
        qq_plot_src = controller._generate_qq_plot(data)
        
        # Verify: Result is a valid base64 data URI
        assert qq_plot_src.startswith("data:image/png;base64,"), (
            "Q-Q plot should be a base64-encoded PNG data URI"
        )
        
        # Verify: Base64 data is valid
        base64_data = qq_plot_src.split(",")[1]
        try:
            decoded = base64.b64decode(base64_data)
            assert len(decoded) > 0, "Q-Q plot image data should not be empty"
        except Exception as e:
            pytest.fail(f"Q-Q plot base64 data is invalid: {e}")
        
        # Verify: Decoded data is a valid PNG
        assert decoded[:8] == b'\x89PNG\r\n\x1a\n', "Q-Q plot should be a valid PNG image"

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=5,
            max_size=100,
        ),
    )
    @settings(deadline=5000, max_examples=100)
    def test_pp_plot_generation_property(self, data: list[float]) -> None:
        """Property 1: P-P plot is generated for all datasets.
        
        This property-based test generates random datasets and verifies that
        the _generate_pp_plot method produces a valid base64-encoded PNG image
        for all inputs.
        
        **Validates: Requirement 2.6**
        """
        # Create UIController instance
        controller = UIController()
        
        # Execute: Generate P-P plot
        pp_plot_src = controller._generate_pp_plot(data)
        
        # Verify: Result is a valid base64 data URI
        assert pp_plot_src.startswith("data:image/png;base64,"), (
            "P-P plot should be a base64-encoded PNG data URI"
        )
        
        # Verify: Base64 data is valid
        base64_data = pp_plot_src.split(",")[1]
        try:
            decoded = base64.b64decode(base64_data)
            assert len(decoded) > 0, "P-P plot image data should not be empty"
        except Exception as e:
            pytest.fail(f"P-P plot base64 data is invalid: {e}")
        
        # Verify: Decoded data is a valid PNG
        assert decoded[:8] == b'\x89PNG\r\n\x1a\n', "P-P plot should be a valid PNG image"

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=5,
            max_size=100,
        ),
    )
    @settings(deadline=5000, max_examples=100)
    def test_imr_chart_generation_property(self, data: list[float]) -> None:
        """Property 1: I-MR chart is generated for all datasets.
        
        This property-based test generates random datasets and verifies that
        the _generate_imr_chart method produces a valid base64-encoded PNG image
        for all inputs.
        
        **Validates: Requirement 2.6**
        """
        # Create UIController instance
        controller = UIController()
        
        # Execute: Generate I-MR chart
        imr_plot_src = controller._generate_imr_chart(data)
        
        # Verify: Result is a valid base64 data URI
        assert imr_plot_src.startswith("data:image/png;base64,"), (
            "I-MR chart should be a base64-encoded PNG data URI"
        )
        
        # Verify: Base64 data is valid
        base64_data = imr_plot_src.split(",")[1]
        try:
            decoded = base64.b64decode(base64_data)
            assert len(decoded) > 0, "I-MR chart image data should not be empty"
        except Exception as e:
            pytest.fail(f"I-MR chart base64 data is invalid: {e}")
        
        # Verify: Decoded data is a valid PNG
        assert decoded[:8] == b'\x89PNG\r\n\x1a\n', "I-MR chart should be a valid PNG image"

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=5,
            max_size=50,
        ),
    )
    @settings(deadline=5000, max_examples=80)
    def test_all_three_plots_generated_property(self, data: list[float]) -> None:
        """Property 1: All three diagnostic plots are generated for all datasets.
        
        This test verifies that all three diagnostic plots (Q-Q, P-P, I-MR) can be
        generated successfully for any dataset.
        
        **Validates: Requirement 2.6**
        """
        # Create UIController instance
        controller = UIController()
        
        # Execute: Generate all three plots
        qq_plot_src = controller._generate_qq_plot(data)
        pp_plot_src = controller._generate_pp_plot(data)
        imr_plot_src = controller._generate_imr_chart(data)
        
        # Verify: All three plots are valid base64 data URIs
        assert qq_plot_src.startswith("data:image/png;base64,"), "Q-Q plot should be valid"
        assert pp_plot_src.startswith("data:image/png;base64,"), "P-P plot should be valid"
        assert imr_plot_src.startswith("data:image/png;base64,"), "I-MR chart should be valid"
        
        # Verify: All three plots have different content (not identical)
        qq_data = qq_plot_src.split(",")[1]
        pp_data = pp_plot_src.split(",")[1]
        imr_data = imr_plot_src.split(",")[1]
        
        # Plots should be different (different visualizations)
        assert qq_data != pp_data, "Q-Q and P-P plots should be different"
        assert qq_data != imr_data, "Q-Q and I-MR plots should be different"
        assert pp_data != imr_data, "P-P and I-MR plots should be different"

    @given(
        data=st.lists(
            st.floats(min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=5,
            max_size=50,
        ),
    )
    @settings(deadline=5000, max_examples=80)
    def test_plots_with_positive_data(self, data: list[float]) -> None:
        """Property 1: Diagnostic plots work with positive data.
        
        This test verifies that all diagnostic plots can be generated for
        positive-only datasets.
        
        **Validates: Requirement 2.6**
        """
        # Create UIController instance
        controller = UIController()
        
        # Execute: Generate all three plots
        qq_plot_src = controller._generate_qq_plot(data)
        pp_plot_src = controller._generate_pp_plot(data)
        imr_plot_src = controller._generate_imr_chart(data)
        
        # Verify: All plots generated successfully
        assert qq_plot_src.startswith("data:image/png;base64,")
        assert pp_plot_src.startswith("data:image/png;base64,")
        assert imr_plot_src.startswith("data:image/png;base64,")

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=-0.1, allow_nan=False, allow_infinity=False),
            min_size=5,
            max_size=50,
        ),
    )
    @settings(deadline=5000, max_examples=80)
    def test_plots_with_negative_data(self, data: list[float]) -> None:
        """Property 1: Diagnostic plots work with negative data.
        
        This test verifies that all diagnostic plots can be generated for
        negative-only datasets.
        
        **Validates: Requirement 2.6**
        """
        # Create UIController instance
        controller = UIController()
        
        # Execute: Generate all three plots
        qq_plot_src = controller._generate_qq_plot(data)
        pp_plot_src = controller._generate_pp_plot(data)
        imr_plot_src = controller._generate_imr_chart(data)
        
        # Verify: All plots generated successfully
        assert qq_plot_src.startswith("data:image/png;base64,")
        assert pp_plot_src.startswith("data:image/png;base64,")
        assert imr_plot_src.startswith("data:image/png;base64,")

    @given(
        data_size=st.integers(min_value=5, max_value=100),
    )
    @settings(deadline=5000, max_examples=80)
    def test_plots_with_various_data_sizes(self, data_size: int) -> None:
        """Property 1: Diagnostic plots work with various data sizes.
        
        This test verifies that all diagnostic plots can be generated for
        datasets of various sizes.
        
        **Validates: Requirement 2.6**
        """
        # Generate data with specified size
        np.random.seed(data_size)
        data = np.random.normal(12.0, 1.0, data_size).tolist()
        
        # Create UIController instance
        controller = UIController()
        
        # Execute: Generate all three plots
        qq_plot_src = controller._generate_qq_plot(data)
        pp_plot_src = controller._generate_pp_plot(data)
        imr_plot_src = controller._generate_imr_chart(data)
        
        # Verify: All plots generated successfully
        assert qq_plot_src.startswith("data:image/png;base64,")
        assert pp_plot_src.startswith("data:image/png;base64,")
        assert imr_plot_src.startswith("data:image/png;base64,")

    @given(
        mean=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        std=st.floats(min_value=0.1, max_value=50.0, allow_nan=False, allow_infinity=False),
    )
    @settings(deadline=5000, max_examples=80)
    def test_plots_with_various_distributions(self, mean: float, std: float) -> None:
        """Property 1: Diagnostic plots work with various normal distributions.
        
        This test verifies that all diagnostic plots can be generated for
        datasets with different means and standard deviations.
        
        **Validates: Requirement 2.6**
        """
        # Generate data with specified distribution
        np.random.seed(hash((mean, std)) % (2**32))
        data = np.random.normal(mean, std, 30).tolist()
        
        # Create UIController instance
        controller = UIController()
        
        # Execute: Generate all three plots
        qq_plot_src = controller._generate_qq_plot(data)
        pp_plot_src = controller._generate_pp_plot(data)
        imr_plot_src = controller._generate_imr_chart(data)
        
        # Verify: All plots generated successfully
        assert qq_plot_src.startswith("data:image/png;base64,")
        assert pp_plot_src.startswith("data:image/png;base64,")
        assert imr_plot_src.startswith("data:image/png;base64,")

    def test_plots_baseline_normal_data(self) -> None:
        """Baseline test: Diagnostic plots work with normal data.
        
        This is a baseline test that verifies all three diagnostic plots can be
        generated for a simple normally distributed dataset.
        
        **Validates: Requirement 2.6**
        """
        # Simple normal data
        np.random.seed(42)
        data = np.random.normal(12.0, 1.0, 30).tolist()
        
        # Create UIController instance
        controller = UIController()
        
        # Execute: Generate all three plots
        qq_plot_src = controller._generate_qq_plot(data)
        pp_plot_src = controller._generate_pp_plot(data)
        imr_plot_src = controller._generate_imr_chart(data)
        
        # Verify: All plots are valid
        assert qq_plot_src.startswith("data:image/png;base64,"), "Q-Q plot should be valid"
        assert pp_plot_src.startswith("data:image/png;base64,"), "P-P plot should be valid"
        assert imr_plot_src.startswith("data:image/png;base64,"), "I-MR chart should be valid"
        
        # Verify: All plots have content
        for plot_name, plot_src in [("Q-Q", qq_plot_src), ("P-P", pp_plot_src), ("I-MR", imr_plot_src)]:
            base64_data = plot_src.split(",")[1]
            decoded = base64.b64decode(base64_data)
            assert len(decoded) > 1000, f"{plot_name} plot should have substantial content"

    def test_plots_baseline_non_normal_data(self) -> None:
        """Baseline test: Diagnostic plots work with non-normal data.
        
        This test verifies that diagnostic plots can be generated even for
        non-normally distributed data (e.g., uniform distribution).
        
        **Validates: Requirement 2.6**
        """
        # Uniform data (non-normal)
        np.random.seed(42)
        data = np.random.uniform(0, 100, 30).tolist()
        
        # Create UIController instance
        controller = UIController()
        
        # Execute: Generate all three plots
        qq_plot_src = controller._generate_qq_plot(data)
        pp_plot_src = controller._generate_pp_plot(data)
        imr_plot_src = controller._generate_imr_chart(data)
        
        # Verify: All plots are valid (should work even for non-normal data)
        assert qq_plot_src.startswith("data:image/png;base64,")
        assert pp_plot_src.startswith("data:image/png;base64,")
        assert imr_plot_src.startswith("data:image/png;base64,")

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=5,
            max_size=50,
        ),
    )
    @settings(deadline=5000, max_examples=50)
    def test_plots_are_reproducible(self, data: list[float]) -> None:
        """Property 1: Diagnostic plots are reproducible for same data.
        
        This test verifies that generating plots multiple times with the same
        data produces consistent results.
        
        **Validates: Requirement 2.6**
        """
        # Create UIController instance
        controller = UIController()
        
        # Execute: Generate plots twice
        qq_plot_src1 = controller._generate_qq_plot(data)
        qq_plot_src2 = controller._generate_qq_plot(data)
        
        pp_plot_src1 = controller._generate_pp_plot(data)
        pp_plot_src2 = controller._generate_pp_plot(data)
        
        imr_plot_src1 = controller._generate_imr_chart(data)
        imr_plot_src2 = controller._generate_imr_chart(data)
        
        # Verify: Plots are reproducible (same data produces same plots)
        assert qq_plot_src1 == qq_plot_src2, "Q-Q plot should be reproducible"
        assert pp_plot_src1 == pp_plot_src2, "P-P plot should be reproducible"
        assert imr_plot_src1 == imr_plot_src2, "I-MR chart should be reproducible"
