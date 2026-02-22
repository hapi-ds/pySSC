# Requirements Document

## Introduction

The Sample Size Calculator is a Python-based web application for determining statistically valid sample sizes for medical device design verification and process validation. This is critical QMS (Quality Management System) software that must comply with ISO/TR 80002-2 standards. The application provides two primary analysis modules: Module A for attribute (binary) data analysis and Module V for variable (continuous) data analysis with a strict 4-phase sequential workflow. The system ensures data integrity through SHA-256 hash verification and provides comprehensive validation reporting (IQ/OQ/PQ).

## Glossary

- **System**: The Sample Size Calculator application
- **Module_A**: The Attribute Data Analysis module for binary Pass/Fail data
- **Module_V**: The Variable Data Analysis module for continuous measurements
- **Calculation_Engine**: The core mathematical computation module (calculations.py)
- **Report_Generator**: The PDF report generation subsystem using reportlab
- **Validation_Suite**: The automated IQ/OQ/PQ test framework using pytest and playwright
- **UI_Controller**: The NiceGUI-based user interface management system
- **Hash_Verifier**: The SHA-256 integrity checking subsystem
- **Transformation_Engine**: The data normalization and transformation subsystem
- **Outlier_Detector**: The IQR-based outlier identification subsystem
- **Normality_Tester**: The Shapiro-Wilk statistical test subsystem
- **Tolerance_Calculator**: The statistical tolerance interval computation subsystem
- **VTM_Generator**: The Verification Traceability Matrix generation subsystem

## Requirements

### Requirement 1: Attribute Data Input Validation

**User Story:** As a quality engineer, I want to input confidence, reliability, and allowable failures parameters for attribute data analysis, so that I can calculate appropriate sample sizes for binary test scenarios.

#### Acceptance Criteria

1. WHEN a user enters a confidence value, THE System SHALL validate that the value is greater than 0 and less than 100
2. WHEN a user enters a reliability value, THE System SHALL validate that the value is greater than 0 and less than 100
3. WHEN a user enters an allowable failures value, THE System SHALL validate that the value is a non-negative integer
4. IF a user enters an invalid parameter value, THEN THE System SHALL display a descriptive error message and prevent calculation
5. THE Module_A SHALL accept confidence, reliability, and allowable failures as input parameters

### Requirement 2: Success Run Theorem Calculation

**User Story:** As a quality engineer, I want to calculate sample size using the Success Run Theorem when zero failures are allowed, so that I can determine the minimum sample size for high-reliability scenarios.

#### Acceptance Criteria

1. WHEN allowable failures equals zero, THE Calculation_Engine SHALL compute sample size using the formula n = ceiling(ln(1-C)/ln(R))
2. THE Calculation_Engine SHALL return an integer sample size value
3. FOR ALL valid confidence and reliability inputs with c=0, calculating then recalculating with the same inputs SHALL produce identical results (idempotence property)
4. THE Module_A SHALL display the calculated sample size to the user

### Requirement 3: Cumulative Binomial Distribution Calculation

**User Story:** As a quality engineer, I want to calculate sample size using cumulative binomial distribution when failures are allowed, so that I can determine appropriate sample sizes for scenarios with acceptable failure rates.

#### Acceptance Criteria

1. WHEN allowable failures is greater than zero, THE Calculation_Engine SHALL compute the minimum sample size where the cumulative binomial probability is less than or equal to 1-C
2. THE Calculation_Engine SHALL iterate to find the smallest n satisfying the cumulative binomial constraint
3. THE Calculation_Engine SHALL use the formula: sum from k=0 to c of [C(n,k) * (1-R)^k * R^(n-k)] <= 1-C
4. FOR ALL valid inputs with c>0, the calculated sample size SHALL be greater than or equal to the sample size for c=0 with the same C and R (monotonicity property)

### Requirement 4: Sensitivity Analysis for Allowable Failures

**User Story:** As a quality engineer, I want to see sample sizes for multiple allowable failure scenarios simultaneously, so that I can make informed decisions about acceptable failure rates.

#### Acceptance Criteria

1. WHEN the allowable failures input is empty, THE Module_A SHALL automatically calculate sample sizes for c=0, c=1, c=2, and c=3
2. THE Module_A SHALL display results in a table with two columns: allowable failures (c) and required sample size (n)
3. THE System SHALL display all four calculations simultaneously
4. FOR ALL sensitivity analysis results, sample sizes SHALL be monotonically non-decreasing as c increases (monotonicity property)

### Requirement 5: Specification Constraint Definition

**User Story:** As a quality engineer, I want to explicitly define specification limits as one-sided or two-sided, so that the system applies the correct statistical methods for my validation scenario.

#### Acceptance Criteria

1. WHEN using Module_V, THE System SHALL require the user to select either One-Sided or Two-Sided specification type
2. IF One-Sided is selected, THEN THE System SHALL require either LSL or USL to be defined
3. IF Two-Sided is selected, THEN THE System SHALL require both LSL and USL to be defined
4. THE System SHALL prevent progression to Phase 2 until specification constraints are fully defined
5. WHEN specification type is changed, THE System SHALL clear all downstream calculation results

### Requirement 6: Pilot Data Input and Validation

**User Story:** As a quality engineer, I want to input pilot dataset measurements or estimated statistics, so that the system can estimate variance and required sample sizes for variable data analysis.

#### Acceptance Criteria

1. THE Module_V SHALL accept a pilot dataset of continuous numeric values as the primary input method
2. THE Module_V SHALL accept estimated mean and standard deviation as an alternative input method
3. THE System SHALL validate that all pilot data values are numeric
4. THE System SHALL require a minimum of 3 data points in the pilot dataset
5. WHEN pilot data contains fewer than 30 datapoints, THE System SHALL display a validation warning indicating that the sample size should be between 12 and 30 for reliable variance estimation
6. IF invalid data is entered, THEN THE System SHALL display a descriptive error message
7. THE System SHALL store the pilot dataset or estimated statistics for use in subsequent phases
8. THE System SHALL prevent simultaneous use of both pilot data and estimated statistics input methods

### Requirement 7: Outlier Detection Using IQR Method

**User Story:** As a quality engineer, I want the system to automatically detect outliers in my pilot data, so that I can identify potentially problematic measurements.

#### Acceptance Criteria

1. WHEN pilot data is provided, THE Outlier_Detector SHALL calculate Q1, Q3, and IQR from the dataset
2. THE Outlier_Detector SHALL flag values less than Q1 - 1.5 * IQR as outliers
3. THE Outlier_Detector SHALL flag values greater than Q3 + 1.5 * IQR as outliers
4. THE System SHALL display all detected outliers to the user with their values
5. FOR ALL datasets, the IQR method SHALL identify the same outliers when applied multiple times (idempotence property)

### Requirement 8: Outlier Exclusion with Engineering Rationale

**User Story:** As a quality engineer, I want to manually exclude detected outliers with documented justification, so that I can remove invalid measurements while maintaining traceability.

#### Acceptance Criteria

1. WHEN an outlier is detected, THE System SHALL allow the user to exclude it from analysis
2. IF a user excludes an outlier, THEN THE System SHALL require entry of an engineering rationale text
3. THE System SHALL prevent outlier exclusion without a non-empty rationale
4. THE System SHALL permanently flag excluded outliers and their rationales in the final report
5. THE System SHALL recalculate all statistics using the cleaned dataset after exclusions

### Requirement 9: Shapiro-Wilk Normality Testing

**User Story:** As a quality engineer, I want the system to test my data for normality, so that I can determine whether parametric or non-parametric methods are appropriate.

#### Acceptance Criteria

1. WHEN Phase 2 is initiated, THE Normality_Tester SHALL perform a Shapiro-Wilk test on the cleaned pilot dataset
2. THE Normality_Tester SHALL calculate the p-value from the Shapiro-Wilk test
3. IF the p-value is greater than 0.05, THEN THE System SHALL classify the data as Normal and lock the method as Parametric
4. IF the p-value is less than or equal to 0.05, THEN THE System SHALL proceed to transformation attempts
5. THE System SHALL display the Shapiro-Wilk p-value to the user

### Requirement 10: Logarithmic Transformation Attempt

**User Story:** As a quality engineer, I want the system to attempt logarithmic transformation on non-normal data, so that I can potentially normalize the data for parametric analysis.

#### Acceptance Criteria

1. WHEN data fails the Shapiro-Wilk test, THE Transformation_Engine SHALL check if all values are greater than zero
2. IF all values are positive, THEN THE Transformation_Engine SHALL apply natural logarithm transformation to the dataset
3. THE Normality_Tester SHALL perform Shapiro-Wilk test on the log-transformed data
4. IF the transformed data p-value is greater than 0.05, THEN THE System SHALL lock Logarithmic as the active transformation method
5. IF all values are not positive, THEN THE System SHALL skip logarithmic transformation and proceed to Box-Cox
6. WHERE manual override is enabled, THE System SHALL allow the user to manually select Logarithmic transformation regardless of automatic cascade results
7. WHEN Logarithmic transformation is manually selected, THE System SHALL validate that all values are greater than zero before applying the transformation

### Requirement 11: Box-Cox Transformation Attempt

**User Story:** As a quality engineer, I want the system to attempt Box-Cox transformation when logarithmic transformation fails or is not applicable, so that I can explore additional normalization options.

#### Acceptance Criteria

1. WHEN logarithmic transformation fails or is skipped, THE Transformation_Engine SHALL check if all values are greater than zero
2. IF all values are positive, THEN THE Transformation_Engine SHALL optimize lambda parameter for Box-Cox transformation
3. THE Transformation_Engine SHALL apply Box-Cox transformation with the optimized lambda
4. THE Normality_Tester SHALL perform Shapiro-Wilk test on the Box-Cox transformed data
5. IF the transformed data p-value is greater than 0.05, THEN THE System SHALL lock Box-Cox as the active transformation method with the specific lambda value
6. IF all values are not positive, THEN THE System SHALL skip Box-Cox transformation and proceed to Yeo-Johnson
7. WHERE manual override is enabled, THE System SHALL allow the user to manually select Box-Cox transformation regardless of automatic cascade results
8. WHEN Box-Cox transformation is manually selected, THE System SHALL validate that all values are greater than zero before applying the transformation

### Requirement 12: Yeo-Johnson Transformation Attempt

**User Story:** As a quality engineer, I want the system to attempt Yeo-Johnson transformation when other transformations fail, so that I can normalize data that includes zero or negative values.

#### Acceptance Criteria

1. WHEN Box-Cox transformation fails or is skipped, THE Transformation_Engine SHALL optimize lambda parameter for Yeo-Johnson transformation
2. THE Transformation_Engine SHALL apply Yeo-Johnson transformation with the optimized lambda
3. THE Normality_Tester SHALL perform Shapiro-Wilk test on the Yeo-Johnson transformed data
4. IF the transformed data p-value is greater than 0.05, THEN THE System SHALL lock Yeo-Johnson as the active transformation method with the specific lambda value
5. THE Transformation_Engine SHALL handle datasets containing zero and negative values
6. WHERE manual override is enabled, THE System SHALL allow the user to manually select Yeo-Johnson transformation regardless of automatic cascade results

### Requirement 13: Non-Parametric Fallback

**User Story:** As a quality engineer, I want the system to automatically switch to non-parametric methods when all transformation attempts fail, so that I can still perform valid statistical analysis.

#### Acceptance Criteria

1. WHEN all transformation attempts fail to achieve p-value greater than 0.05, THE System SHALL lock the method as Non-Parametric (Wilks)
2. THE System SHALL display a message indicating that data cannot be normalized
3. THE System SHALL disable parametric calculation methods for subsequent phases
4. THE System SHALL enable Wilks non-parametric calculation methods
5. WHERE manual override is enabled, THE System SHALL allow the user to manually select Non-Parametric (Wilks) method regardless of automatic cascade results

### Requirement 14: Capability Margin Calculation

**User Story:** As a quality engineer, I want the system to calculate the capability margin of my pilot data, so that I can verify that my process is capable before determining sample size.

#### Acceptance Criteria

1. WHEN the method is Parametric or transformed, THE Tolerance_Calculator SHALL forward-transform the specification limits
2. THE Tolerance_Calculator SHALL calculate the distance from the mean to each transformed specification limit
3. THE Tolerance_Calculator SHALL divide each distance by the standard deviation to get capability margins
4. THE Tolerance_Calculator SHALL set k_margin as the minimum of the calculated capability margins
5. IF k_margin is less than or equal to zero, THEN THE System SHALL display a FATAL ERROR message indicating the process is incapable and prevent further calculation

### Requirement 15: Parametric Sample Size Iteration for One-Sided Specifications

**User Story:** As a quality engineer, I want the system to iteratively determine the required sample size for one-sided specifications, so that I can ensure adequate statistical power.

#### Acceptance Criteria

1. WHEN the specification is One-Sided and the method is Parametric, THE Tolerance_Calculator SHALL calculate the one-sided tolerance factor k1 for candidate sample size N
2. THE Tolerance_Calculator SHALL use the non-central t-distribution to calculate k1
3. THE Tolerance_Calculator SHALL iterate N upward until k1(N) is less than or equal to k_margin
4. THE System SHALL return the minimum N satisfying the constraint
5. FOR ALL valid inputs, the calculated N SHALL be sufficient to achieve the specified confidence and reliability (correctness property)

### Requirement 16: Parametric Sample Size Iteration for Two-Sided Specifications

**User Story:** As a quality engineer, I want the system to iteratively determine the required sample size for two-sided specifications, so that I can ensure adequate statistical power for bilateral tolerance intervals.

#### Acceptance Criteria

1. WHEN the specification is Two-Sided and the method is Parametric, THE Tolerance_Calculator SHALL calculate the two-sided tolerance factor k2 for candidate sample size N
2. THE Tolerance_Calculator SHALL use the Howe-Guenther approximation to calculate k2
3. THE Tolerance_Calculator SHALL iterate N upward until k2(N) is less than or equal to k_margin
4. THE System SHALL return the minimum N satisfying the constraint
5. FOR ALL valid inputs, the calculated N SHALL be greater than or equal to the N for one-sided specification with the same parameters (monotonicity property)

### Requirement 17: Non-Parametric Sample Size Calculation for One-Sided Specifications

**User Story:** As a quality engineer, I want the system to calculate the required sample size using non-parametric methods for one-sided specifications, so that I can perform distribution-free analysis.

#### Acceptance Criteria

1. WHEN the specification is One-Sided and the method is Non-Parametric, THE Tolerance_Calculator SHALL calculate N using the formula n = ceiling(ln(1-C)/ln(R))
2. THE Tolerance_Calculator SHALL return an integer sample size value
3. THE System SHALL use extreme order statistics (minimum or maximum) for tolerance limit calculation
4. FOR ALL valid inputs, the formula SHALL produce the same result as the Success Run Theorem (consistency property)

### Requirement 18: Non-Parametric Sample Size Calculation for Two-Sided Specifications

**User Story:** As a quality engineer, I want the system to calculate the required sample size using non-parametric methods for two-sided specifications, so that I can perform distribution-free bilateral analysis.

#### Acceptance Criteria

1. WHEN the specification is Two-Sided and the method is Non-Parametric, THE Tolerance_Calculator SHALL iterate N until the constraint 1 - N*R^(N-1) + (N-1)*R^N >= C is satisfied
2. THE Tolerance_Calculator SHALL return the minimum integer N satisfying the constraint
3. THE System SHALL use both minimum and maximum order statistics for tolerance limit calculation
4. FOR ALL valid inputs, the calculated N SHALL be greater than or equal to the one-sided N (monotonicity property)

### Requirement 19: Final Validation Data Input and Transformation

**User Story:** As a quality engineer, I want to input my final validation dataset and have it transformed using the locked method, so that I can calculate final tolerance intervals consistently.

#### Acceptance Criteria

1. WHEN Phase 4 is initiated, THE System SHALL accept a final validation dataset of size N
2. THE System SHALL validate that the final dataset size matches the calculated required sample size N
3. THE Transformation_Engine SHALL apply the exact transformation method and lambda locked during Phase 2
4. THE System SHALL prevent the user from changing the transformation method or parameters
5. FOR ALL valid datasets, applying the locked transformation SHALL produce data in the same normalized space as the pilot data (consistency property)

### Requirement 20: Parametric Tolerance Limit Calculation

**User Story:** As a quality engineer, I want the system to calculate parametric tolerance limits in the normalized space, so that I can determine the statistical bounds of my process.

#### Acceptance Criteria

1. WHEN the method is Parametric, THE Tolerance_Calculator SHALL calculate the mean and standard deviation of the transformed final dataset
2. IF the specification is One-Sided, THEN THE Tolerance_Calculator SHALL compute the tolerance limit using the k1 factor and the formula: Limit_t = mean_t ± (k1 * std_t)
3. IF the specification is Two-Sided, THEN THE Tolerance_Calculator SHALL compute both tolerance limits using the k2 factor and the formula: Limits_t = mean_t ± (k2 * std_t)
4. THE System SHALL display the tolerance limits in the transformed space
5. FOR ALL valid datasets, the tolerance limits SHALL contain the specified proportion of the population with the specified confidence (correctness property)

### Requirement 21: Non-Parametric Tolerance Limit Calculation

**User Story:** As a quality engineer, I want the system to calculate non-parametric tolerance limits using order statistics, so that I can determine distribution-free bounds of my process.

#### Acceptance Criteria

1. WHEN the method is Non-Parametric and specification is One-Sided LSL, THE Tolerance_Calculator SHALL set the tolerance limit as the minimum value of the final dataset
2. WHEN the method is Non-Parametric and specification is One-Sided USL, THE Tolerance_Calculator SHALL set the tolerance limit as the maximum value of the final dataset
3. WHEN the method is Non-Parametric and specification is Two-Sided, THE Tolerance_Calculator SHALL set the tolerance limits as the minimum and maximum values of the final dataset
4. THE System SHALL display the tolerance limits in the original units
5. FOR ALL valid datasets, the non-parametric limits SHALL be the extreme order statistics (correctness property)

### Requirement 22: Back-Transformation of Tolerance Limits

**User Story:** As a quality engineer, I want parametric tolerance limits back-transformed to original engineering units, so that I can compare them directly to my specifications.

#### Acceptance Criteria

1. WHEN the transformation method is Logarithmic, THE Transformation_Engine SHALL back-transform using the formula: Limit_orig = exp(Limit_t)
2. WHEN the transformation method is Box-Cox, THE Transformation_Engine SHALL back-transform using the formula: Limit_orig = (lambda * Limit_t + 1)^(1/lambda)
3. WHEN the transformation method is Yeo-Johnson, THE Transformation_Engine SHALL apply the inverse Yeo-Johnson transformation with the locked lambda
4. THE System SHALL display the back-transformed limits in the original units
5. FOR ALL valid tolerance limits, back-transforming then forward-transforming SHALL produce the original transformed limit within numerical precision (round-trip property)

### Requirement 23: Pass/Fail Determination and Capability Calculation

**User Story:** As a quality engineer, I want the system to compare tolerance limits to specifications and calculate process capability, so that I can determine if my process meets requirements.

#### Acceptance Criteria

1. WHEN tolerance limits are calculated, THE System SHALL compare the back-transformed limits to the original specification limits
2. IF all tolerance limits are within the specification limits, THEN THE System SHALL display Pass
3. IF any tolerance limit exceeds a specification limit, THEN THE System SHALL display Fail
4. WHEN the method is Parametric or transformed, THE System SHALL calculate Ppk using the formula: Ppk = min(Ppu, Ppl)
5. WHEN the method is Non-Parametric, THE System SHALL hide the Ppk calculation

### Requirement 24: Sequential Workflow Enforcement

**User Story:** As a quality engineer, I want the system to prevent me from skipping workflow phases, so that I avoid statistical errors from incomplete analysis.

#### Acceptance Criteria

1. WHEN Module_V is opened, THE UI_Controller SHALL disable Phase 2 controls until Phase 1 is completed
2. WHEN Phase 1 is completed, THE UI_Controller SHALL enable Phase 2 controls and disable Phase 3 controls
3. WHEN Phase 2 is completed, THE UI_Controller SHALL enable Phase 3 controls and disable Phase 4 controls
4. WHEN Phase 3 is completed, THE UI_Controller SHALL enable Phase 4 controls
5. IF any phase input is modified, THEN THE UI_Controller SHALL disable and clear all subsequent phase results

### Requirement 25: Method Transparency Display

**User Story:** As a quality engineer, I want to see the active mathematical path being used, so that I understand which statistical methods are being applied to my data.

#### Acceptance Criteria

1. WHEN a transformation method is locked, THE UI_Controller SHALL display the active transformation method name
2. WHEN a specification type is selected, THE UI_Controller SHALL display whether one-sided or two-sided methods are active
3. WHEN a tolerance factor is calculated, THE UI_Controller SHALL display which k-factor formula is being used
4. THE System SHALL update the method transparency display dynamically as the workflow progresses
5. THE System SHALL display the complete mathematical path in a prominent text block

### Requirement 26: Contextual Tooltips for Statistical Terms

**User Story:** As a quality engineer, I want to see explanations of statistical terms when I hover over them, so that I can understand the meaning of inputs and outputs.

#### Acceptance Criteria

1. THE UI_Controller SHALL provide a tooltip for every statistical input field
2. THE UI_Controller SHALL provide a tooltip for every statistical output value
3. WHEN a user hovers over a statistical term, THE System SHALL display a concise explanation of its function
4. THE System SHALL include formula references in tooltips where applicable
5. THE System SHALL display tooltips within 500 milliseconds of hover

### Requirement 27: User Calculation Report Generation

**User Story:** As a quality engineer, I want to generate a PDF report of my calculation session, so that I can document my sample size determination for QMS records.

#### Acceptance Criteria

1. WHEN a calculation is completed, THE Report_Generator SHALL create a downloadable PDF report
2. THE Report_Generator SHALL include the date and time of the calculation
3. THE Report_Generator SHALL include all user inputs (C, R, c, specification limits, datasets)
4. THE Report_Generator SHALL include all calculated results (n, k-factors, tolerance limits, Ppk)
5. THE Report_Generator SHALL include the statistical method used
6. THE Report_Generator SHALL use reportlab with flowable paragraphs to prevent text overflow in table cells

### Requirement 28: Engine Hash Display in Reports

**User Story:** As a quality engineer, I want to see the SHA-256 hash of the calculation engine in my report, so that I can verify the code has not been altered since validation.

#### Acceptance Criteria

1. WHEN generating a user calculation report, THE Hash_Verifier SHALL calculate the SHA-256 hash of the calculations.py file
2. THE Report_Generator SHALL display the engine hash in the report with the label "Engine Hash: [HashValue]"
3. THE System SHALL calculate the hash from the current state of the calculation engine file
4. FOR ALL unchanged calculation engine files, calculating the hash multiple times SHALL produce identical results (idempotence property)

### Requirement 29: Validation State Verification in Reports

**User Story:** As a quality engineer, I want the report to indicate whether the calculation engine is in a validated state, so that I can ensure compliance with QMS requirements.

#### Acceptance Criteria

1. WHEN generating a user calculation report, THE Hash_Verifier SHALL compare the current engine hash against a stored validated hash
2. IF the hashes match, THEN THE Report_Generator SHALL print "VALIDATED STATE: YES" in the report
3. IF the hashes do not match, THEN THE Report_Generator SHALL print "VALIDATED STATE: NO - UNVERIFIED CHANGE" in the report
4. THE System SHALL store the validated hash in a configuration file
5. THE System SHALL clearly display the validation state in a prominent location in the report

### Requirement 30: Automated Validation Report Generation

**User Story:** As a validation engineer, I want the IQ/OQ/PQ test suite to generate a validation certificate PDF, so that I can document that the system has been properly validated.

#### Acceptance Criteria

1. WHEN the validation test suite completes, THE VTM_Generator SHALL create a PDF validation certificate
2. THE Report_Generator SHALL include the test execution date in the validation certificate
3. THE Report_Generator SHALL include the tester name in the validation certificate
4. THE Report_Generator SHALL include system information (OS, Python version) in the validation certificate
5. THE Report_Generator SHALL include a list of all URS IDs tested with their pass/fail status
6. THE Report_Generator SHALL include the final validated hash of the calculation engine
7. THE Report_Generator SHALL use reportlab with flowable paragraphs for the validation certificate

### Requirement 31: Installation Qualification with Version Locking

**User Story:** As a validation engineer, I want dependencies strictly version-locked using a hash-based lockfile, so that I can ensure consistent installation across environments.

#### Acceptance Criteria

1. THE System SHALL use uv as the package manager
2. THE System SHALL maintain a uv.lock file with hash-based dependency locking
3. WHEN running uv sync, THE System SHALL install dependencies without conflicts
4. THE Validation_Suite SHALL verify that scipy version 1.x.x is installed
5. THE Validation_Suite SHALL verify that all required dependencies are present

### Requirement 32: Operational Qualification with URS-Linked Tests

**User Story:** As a validation engineer, I want pytest tests that verify all mathematical models against known values, so that I can ensure the calculation engine operates correctly.

#### Acceptance Criteria

1. THE Validation_Suite SHALL include pytest tests for all mathematical formulas
2. THE Validation_Suite SHALL use pytest markers linking each test to specific URS IDs
3. THE Validation_Suite SHALL verify calculations against known standard values
4. THE Validation_Suite SHALL test edge cases for each calculation method
5. WHEN the OQ test suite runs, THE System SHALL require all tests to pass

### Requirement 33: Performance Qualification with End-to-End UI Testing

**User Story:** As a validation engineer, I want automated UI tests that simulate complete user workflows, so that I can verify the system performs correctly in realistic scenarios.

#### Acceptance Criteria

1. THE Validation_Suite SHALL use playwright for automated UI testing
2. THE Validation_Suite SHALL test the complete Module A workflow (input → calculate → verify output)
3. THE Validation_Suite SHALL test the complete Module V workflow (Phase 1 → Phase 2 → Phase 3 → Phase 4)
4. THE Validation_Suite SHALL test PDF report generation and verify report content
5. THE Validation_Suite SHALL verify that calculated values appear correctly in the UI

### Requirement 34: Verification Traceability Matrix Generation

**User Story:** As a validation engineer, I want a Verification Traceability Matrix that links requirements to tests and results, so that I can demonstrate complete validation coverage.

#### Acceptance Criteria

1. THE VTM_Generator SHALL include the URS ID and corresponding requirement text for each requirement
2. THE VTM_Generator SHALL include the test ID for each test case
3. THE VTM_Generator SHALL include the test result (passed/failed) for each test case
4. THE VTM_Generator SHALL generate the VTM in a structured format (table or CSV)
5. THE VTM_Generator SHALL include all URS IDs from the requirements document

### Requirement 35: Docker Compose Deployment

**User Story:** As a system administrator, I want to deploy the validated system using docker compose, so that I can ensure consistent installation without manual intervention.

#### Acceptance Criteria

1. THE System SHALL provide a docker-compose.yml file for deployment
2. WHEN running docker compose up, THE System SHALL start without requiring manual configuration
3. THE System SHALL reach a validated state after docker compose deployment
4. THE System SHALL expose the web interface on a configurable port
5. THE System SHALL include all required dependencies in the Docker image

### Requirement 36: NiceGUI Framework Integration

**User Story:** As a developer, I want the UI built with NiceGUI framework, so that I can provide a modern, responsive web interface.

#### Acceptance Criteria

1. THE UI_Controller SHALL use NiceGUI as the web framework
2. THE System SHALL provide a responsive web interface accessible via browser
3. THE UI_Controller SHALL organize Module A and Module V as separate tabs
4. THE UI_Controller SHALL use NiceGUI components for all user inputs and outputs
5. THE System SHALL handle concurrent user sessions independently

### Requirement 37: Single Source of Truth for Data Models

**User Story:** As a developer, I want a single point of truth for data models, so that I can maintain consistency across the application.

#### Acceptance Criteria

1. THE System SHALL define all data models in a centralized location
2. THE System SHALL use the same data model definitions across UI, calculation engine, and reporting
3. WHEN a data model is updated, THE System SHALL reflect the change in all components
4. THE System SHALL use Pydantic or dataclasses for data model definitions
5. THE System SHALL validate data against the defined models at all boundaries

### Requirement 38: Audit Trail Logging for UI Interactions and System Events

**User Story:** As a quality engineer, I want all UI interactions and important system events logged to local files with timestamps and context, so that I can audit user actions, troubleshoot issues, and maintain QMS compliance for medical device software validation.

#### Acceptance Criteria

1. WHEN a user interacts with any UI element, THE System SHALL log the event type, timestamp, user session identifier, and relevant context to a local log file
2. WHEN a user clicks a button or navigation element, THE System SHALL log the button identifier, module name, and phase context
3. WHEN a user enters or modifies input data, THE System SHALL log the field identifier, previous value, new value, and validation result
4. WHEN a calculation is performed, THE System SHALL log the calculation type, input parameters, output results, and calculation engine hash
5. WHEN a validation error occurs, THE System SHALL log the error type, error message, field identifier, and invalid value
6. WHEN a phase transition occurs in Module V, THE System SHALL log the source phase, destination phase, timestamp, and transition trigger
7. WHEN a transformation method is locked, THE System SHALL log the selected method, lambda parameter if applicable, and Shapiro-Wilk p-value
8. WHEN an outlier is excluded, THE System SHALL log the outlier value, exclusion timestamp, and engineering rationale provided by the user
9. WHEN a PDF report is generated, THE System SHALL log the report type, generation timestamp, calculation engine hash, and validation state
10. THE System SHALL store logs in a dedicated logs directory with daily rotation and retention of at least 90 days
11. THE System SHALL use ISO 8601 format for all timestamps in log entries
12. THE System SHALL include log level indicators (INFO, WARNING, ERROR) for each log entry
13. THE System SHALL ensure log files are human-readable text format with structured fields
14. THE System SHALL prevent log file corruption by using atomic write operations
15. WHEN log files reach 10MB in size, THE System SHALL rotate to a new log file with sequential numbering
16. THE System SHALL include the calculation engine hash in every calculation-related log entry for traceability
17. FOR ALL log write operations, writing the same event multiple times SHALL produce separate timestamped entries (no idempotence for logging)
