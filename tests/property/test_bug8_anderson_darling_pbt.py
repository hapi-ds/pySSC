"""Property-based tests for Bug 8: Two normality tests performed.

This module contains property-based tests that verify Bug 8 fix works correctly
across a wide range of inputs. Bug 8 was about only performing Shapiro-Wilk test
instead of both Shapiro-Wilk and Anderson-Darling tests for normality assessment.

**Property 1: Expected Behavior** - Two Normality Tests Performed

For any Phase 2 normality assessment, the fixed system SHALL perform both
Shapiro-Wilk and Anderson-Darling tests and display all test results with their
respective statistics and p-values/critical values.

**Validates: Requirement 2.8**
"""

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from src.sample_size_calculator.normality import (
    anderson_darling_test,
    shapiro_wilk_test,
)


class TestBug8AndersonDarlingProperty:
    """Property-based tests for Bug 8: Two normality tests performed.
    
    **Validates: Requirement 2.8**
    """

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=5,
            max_size=100,
        ),
    )
    @settings(deadline=5000, max_examples=100)
    def test_anderson_darling_test_returns_valid_results_property(
        self, data: list[float]
    ) -> None:
        """Property 1: Anderson-Darling test returns valid results for all datasets.
        
        This property-based test generates random datasets and verifies that
        the anderson_darling_test function returns valid results (statistic,
        critical values, significance levels) for all inputs.
        
        **Validates: Requirement 2.8**
        """
        # Execute: Perform Anderson-Darling test
        statistic, critical_values, significance_levels = anderson_darling_test(data)
        
        # Verify: Statistic is a valid float
        assert isinstance(statistic, float), "Statistic should be a float"
        assert not np.isnan(statistic), "Statistic should not be NaN"
        assert not np.isinf(statistic), "Statistic should not be infinite"
        assert statistic >= 0, "Anderson-Darling statistic should be non-negative"
        
        # Verify: Critical values are valid
        assert isinstance(critical_values, (list, np.ndarray)), (
            "Critical values should be a list or array"
        )
        assert len(critical_values) == 5, (
            "Anderson-Darling should return 5 critical values (15%, 10%, 5%, 2.5%, 1%)"
        )
        for cv in critical_values:
            assert isinstance(cv, (float, np.floating)), f"Critical value should be float, got {type(cv)}"
            assert not np.isnan(cv), "Critical value should not be NaN"
            assert not np.isinf(cv), "Critical value should not be infinite"
            assert cv > 0, "Critical values should be positive"
        
        # Verify: Significance levels are valid
        assert isinstance(significance_levels, (list, np.ndarray)), (
            "Significance levels should be a list or array"
        )
        assert len(significance_levels) == 5, (
            "Anderson-Darling should return 5 significance levels"
        )
        expected_levels = [15.0, 10.0, 5.0, 2.5, 1.0]
        for i, level in enumerate(significance_levels):
            assert isinstance(level, (float, np.floating)), f"Significance level should be float, got {type(level)}"
            assert level == expected_levels[i], (
                f"Significance level {i} should be {expected_levels[i]}%, got {level}%"
            )

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=5,
            max_size=100,
        ),
    )
    @settings(deadline=5000, max_examples=100)
    def test_both_normality_tests_work_together_property(
        self, data: list[float]
    ) -> None:
        """Property 1: Both Shapiro-Wilk and Anderson-Darling tests work together.
        
        This test verifies that both normality tests can be performed on the same
        dataset and both return valid results.
        
        **Validates: Requirement 2.8**
        """
        # Execute: Perform both tests
        sw_statistic, sw_p_value = shapiro_wilk_test(data)
        ad_statistic, ad_critical_values, ad_significance_levels = anderson_darling_test(data)
        
        # Verify: Shapiro-Wilk results are valid
        assert isinstance(sw_statistic, float), "Shapiro-Wilk statistic should be float"
        assert isinstance(sw_p_value, float), "Shapiro-Wilk p-value should be float"
        assert 0 <= sw_p_value <= 1, "Shapiro-Wilk p-value should be between 0 and 1"
        
        # Verify: Anderson-Darling results are valid
        assert isinstance(ad_statistic, float), "Anderson-Darling statistic should be float"
        assert ad_statistic >= 0, "Anderson-Darling statistic should be non-negative"
        assert len(ad_critical_values) == 5, "Anderson-Darling should return 5 critical values"
        assert len(ad_significance_levels) == 5, "Anderson-Darling should return 5 significance levels"
        
        # Verify: Both tests completed successfully (no exceptions)
        assert sw_statistic is not None
        assert ad_statistic is not None

    @given(
        data=st.lists(
            st.floats(min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=5,
            max_size=50,
        ),
    )
    @settings(deadline=5000, max_examples=80)
    def test_anderson_darling_with_positive_data(self, data: list[float]) -> None:
        """Property 1: Anderson-Darling test works with positive data.
        
        This test verifies that the Anderson-Darling test works correctly with
        positive-only datasets.
        
        **Validates: Requirement 2.8**
        """
        # Execute: Perform Anderson-Darling test
        statistic, critical_values, significance_levels = anderson_darling_test(data)
        
        # Verify: Valid results
        assert statistic >= 0
        assert len(critical_values) == 5
        assert len(significance_levels) == 5

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=-0.1, allow_nan=False, allow_infinity=False),
            min_size=5,
            max_size=50,
        ),
    )
    @settings(deadline=5000, max_examples=80)
    def test_anderson_darling_with_negative_data(self, data: list[float]) -> None:
        """Property 1: Anderson-Darling test works with negative data.
        
        This test verifies that the Anderson-Darling test works correctly with
        negative-only datasets.
        
        **Validates: Requirement 2.8**
        """
        # Execute: Perform Anderson-Darling test
        statistic, critical_values, significance_levels = anderson_darling_test(data)
        
        # Verify: Valid results
        assert statistic >= 0
        assert len(critical_values) == 5
        assert len(significance_levels) == 5

    @given(
        data_size=st.integers(min_value=5, max_value=100),
    )
    @settings(deadline=5000, max_examples=80)
    def test_anderson_darling_with_various_data_sizes(self, data_size: int) -> None:
        """Property 1: Anderson-Darling test works with various data sizes.
        
        This test verifies that the Anderson-Darling test works correctly with
        datasets of various sizes.
        
        **Validates: Requirement 2.8**
        """
        # Generate data with specified size
        np.random.seed(data_size)
        data = np.random.normal(12.0, 1.0, data_size).tolist()
        
        # Execute: Perform Anderson-Darling test
        statistic, critical_values, significance_levels = anderson_darling_test(data)
        
        # Verify: Valid results
        assert statistic >= 0
        assert len(critical_values) == 5
        assert len(significance_levels) == 5

    @given(
        mean=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        std=st.floats(min_value=0.1, max_value=50.0, allow_nan=False, allow_infinity=False),
    )
    @settings(deadline=5000, max_examples=80)
    def test_anderson_darling_with_various_distributions(
        self, mean: float, std: float
    ) -> None:
        """Property 1: Anderson-Darling test works with various normal distributions.
        
        This test verifies that the Anderson-Darling test works correctly with
        datasets from different normal distributions (various means and std devs).
        
        **Validates: Requirement 2.8**
        """
        # Generate data with specified distribution
        np.random.seed(hash((mean, std)) % (2**32))
        data = np.random.normal(mean, std, 30).tolist()
        
        # Execute: Perform Anderson-Darling test
        statistic, critical_values, significance_levels = anderson_darling_test(data)
        
        # Verify: Valid results
        assert statistic >= 0
        assert len(critical_values) == 5
        assert len(significance_levels) == 5

    def test_anderson_darling_baseline_normal_data(self) -> None:
        """Baseline test: Anderson-Darling test works with normal data.
        
        This is a baseline test that verifies the Anderson-Darling test works
        correctly with a simple normally distributed dataset.
        
        **Validates: Requirement 2.8**
        """
        # Simple normal data
        np.random.seed(42)
        data = np.random.normal(12.0, 1.0, 30).tolist()
        
        # Execute: Perform Anderson-Darling test
        statistic, critical_values, significance_levels = anderson_darling_test(data)
        
        # Verify: Valid results
        assert isinstance(statistic, float)
        assert statistic >= 0
        assert len(critical_values) == 5
        assert len(significance_levels) == 5
        
        # For normal data, statistic should typically be small
        # (though this is not guaranteed, it's a reasonable expectation)
        assert statistic < 10, "Statistic for normal data should typically be small"

    def test_anderson_darling_baseline_non_normal_data(self) -> None:
        """Baseline test: Anderson-Darling test works with non-normal data.
        
        This test verifies that the Anderson-Darling test works correctly with
        non-normally distributed data (e.g., uniform distribution).
        
        **Validates: Requirement 2.8**
        """
        # Uniform data (non-normal)
        np.random.seed(42)
        data = np.random.uniform(0, 100, 30).tolist()
        
        # Execute: Perform Anderson-Darling test
        statistic, critical_values, significance_levels = anderson_darling_test(data)
        
        # Verify: Valid results
        assert isinstance(statistic, float)
        assert statistic >= 0
        assert len(critical_values) == 5
        assert len(significance_levels) == 5
        
        # For non-normal data, statistic should typically be larger
        # (though this is not guaranteed, it's a reasonable expectation)
        # We just verify it's a valid number

    def test_both_tests_baseline_comparison(self) -> None:
        """Baseline test: Compare Shapiro-Wilk and Anderson-Darling results.
        
        This test verifies that both tests can be performed on the same dataset
        and provides a baseline comparison of their results.
        
        **Validates: Requirement 2.8**
        """
        # Test with normal data
        np.random.seed(42)
        normal_data = np.random.normal(12.0, 1.0, 30).tolist()
        
        # Execute: Perform both tests
        sw_statistic, sw_p_value = shapiro_wilk_test(normal_data)
        ad_statistic, ad_critical_values, ad_significance_levels = anderson_darling_test(normal_data)
        
        # Verify: Both tests return valid results
        assert 0 <= sw_p_value <= 1, "Shapiro-Wilk p-value should be between 0 and 1"
        assert ad_statistic >= 0, "Anderson-Darling statistic should be non-negative"
        
        # For normal data, both tests should suggest normality
        # Shapiro-Wilk: high p-value (> 0.05)
        # Anderson-Darling: statistic < critical value at 5% level
        assert sw_p_value > 0.05, "Shapiro-Wilk should suggest normality for normal data"
        assert ad_statistic < ad_critical_values[2], (
            "Anderson-Darling should suggest normality for normal data (statistic < 5% critical value)"
        )
        
        # Test with non-normal data
        np.random.seed(42)
        uniform_data = np.random.uniform(0, 100, 30).tolist()
        
        # Execute: Perform both tests
        sw_statistic_u, sw_p_value_u = shapiro_wilk_test(uniform_data)
        ad_statistic_u, ad_critical_values_u, ad_significance_levels_u = anderson_darling_test(uniform_data)
        
        # Verify: Both tests return valid results
        assert 0 <= sw_p_value_u <= 1
        assert ad_statistic_u >= 0

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=5,
            max_size=50,
        ),
    )
    @settings(deadline=5000, max_examples=50)
    def test_anderson_darling_critical_values_ordered(self, data: list[float]) -> None:
        """Property 1: Anderson-Darling critical values are properly ordered.
        
        This test verifies that the critical values returned by the Anderson-Darling
        test are in ascending order (15% < 10% < 5% < 2.5% < 1%).
        
        **Validates: Requirement 2.8**
        """
        # Execute: Perform Anderson-Darling test
        statistic, critical_values, significance_levels = anderson_darling_test(data)
        
        # Verify: Critical values are in ascending order
        for i in range(len(critical_values) - 1):
            assert critical_values[i] < critical_values[i + 1], (
                f"Critical values should be in ascending order: "
                f"cv[{i}]={critical_values[i]:.4f} should be < cv[{i+1}]={critical_values[i+1]:.4f}"
            )

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=5,
            max_size=50,
        ),
    )
    @settings(deadline=5000, max_examples=50)
    def test_anderson_darling_is_reproducible(self, data: list[float]) -> None:
        """Property 1: Anderson-Darling test is reproducible for same data.
        
        This test verifies that running the Anderson-Darling test multiple times
        on the same data produces identical results.
        
        **Validates: Requirement 2.8**
        """
        # Execute: Perform test twice
        statistic1, critical_values1, significance_levels1 = anderson_darling_test(data)
        statistic2, critical_values2, significance_levels2 = anderson_darling_test(data)
        
        # Verify: Results are identical
        assert statistic1 == statistic2, "Statistic should be reproducible"
        assert np.allclose(critical_values1, critical_values2), "Critical values should be reproducible"
        assert np.allclose(significance_levels1, significance_levels2), "Significance levels should be reproducible"

    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=5,
            max_size=50,
        ),
    )
    @settings(deadline=5000, max_examples=50)
    def test_both_tests_are_independent(self, data: list[float]) -> None:
        """Property 1: Shapiro-Wilk and Anderson-Darling tests are independent.
        
        This test verifies that performing one test does not affect the results
        of the other test (they are independent).
        
        **Validates: Requirement 2.8**
        """
        # Execute: Perform Shapiro-Wilk first, then Anderson-Darling
        sw_statistic1, sw_p_value1 = shapiro_wilk_test(data)
        ad_statistic1, ad_critical_values1, ad_significance_levels1 = anderson_darling_test(data)
        
        # Execute: Perform Anderson-Darling first, then Shapiro-Wilk
        ad_statistic2, ad_critical_values2, ad_significance_levels2 = anderson_darling_test(data)
        sw_statistic2, sw_p_value2 = shapiro_wilk_test(data)
        
        # Verify: Results are independent of execution order
        assert sw_statistic1 == sw_statistic2, "Shapiro-Wilk should be independent of execution order"
        assert sw_p_value1 == sw_p_value2, "Shapiro-Wilk p-value should be independent of execution order"
        assert ad_statistic1 == ad_statistic2, "Anderson-Darling should be independent of execution order"
        assert np.allclose(ad_critical_values1, ad_critical_values2), (
            "Anderson-Darling critical values should be independent of execution order"
        )
