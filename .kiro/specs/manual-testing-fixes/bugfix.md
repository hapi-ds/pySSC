# Bugfix Requirements Document

## Introduction

This document captures bugs discovered during manual testing of the Sample Size Calculator application. The issues span nine areas: Phase 4 validation logic, Yeo-Johnson transformation round-trip behavior, UI workflow state management, missing help documentation, Phase 2 manual override method selection limitations, missing normality test diagnostic plots, incomplete help page content, insufficient normality testing methodology, and PDF report formatting. These bugs affect the usability and correctness of the Module V variable data analysis workflow.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN Phase 4 receives final validation data with sample size greater than the calculated required sample size N THEN the system rejects the data with a validation error stating "Final dataset must contain exactly N data points"

1.2 WHEN Yeo-Johnson transformation is applied with lambda=-7.545504735605443 to the dataset [23.0, 24.0, 27.0] THEN the system fails the round-trip property test (transform then inverse transform does not return to original values)

1.3 WHEN Phase 3 sample size calculation is completed THEN the system does not disable Phase 3 controls, allowing users to recalculate and potentially invalidate downstream Phase 4 results

1.4 WHEN users navigate the application interface THEN the system displays only two tabs (Module A and Module V) without providing help documentation or guidance on how to use the application

1.5 WHEN users enable Manual Override in Phase 2 THEN the system restricts method selection to only "Parametric", preventing selection of other available transformation/analysis methods (None/Parametric, Logarithmic, Box-Cox, Yeo-Johnson, Non-Parametric/Wilks)

1.6 WHEN Phase 2 normality testing is performed THEN the system displays only the Shapiro-Wilk p-value without providing visual diagnostic plots (Q-Q plot, P-P plot, I-MR chart) to help users assess normality

1.7 WHEN the Help tab is created and users access it THEN the system does not display comprehensive "how to use" documentation explaining Module A usage, Module V 4-phase workflow, statistical terms and methods, or step-by-step guidance for common workflows

1.8 WHEN Phase 2 normality assessment is performed THEN the system performs only the Shapiro-Wilk test without conducting a second normality test (e.g., Anderson-Darling test) to provide more robust normality assessment

1.9 WHEN PDF report is generated with calculation results THEN the system displays results in a list format instead of using a well-formatted table with proper columns, rows, headers, and alignment

### Expected Behavior (Correct)

2.1 WHEN Phase 4 receives final validation data with sample size greater than or equal to the calculated required sample size N THEN the system SHALL accept the data and proceed with tolerance limit calculations

2.2 WHEN Yeo-Johnson transformation is applied with any valid lambda parameter to any dataset THEN the system SHALL ensure round-trip transformation (transform then inverse transform) returns values within acceptable numerical precision of the original values

2.3 WHEN Phase 3 sample size calculation is completed THEN the system SHALL disable Phase 3 controls to prevent recalculation that would invalidate Phase 4 results

2.4 WHEN users navigate the application interface THEN the system SHALL display a third "Help" tab containing documentation and guidance on how to use the application features

2.5 WHEN users enable Manual Override in Phase 2 THEN the system SHALL allow free selection from all available transformation/analysis methods (None/Parametric, Logarithmic, Box-Cox, Yeo-Johnson, Non-Parametric/Wilks)

2.6 WHEN Phase 2 normality testing is performed THEN the system SHALL display visual diagnostic plots including Q-Q plot (Quantile-Quantile plot comparing data distribution against theoretical normal distribution), P-P plot (Probability-Probability plot for cumulative distribution comparison), and I-MR chart (Individual Moving Range chart for process stability assessment) alongside the Shapiro-Wilk p-value

2.7 WHEN the Help tab is created and users access it THEN the system SHALL display comprehensive "how to use" documentation including how to use Module A for attribute data analysis, how to use Module V with the 4-phase workflow, explanation of statistical terms and methods, and step-by-step guidance for common workflows

2.8 WHEN Phase 2 normality assessment is performed THEN the system SHALL perform at least two normality tests (Shapiro-Wilk and Anderson-Darling) and display all test results with their respective test statistics and p-values/critical values to provide robust normality assessment

2.9 WHEN PDF report is generated with calculation results THEN the system SHALL display results in a professional table format with proper columns, rows, headers, and alignment for better readability and professional appearance

### Unchanged Behavior (Regression Prevention)

3.1 WHEN Phase 4 receives final validation data with sample size less than the calculated required sample size N THEN the system SHALL CONTINUE TO reject the data with an appropriate validation error

3.2 WHEN logarithmic or Box-Cox transformations are applied to datasets THEN the system SHALL CONTINUE TO maintain round-trip transformation accuracy within acceptable numerical precision

3.3 WHEN Phase 1 or Phase 2 are completed THEN the system SHALL CONTINUE TO enable the next phase while disabling downstream phases that depend on potentially changed data

3.4 WHEN Phase 4 tolerance limit calculations are performed with valid data THEN the system SHALL CONTINUE TO produce correct tolerance limits, pass/fail results, and Ppk values

3.5 WHEN users navigate between Module A and Module V tabs THEN the system SHALL CONTINUE TO maintain proper tab functionality and state management

3.6 WHEN users do not enable Manual Override in Phase 2 THEN the system SHALL CONTINUE TO automatically select the appropriate transformation/analysis method based on the data characteristics

3.7 WHEN Phase 2 normality testing is performed with transformations applied THEN the system SHALL CONTINUE TO display the Shapiro-Wilk p-value and transformation parameters

3.8 WHEN users access Module A or Module V tabs THEN the system SHALL CONTINUE TO display the respective analysis interfaces with proper functionality

3.9 WHEN Phase 2 normality assessment is performed with the Shapiro-Wilk test THEN the system SHALL CONTINUE TO display the Shapiro-Wilk test statistic and p-value as part of the normality assessment results

3.10 WHEN PDF report is generated with other content sections (headers, metadata, charts, analysis text) THEN the system SHALL CONTINUE TO format those sections correctly and maintain overall PDF structure and layout
