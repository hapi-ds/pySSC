"""Pydantic data models for the Sample Size Calculator application.

This module defines all data structures used throughout the application,
providing type safety, validation, and serialization capabilities. All models
use Pydantic for automatic validation and type checking at runtime.

The models serve as the single source of truth for data structures across:
- User interface (input validation and display)
- Calculation engine (parameter passing and result storage)
- Report generation (PDF content and formatting)
- Audit logging (structured event data)

References:
    - Pydantic documentation: https://docs.pydantic.dev/
    - ISO/TR 80002-2: Medical device software validation guidance

Validates: Requirements 37.1, 37.2, 37.3, 37.4, 37.5
"""

from enum import StrEnum

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from sample_size_calculator.version import __version__


class SpecificationType(StrEnum):
    """Specification type for Module V analysis."""

    ONE_SIDED = "One-Sided"
    TWO_SIDED = "Two-Sided"


class TransformationMethod(StrEnum):
    """Data transformation methods for normality."""

    NONE = "None"
    LOGARITHMIC = "Logarithmic"
    BOX_COX = "Box-Cox"
    YEO_JOHNSON = "Yeo-Johnson"


class AnalysisMethod(StrEnum):
    """Statistical analysis methods."""

    PARAMETRIC = "Parametric"
    NON_PARAMETRIC = "Non-Parametric (Wilks)"


# Module A Models


class AttributeInputs(BaseModel):
    """Input parameters for Module A attribute data analysis.

    This model validates input parameters for binary Pass/Fail test scenarios.
    It supports both zero-failure testing (Success Run Theorem) and scenarios
    with allowable failures (Cumulative Binomial Distribution).

    Attributes:
        confidence: Confidence level as percentage (0-100). The probability that
            the true reliability is at least the specified value. Typical values:
            90%, 95%, 99%.
        reliability: Reliability level as percentage (0-100). The minimum acceptable
            proportion of passing units in the population. Typical values: 90%, 95%, 99%.
        allowable_failures: Number of failures allowed in the test (c). Use 0 for
            zero-failure testing, or None for sensitivity analysis across c=0,1,2,3.
            Must be non-negative integer.

    Validates: Requirements 1.1, 1.2, 1.3
    """

    confidence: float = Field(gt=0, lt=100, description="Confidence level (%)")
    reliability: float = Field(gt=0, lt=100, description="Reliability level (%)")
    allowable_failures: int | None = Field(
        default=None, ge=0, description="Allowable failures (c)"
    )

    @field_validator("allowable_failures")
    @classmethod
    def validate_allowable_failures(cls, v: int | None) -> int | None:
        """Validate that allowable failures is non-negative."""
        if v is not None and v < 0:
            raise ValueError("Allowable failures must be non-negative")
        return v


class AttributeResults(BaseModel):
    """Results from Module A attribute data analysis."""

    sample_size: int
    confidence: float
    reliability: float
    allowable_failures: int
    method: Literal["Success Run Theorem", "Cumulative Binomial"]


class SensitivityAnalysisResults(BaseModel):
    """Results from sensitivity analysis for multiple allowable failure values."""

    results: list[tuple[int, int]]  # [(c, n), ...]


# Module V Models


class SpecificationLimits(BaseModel):
    """Specification limits for Module V variable data analysis."""

    spec_type: SpecificationType
    lsl: float | None = None
    usl: float | None = None

    @field_validator("lsl", "usl", mode="after")
    @classmethod
    def validate_limits(cls, v: float | None, info) -> float | None:
        """Validate specification limits based on specification type."""
        spec_type = info.data.get("spec_type")
        field_name = info.field_name

        # For two-sided, both limits must be defined
        if spec_type == SpecificationType.TWO_SIDED:
            if v is None:
                missing = field_name.upper()
                raise ValueError(
                    f"Two-sided spec requires both LSL and USL (missing {missing})"
                )
        return v

    def model_post_init(self, __context) -> None:
        """Validate one-sided specification after all fields are set."""
        # For one-sided, at least one limit must be defined
        if self.spec_type == SpecificationType.ONE_SIDED:
            if self.lsl is None and self.usl is None:
                raise ValueError("One-sided spec requires either LSL or USL")


class PilotDataInput(BaseModel):
    """Input for pilot data in Module V Phase 1."""

    input_method: Literal["dataset", "statistics"]
    dataset: list[float] | None = None
    estimated_mean: float | None = None
    estimated_std: float | None = None

    @field_validator("dataset")
    @classmethod
    def validate_dataset(cls, v: list[float] | None) -> list[float] | None:
        """Validate pilot dataset requirements."""
        if v is not None:
            if len(v) < 3:
                raise ValueError("Pilot dataset must contain at least 3 data points")
            if not all(isinstance(x, (int, float)) for x in v):
                raise ValueError("All pilot data values must be numeric")
        return v


class OutlierInfo(BaseModel):
    """Information about a detected outlier."""

    value: float
    is_excluded: bool = False
    rationale: str | None = None


class Phase1Results(BaseModel):
    """Results from Module V Phase 1 (pilot data analysis and outlier detection)."""

    pilot_data: list[float]
    outliers: list[OutlierInfo]
    q1: float
    q3: float
    iqr: float


class Phase2Results(BaseModel):
    """Results from Module V Phase 2 (normality testing and transformation)."""

    cleaned_data: list[float]
    shapiro_p_value: float
    transformation_method: TransformationMethod
    analysis_method: AnalysisMethod
    lambda_param: float | None = None
    manual_override: bool = False


class Phase3Results(BaseModel):
    """Results from Module V Phase 3 (sample size calculation)."""

    required_sample_size: int
    k_margin: float
    k_factor: float
    specification_type: SpecificationType


class Phase4Results(BaseModel):
    """Results from Module V Phase 4 (final validation and tolerance limits)."""

    final_data: list[float]
    tolerance_limits: dict[str, float]  # {"lower": x, "upper": y} or {"limit": x}
    pass_fail: Literal["Pass", "Fail"]
    ppk: float | None = None


# Report Models


class CalculationReport(BaseModel):
    """User calculation report data."""

    timestamp: str
    module: Literal["Module A", "Module V"]
    inputs: dict
    results: dict
    engine_hash: str
    validation_state: bool
    method_path: str
    version: str = __version__


class ValidationCertificate(BaseModel):
    """Validation certificate data for IQ/OQ/PQ reports."""

    test_date: str
    tester_name: str
    system_info: dict
    test_results: list[dict]  # [{"urs_id": "...", "test_id": "...", "status": "..."}]
    validated_hash: str
    pdf_test_results: list[dict] = []  # PDF validation test results
