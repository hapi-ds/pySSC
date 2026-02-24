"""Property-based tests for Bug 1: Phase 4 validation accepts N or more samples.

This module contains property-based tests that verify Bug 1 fix works correctly
across a wide range of inputs. Bug 1 was about Phase 4 validation being too strict
(requiring exactly N samples instead of N or more).

**Property 1: Expected Behavior** - Phase 4 Accepts N or More Samples

For any Phase 4 validation input where the final dataset size is greater than or
equal to the required sample size N, the fixed validation function SHALL accept
the data and proceed with tolerance limit calculations.

**Validates: Requirement 2.1**
"""

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from src.sample_size_calculator.models import (
    AnalysisMethod,
    Phase2Results,
    Phase3Results,
    SpecificationLimits,
    SpecificationType,
    TransformationMethod,
)
from src.sample_size_calculator.tolerance import calculate_tolerance_limits


class TestBug1Phase4ValidationProperty:
    """Property-based tests for Bug 1: Phase 4 accepts N or more samples.
    
    **Validates: Requirement 2.1**
    """

    @given(
        required_n=st.sampled_from([10, 30, 50, 100]),
        excess_samples=st.integers(min_value=0, max_value=50),
    )
    @settings(deadline=3000, max_examples=100)
    def test_phase4_accepts_n_or_more_samples_property(
        self, required_n: int, excess_samples: int
    ) -> None:
        """Property 1: Phase 4 accepts any dataset with size >= N.
        
        This property-based test generates random combinations of:
        - Required sample sizes N (10, 30, 50, 100)
        - Excess samples (0 to 50 additional samples beyond N)
        
        For all combinations, Phase 4 validation should accept the data and
        proceed with tolerance calculations.
        
        **Validates: Requirement 2.1**
        """
        # Generate final dataset with N + excess_samples
        final_data_size = required_n + excess_samples
        
        # Generate realistic data around mean=12.0 with std=1.0
        np.random.seed(hash((required_n, excess_samples)) % (2**32))
        final_data = np.random.normal(12.0, 1.0, final_data_size).tolist()
        
        # Phase 2 results: No transformation, parametric analysis
        phase2_results = Phase2Results(
            cleaned_data=final_data[:min(10, len(final_data))],
            shapiro_p_value=0.8,
            transformation_method=TransformationMethod.NONE,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=None,
            manual_override=False,
        )
        
        # Phase 3 results: Required sample size = required_n
        phase3_results = Phase3Results(
            required_sample_size=required_n,
            k_margin=3.0,
            k_factor=2.5,
            specification_type=SpecificationType.TWO_SIDED,
        )
        
        # Specification limits
        spec_limits = SpecificationLimits(
            spec_type=SpecificationType.TWO_SIDED,
            lsl=5.0,
            usl=20.0,
        )
        
        # Execute: Should accept and calculate tolerance limits
        result = calculate_tolerance_limits(
            final_data, phase2_results, phase3_results, spec_limits
        )
        
        # Verify: Should succeed without raising ValueError
        assert result is not None, (
            f"Phase 4 validation failed for N={required_n}, "
            f"data_size={final_data_size} (N+{excess_samples})"
        )
        assert result.pass_fail in ["Pass", "Fail"], (
            f"Invalid pass_fail value: {result.pass_fail}"
        )
        assert "lower" in result.tolerance_limits or "upper" in result.tolerance_limits, (
            "Tolerance limits should contain at least one limit"
        )
        assert result.ppk is not None, "Ppk should be calculated for parametric method"
        assert len(result.final_data) == final_data_size, (
            f"Final data size mismatch: expected {final_data_size}, "
            f"got {len(result.final_data)}"
        )

    @given(
        required_n=st.sampled_from([10, 30, 50, 100]),
        excess_samples=st.integers(min_value=1, max_value=50),
        spec_type=st.sampled_from([SpecificationType.ONE_SIDED, SpecificationType.TWO_SIDED]),
    )
    @settings(deadline=3000, max_examples=100)
    def test_phase4_accepts_n_plus_samples_various_spec_types(
        self, required_n: int, excess_samples: int, spec_type: SpecificationType
    ) -> None:
        """Property 1: Phase 4 accepts N+ samples with various specification types.
        
        This test verifies that Phase 4 accepts N+ samples regardless of
        specification type (one-sided or two-sided).
        
        **Validates: Requirement 2.1**
        """
        # Generate final dataset with N + excess_samples
        final_data_size = required_n + excess_samples
        
        # Generate realistic data
        np.random.seed(hash((required_n, excess_samples, spec_type.value)) % (2**32))
        final_data = np.random.normal(12.0, 1.0, final_data_size).tolist()
        
        # Phase 2 results: No transformation, parametric analysis
        phase2_results = Phase2Results(
            cleaned_data=final_data[:min(10, len(final_data))],
            shapiro_p_value=0.8,
            transformation_method=TransformationMethod.NONE,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=None,
            manual_override=False,
        )
        
        # Phase 3 results with specified spec type
        phase3_results = Phase3Results(
            required_sample_size=required_n,
            k_margin=3.0,
            k_factor=2.5,
            specification_type=spec_type,
        )
        
        # Specification limits based on spec type
        if spec_type == SpecificationType.ONE_SIDED:
            # Randomly choose lower or upper spec limit
            if hash((required_n, excess_samples)) % 2 == 0:
                spec_limits = SpecificationLimits(
                    spec_type=spec_type,
                    lsl=5.0,
                    usl=None,
                )
            else:
                spec_limits = SpecificationLimits(
                    spec_type=spec_type,
                    lsl=None,
                    usl=20.0,
                )
        else:  # TWO_SIDED
            spec_limits = SpecificationLimits(
                spec_type=spec_type,
                lsl=5.0,
                usl=20.0,
            )
        
        # Execute: Should accept and calculate tolerance limits
        result = calculate_tolerance_limits(
            final_data, phase2_results, phase3_results, spec_limits
        )
        
        # Verify: Should succeed
        assert result is not None
        assert result.pass_fail in ["Pass", "Fail"]
        assert len(result.tolerance_limits) > 0
        assert len(result.final_data) == final_data_size

    @given(
        required_n=st.sampled_from([10, 30, 50, 100]),
        excess_samples=st.integers(min_value=0, max_value=50),
        analysis_method=st.sampled_from([AnalysisMethod.PARAMETRIC, AnalysisMethod.NON_PARAMETRIC]),
    )
    @settings(deadline=3000, max_examples=100)
    def test_phase4_accepts_n_plus_samples_various_analysis_methods(
        self, required_n: int, excess_samples: int, analysis_method: AnalysisMethod
    ) -> None:
        """Property 1: Phase 4 accepts N+ samples with various analysis methods.
        
        This test verifies that Phase 4 accepts N+ samples regardless of
        analysis method (parametric or non-parametric).
        
        **Validates: Requirement 2.1**
        """
        # Generate final dataset with N + excess_samples
        final_data_size = required_n + excess_samples
        
        # Generate realistic data
        np.random.seed(hash((required_n, excess_samples, analysis_method.value)) % (2**32))
        final_data = np.random.normal(12.0, 1.0, final_data_size).tolist()
        
        # Phase 2 results with specified analysis method
        phase2_results = Phase2Results(
            cleaned_data=final_data[:min(10, len(final_data))],
            shapiro_p_value=0.8 if analysis_method == AnalysisMethod.PARAMETRIC else 0.02,
            transformation_method=TransformationMethod.NONE,
            analysis_method=analysis_method,
            lambda_param=None,
            manual_override=False,
        )
        
        # Phase 3 results
        phase3_results = Phase3Results(
            required_sample_size=required_n,
            k_margin=3.0,
            k_factor=2.5,
            specification_type=SpecificationType.TWO_SIDED,
        )
        
        # Specification limits
        spec_limits = SpecificationLimits(
            spec_type=SpecificationType.TWO_SIDED,
            lsl=5.0,
            usl=20.0,
        )
        
        # Execute: Should accept and calculate tolerance limits
        result = calculate_tolerance_limits(
            final_data, phase2_results, phase3_results, spec_limits
        )
        
        # Verify: Should succeed
        assert result is not None
        assert result.pass_fail in ["Pass", "Fail"]
        assert len(result.tolerance_limits) > 0
        assert len(result.final_data) == final_data_size
        
        # Ppk should only be calculated for parametric methods
        if analysis_method == AnalysisMethod.PARAMETRIC:
            assert result.ppk is not None
        else:
            assert result.ppk is None

    @given(
        required_n=st.sampled_from([10, 30, 50, 100]),
        excess_samples=st.integers(min_value=0, max_value=50),
        transformation=st.sampled_from([
            TransformationMethod.NONE,
            TransformationMethod.LOGARITHMIC,
        ]),
    )
    @settings(deadline=3000, max_examples=80)
    def test_phase4_accepts_n_plus_samples_with_transformations(
        self, required_n: int, excess_samples: int, transformation: TransformationMethod
    ) -> None:
        """Property 1: Phase 4 accepts N+ samples with various transformations.
        
        This test verifies that Phase 4 accepts N+ samples regardless of
        transformation method applied in Phase 2.
        
        **Validates: Requirement 2.1**
        """
        # Generate final dataset with N + excess_samples
        final_data_size = required_n + excess_samples
        
        # Generate realistic positive data for transformations
        np.random.seed(hash((required_n, excess_samples, transformation.value)) % (2**32))
        # Use positive data for logarithmic transformation
        final_data = np.random.lognormal(2.5, 0.3, final_data_size).tolist()
        
        # Phase 2 results with specified transformation
        phase2_results = Phase2Results(
            cleaned_data=final_data[:min(10, len(final_data))],
            shapiro_p_value=0.8,
            transformation_method=transformation,
            analysis_method=AnalysisMethod.PARAMETRIC,
            lambda_param=None,
            manual_override=False,
        )
        
        # Phase 3 results
        phase3_results = Phase3Results(
            required_sample_size=required_n,
            k_margin=3.0,
            k_factor=2.5,
            specification_type=SpecificationType.TWO_SIDED,
        )
        
        # Specification limits
        spec_limits = SpecificationLimits(
            spec_type=SpecificationType.TWO_SIDED,
            lsl=5.0,
            usl=50.0,
        )
        
        # Execute: Should accept and calculate tolerance limits
        result = calculate_tolerance_limits(
            final_data, phase2_results, phase3_results, spec_limits
        )
        
        # Verify: Should succeed
        assert result is not None
        assert result.pass_fail in ["Pass", "Fail"]
        assert len(result.tolerance_limits) > 0
        assert len(result.final_data) == final_data_size
        assert result.ppk is not None

    def test_phase4_accepts_exactly_n_samples_baseline(self) -> None:
        """Baseline test: Phase 4 accepts datasets with exactly N samples.
        
        This is a baseline case that should work both before and after the fix.
        Included here to verify the property holds for the N=N case.
        
        **Validates: Requirement 2.1**
        """
        # Test with various N values
        for required_n in [10, 30, 50, 100]:
            # Generate final dataset with exactly N samples
            np.random.seed(required_n)
            final_data = np.random.normal(12.0, 1.0, required_n).tolist()
            
            # Phase 2 results
            phase2_results = Phase2Results(
                cleaned_data=final_data[:min(10, len(final_data))],
                shapiro_p_value=0.8,
                transformation_method=TransformationMethod.NONE,
                analysis_method=AnalysisMethod.PARAMETRIC,
                lambda_param=None,
                manual_override=False,
            )
            
            # Phase 3 results
            phase3_results = Phase3Results(
                required_sample_size=required_n,
                k_margin=3.0,
                k_factor=2.5,
                specification_type=SpecificationType.TWO_SIDED,
            )
            
            # Specification limits
            spec_limits = SpecificationLimits(
                spec_type=SpecificationType.TWO_SIDED,
                lsl=5.0,
                usl=20.0,
            )
            
            # Execute: Should accept and calculate tolerance limits
            result = calculate_tolerance_limits(
                final_data, phase2_results, phase3_results, spec_limits
            )
            
            # Verify: Should succeed
            assert result is not None, f"Failed for N={required_n}"
            assert result.pass_fail in ["Pass", "Fail"]
            assert len(result.tolerance_limits) > 0
            assert len(result.final_data) == required_n
