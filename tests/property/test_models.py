"""Property-based tests for Pydantic data models.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

This module contains property-based tests using Hypothesis to validate that
the Pydantic models correctly enforce input validation rules for:
- Confidence value constraints (0 < value < 100)
- Reliability value constraints (0 < value < 100)
- Allowable failures constraints (value >= 0, integer)
- Specification limits validation based on specification type
- Pilot data validation (minimum 3 points, all numeric)
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from sample_size_calculator.models import (
    AttributeInputs,
    PilotDataInput,
    SpecificationLimits,
    SpecificationType,
)

# ============================================================================
# Property 1: Input Validation Completeness
# Tests that all validation rules are correctly enforced
# ============================================================================


class TestAttributeInputsValidation:
    """Property tests for AttributeInputs model validation."""

    @pytest.mark.urs("1.1", "1.2", "1.3")
    @given(
        confidence=st.floats(min_value=0.001, max_value=99.999),
        reliability=st.floats(min_value=0.001, max_value=99.999),
        allowable_failures=st.integers(min_value=0, max_value=1000),
    )
    def test_valid_inputs_are_accepted(
        self, confidence: float, reliability: float, allowable_failures: int
    ) -> None:
        """Property: All valid inputs within constraints should be accepted.

        **Validates: Requirements 1.1, 1.2, 1.3**

        Tests that when confidence and reliability are in (0, 100) and
        allowable_failures is non-negative, the model accepts the input.
        """
        # Act
        result = AttributeInputs(
            confidence=confidence,
            reliability=reliability,
            allowable_failures=allowable_failures,
        )

        # Assert
        assert result.confidence == confidence
        assert result.reliability == reliability
        assert result.allowable_failures == allowable_failures

    @pytest.mark.urs("1.1")
    @given(
        confidence=st.one_of(
            st.floats(max_value=0.0, exclude_max=True),
            st.floats(min_value=100.0),
        ),
        reliability=st.floats(min_value=0.001, max_value=99.999),
    )
    def test_invalid_confidence_rejected(
        self, confidence: float, reliability: float
    ) -> None:
        """Property: Confidence values outside (0, 100) should be rejected.

        **Validates: Requirements 1.1, 1.4**

        Tests that confidence values <= 0 or >= 100 raise ValidationError.
        """
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AttributeInputs(
                confidence=confidence,
                reliability=reliability,
                allowable_failures=0,
            )

        # Verify error message is descriptive
        error_msg = str(exc_info.value)
        assert "confidence" in error_msg.lower()

    @pytest.mark.urs("1.2")
    @given(
        confidence=st.floats(min_value=0.001, max_value=99.999),
        reliability=st.one_of(
            st.floats(max_value=0.0, exclude_max=True),
            st.floats(min_value=100.0),
        ),
    )
    def test_invalid_reliability_rejected(
        self, confidence: float, reliability: float
    ) -> None:
        """Property: Reliability values outside (0, 100) should be rejected.

        **Validates: Requirements 1.2, 1.4**

        Tests that reliability values <= 0 or >= 100 raise ValidationError.
        """
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AttributeInputs(
                confidence=confidence,
                reliability=reliability,
                allowable_failures=0,
            )

        # Verify error message is descriptive
        error_msg = str(exc_info.value)
        assert "reliability" in error_msg.lower()

    @pytest.mark.urs("1.3")
    @given(
        confidence=st.floats(min_value=0.001, max_value=99.999),
        reliability=st.floats(min_value=0.001, max_value=99.999),
        allowable_failures=st.integers(max_value=-1),
    )
    def test_negative_allowable_failures_rejected(
        self, confidence: float, reliability: float, allowable_failures: int
    ) -> None:
        """Property: Negative allowable failures should be rejected.

        **Validates: Requirements 1.3, 1.4**

        Tests that allowable_failures < 0 raises ValidationError.
        """
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AttributeInputs(
                confidence=confidence,
                reliability=reliability,
                allowable_failures=allowable_failures,
            )

        # Verify error message is descriptive
        error_msg = str(exc_info.value)
        assert (
            "allowable_failures" in error_msg.lower() or "greater" in error_msg.lower()
        )

    @pytest.mark.urs("1.3")
    @given(
        confidence=st.floats(min_value=0.001, max_value=99.999),
        reliability=st.floats(min_value=0.001, max_value=99.999),
    )
    def test_none_allowable_failures_accepted(
        self, confidence: float, reliability: float
    ) -> None:
        """Property: None value for allowable_failures should be accepted.

        **Validates: Requirements 1.3**

        Tests that allowable_failures can be None (for sensitivity analysis).
        """
        # Act
        result = AttributeInputs(
            confidence=confidence,
            reliability=reliability,
            allowable_failures=None,
        )

        # Assert
        assert result.allowable_failures is None

    @pytest.mark.urs("1.1", "1.2")
    @given(
        confidence=st.floats(min_value=0.001, max_value=99.999),
        reliability=st.floats(min_value=0.001, max_value=99.999),
        allowable_failures=st.integers(min_value=0, max_value=1000),
    )
    def test_validation_idempotence(
        self, confidence: float, reliability: float, allowable_failures: int
    ) -> None:
        """Property: Validating the same input multiple times produces same result.

        **Validates: Requirements 1.1, 1.2, 1.3**

        Tests that validation is deterministic and idempotent.
        """
        # Act
        result1 = AttributeInputs(
            confidence=confidence,
            reliability=reliability,
            allowable_failures=allowable_failures,
        )
        result2 = AttributeInputs(
            confidence=confidence,
            reliability=reliability,
            allowable_failures=allowable_failures,
        )

        # Assert
        assert result1.confidence == result2.confidence
        assert result1.reliability == result2.reliability
        assert result1.allowable_failures == result2.allowable_failures


class TestSpecificationLimitsValidation:
    """Property tests for SpecificationLimits model validation."""

    @pytest.mark.urs("1.1", "1.2", "1.3", "1.4")
    @given(
        lsl=st.floats(min_value=-1000.0, max_value=1000.0),
    )
    def test_one_sided_lsl_only_accepted(self, lsl: float) -> None:
        """Property: One-sided spec with only LSL should be accepted.

        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

        Tests that one-sided specification with LSL defined is valid.
        """
        # Act
        result = SpecificationLimits(
            spec_type=SpecificationType.ONE_SIDED,
            lsl=lsl,
            usl=None,
        )

        # Assert
        assert result.spec_type == SpecificationType.ONE_SIDED
        assert result.lsl == lsl
        assert result.usl is None

    @pytest.mark.urs("1.1", "1.2", "1.3", "1.4")
    @given(
        usl=st.floats(min_value=-1000.0, max_value=1000.0),
    )
    def test_one_sided_usl_only_accepted(self, usl: float) -> None:
        """Property: One-sided spec with only USL should be accepted.

        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

        Tests that one-sided specification with USL defined is valid.
        """
        # Act
        result = SpecificationLimits(
            spec_type=SpecificationType.ONE_SIDED,
            lsl=None,
            usl=usl,
        )

        # Assert
        assert result.spec_type == SpecificationType.ONE_SIDED
        assert result.lsl is None
        assert result.usl == usl

    @pytest.mark.urs("1.1", "1.2", "1.3", "1.4")
    def test_one_sided_no_limits_rejected(self) -> None:
        """Property: One-sided spec with no limits should be rejected.

        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

        Tests that one-sided specification requires at least one limit.
        """
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            SpecificationLimits(
                spec_type=SpecificationType.ONE_SIDED,
                lsl=None,
                usl=None,
            )

        # Verify error message is descriptive
        error_msg = str(exc_info.value)
        assert (
            "one-sided" in error_msg.lower()
            or "lsl" in error_msg.lower()
            or "usl" in error_msg.lower()
        )

    @pytest.mark.urs("1.1", "1.2", "1.3", "1.4")
    @given(
        lsl=st.floats(min_value=-1000.0, max_value=0.0),
        usl=st.floats(min_value=0.0, max_value=1000.0),
    )
    def test_two_sided_both_limits_accepted(self, lsl: float, usl: float) -> None:
        """Property: Two-sided spec with both limits should be accepted.

        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

        Tests that two-sided specification with both LSL and USL is valid.
        """
        # Act
        result = SpecificationLimits(
            spec_type=SpecificationType.TWO_SIDED,
            lsl=lsl,
            usl=usl,
        )

        # Assert
        assert result.spec_type == SpecificationType.TWO_SIDED
        assert result.lsl == lsl
        assert result.usl == usl

    @pytest.mark.urs("1.1", "1.2", "1.3", "1.4")
    @given(
        lsl=st.floats(min_value=-1000.0, max_value=1000.0),
    )
    def test_two_sided_missing_usl_rejected(self, lsl: float) -> None:
        """Property: Two-sided spec missing USL should be rejected.

        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

        Tests that two-sided specification requires both limits.
        """
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            SpecificationLimits(
                spec_type=SpecificationType.TWO_SIDED,
                lsl=lsl,
                usl=None,
            )

        # Verify error message is descriptive
        error_msg = str(exc_info.value)
        assert "two-sided" in error_msg.lower() or "usl" in error_msg.lower()

    @pytest.mark.urs("1.1", "1.2", "1.3", "1.4")
    @given(
        usl=st.floats(min_value=-1000.0, max_value=1000.0),
    )
    def test_two_sided_missing_lsl_rejected(self, usl: float) -> None:
        """Property: Two-sided spec missing LSL should be rejected.

        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

        Tests that two-sided specification requires both limits.
        """
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            SpecificationLimits(
                spec_type=SpecificationType.TWO_SIDED,
                lsl=None,
                usl=usl,
            )

        # Verify error message is descriptive
        error_msg = str(exc_info.value)
        assert "two-sided" in error_msg.lower() or "lsl" in error_msg.lower()


class TestPilotDataInputValidation:
    """Property tests for PilotDataInput model validation."""

    @pytest.mark.urs("1.1", "1.2", "1.3", "1.4")
    @given(
        dataset=st.lists(
            st.floats(
                min_value=-1000.0,
                max_value=1000.0,
                allow_nan=False,
                allow_infinity=False,
            ),
            min_size=3,
            max_size=100,
        )
    )
    def test_valid_dataset_accepted(self, dataset: list[float]) -> None:
        """Property: Valid datasets with >= 3 numeric values should be accepted.

        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

        Tests that pilot datasets with at least 3 numeric values are valid.
        """
        # Act
        result = PilotDataInput(
            input_method="dataset",
            dataset=dataset,
        )

        # Assert
        assert result.input_method == "dataset"
        assert result.dataset == dataset
        assert result.dataset is not None
        assert len(result.dataset) >= 3

    @pytest.mark.urs("1.1", "1.2", "1.3", "1.4")
    @given(
        dataset=st.lists(
            st.floats(
                min_value=-1000.0,
                max_value=1000.0,
                allow_nan=False,
                allow_infinity=False,
            ),
            min_size=0,
            max_size=2,
        )
    )
    def test_dataset_too_small_rejected(self, dataset: list[float]) -> None:
        """Property: Datasets with < 3 values should be rejected.

        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

        Tests that pilot datasets with fewer than 3 points raise ValidationError.
        """
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PilotDataInput(
                input_method="dataset",
                dataset=dataset,
            )

        # Verify error message is descriptive
        error_msg = str(exc_info.value)
        assert "3" in error_msg or "data points" in error_msg.lower()

    @pytest.mark.urs("1.1", "1.2", "1.3", "1.4")
    @given(
        mean=st.floats(
            min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False
        ),
        std=st.floats(
            min_value=0.001, max_value=1000.0, allow_nan=False, allow_infinity=False
        ),
    )
    def test_statistics_input_accepted(self, mean: float, std: float) -> None:
        """Property: Valid estimated statistics should be accepted.

        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

        Tests that estimated mean and standard deviation are valid inputs.
        """
        # Act
        result = PilotDataInput(
            input_method="statistics",
            estimated_mean=mean,
            estimated_std=std,
        )

        # Assert
        assert result.input_method == "statistics"
        assert result.estimated_mean == mean
        assert result.estimated_std == std

    @pytest.mark.urs("1.1", "1.2", "1.3", "1.4")
    @given(
        dataset=st.lists(
            st.floats(
                min_value=-1000.0,
                max_value=1000.0,
                allow_nan=False,
                allow_infinity=False,
            ),
            min_size=3,
            max_size=100,
        )
    )
    def test_dataset_validation_idempotence(self, dataset: list[float]) -> None:
        """Property: Validating the same dataset multiple times produces same result.

        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

        Tests that validation is deterministic and idempotent.
        """
        # Act
        result1 = PilotDataInput(
            input_method="dataset",
            dataset=dataset,
        )
        result2 = PilotDataInput(
            input_method="dataset",
            dataset=dataset,
        )

        # Assert
        assert result1.dataset == result2.dataset
        assert result1.input_method == result2.input_method


class TestBoundaryConditions:
    """Property tests for boundary conditions and edge cases."""

    @pytest.mark.urs("1.1", "1.2")
    def test_confidence_boundary_near_zero(self) -> None:
        """Property: Confidence values very close to 0 should be accepted.

        **Validates: Requirements 1.1, 1.4**

        Tests boundary condition at lower limit of confidence range.
        """
        # Act
        result = AttributeInputs(
            confidence=0.001,
            reliability=50.0,
            allowable_failures=0,
        )

        # Assert
        assert result.confidence == 0.001

    @pytest.mark.urs("1.1", "1.2")
    def test_confidence_boundary_near_hundred(self) -> None:
        """Property: Confidence values very close to 100 should be accepted.

        **Validates: Requirements 1.1, 1.4**

        Tests boundary condition at upper limit of confidence range.
        """
        # Act
        result = AttributeInputs(
            confidence=99.999,
            reliability=50.0,
            allowable_failures=0,
        )

        # Assert
        assert result.confidence == 99.999

    @pytest.mark.urs("1.2")
    def test_reliability_boundary_near_zero(self) -> None:
        """Property: Reliability values very close to 0 should be accepted.

        **Validates: Requirements 1.2, 1.4**

        Tests boundary condition at lower limit of reliability range.
        """
        # Act
        result = AttributeInputs(
            confidence=50.0,
            reliability=0.001,
            allowable_failures=0,
        )

        # Assert
        assert result.reliability == 0.001

    @pytest.mark.urs("1.2")
    def test_reliability_boundary_near_hundred(self) -> None:
        """Property: Reliability values very close to 100 should be accepted.

        **Validates: Requirements 1.2, 1.4**

        Tests boundary condition at upper limit of reliability range.
        """
        # Act
        result = AttributeInputs(
            confidence=50.0,
            reliability=99.999,
            allowable_failures=0,
        )

        # Assert
        assert result.reliability == 99.999

    @pytest.mark.urs("1.3")
    def test_allowable_failures_zero(self) -> None:
        """Property: Zero allowable failures should be accepted.

        **Validates: Requirements 1.3, 1.4**

        Tests boundary condition at lower limit of allowable failures.
        """
        # Act
        result = AttributeInputs(
            confidence=50.0,
            reliability=50.0,
            allowable_failures=0,
        )

        # Assert
        assert result.allowable_failures == 0

    @pytest.mark.urs("1.1", "1.2", "1.3", "1.4")
    def test_pilot_data_minimum_size(self) -> None:
        """Property: Pilot dataset with exactly 3 points should be accepted.

        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

        Tests boundary condition at minimum dataset size.
        """
        # Act
        result = PilotDataInput(
            input_method="dataset",
            dataset=[1.0, 2.0, 3.0],
        )

        # Assert
        assert result.dataset is not None
        assert len(result.dataset) == 3


class TestErrorMessages:
    """Property tests for descriptive error messages."""

    @pytest.mark.urs("1.4")
    def test_confidence_error_message_descriptive(self) -> None:
        """Property: Confidence validation errors should be descriptive.

        **Validates: Requirements 1.4**

        Tests that error messages clearly indicate the validation issue.
        """
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AttributeInputs(
                confidence=150.0,
                reliability=50.0,
                allowable_failures=0,
            )

        # Verify error message contains relevant information
        error_msg = str(exc_info.value)
        assert "confidence" in error_msg.lower()
        assert any(word in error_msg.lower() for word in ["less", "100", "input"])

    @pytest.mark.urs("1.4")
    def test_reliability_error_message_descriptive(self) -> None:
        """Property: Reliability validation errors should be descriptive.

        **Validates: Requirements 1.4**

        Tests that error messages clearly indicate the validation issue.
        """
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AttributeInputs(
                confidence=50.0,
                reliability=-10.0,
                allowable_failures=0,
            )

        # Verify error message contains relevant information
        error_msg = str(exc_info.value)
        assert "reliability" in error_msg.lower()
        assert any(word in error_msg.lower() for word in ["greater", "0", "input"])

    @pytest.mark.urs("1.4")
    def test_allowable_failures_error_message_descriptive(self) -> None:
        """Property: Allowable failures validation errors should be descriptive.

        **Validates: Requirements 1.4**

        Tests that error messages clearly indicate the validation issue.
        """
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AttributeInputs(
                confidence=50.0,
                reliability=50.0,
                allowable_failures=-5,
            )

        # Verify error message contains relevant information
        error_msg = str(exc_info.value)
        assert any(
            word in error_msg.lower()
            for word in ["allowable", "failures", "greater", "0"]
        )

    @pytest.mark.urs("1.4")
    def test_pilot_data_error_message_descriptive(self) -> None:
        """Property: Pilot data validation errors should be descriptive.

        **Validates: Requirements 1.4**

        Tests that error messages clearly indicate the validation issue.
        """
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PilotDataInput(
                input_method="dataset",
                dataset=[1.0, 2.0],  # Only 2 points
            )

        # Verify error message contains relevant information
        error_msg = str(exc_info.value)
        assert any(
            word in error_msg.lower() for word in ["3", "data", "points", "least"]
        )

    @pytest.mark.urs("1.4")
    def test_specification_limits_error_message_descriptive(self) -> None:
        """Property: Specification limits validation errors should be descriptive.

        **Validates: Requirements 1.4**

        Tests that error messages clearly indicate the validation issue.
        """
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            SpecificationLimits(
                spec_type=SpecificationType.TWO_SIDED,
                lsl=10.0,
                usl=None,  # Missing USL for two-sided
            )

        # Verify error message contains relevant information
        error_msg = str(exc_info.value)
        assert any(
            word in error_msg.lower() for word in ["two-sided", "usl", "lsl", "both"]
        )
