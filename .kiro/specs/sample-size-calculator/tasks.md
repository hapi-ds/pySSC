# Implementation Plan: Sample Size Calculator

## Overview

This implementation plan covers the development of a Python-based web application for medical device design verification and process validation. The system provides two analysis modules: Module A (attribute/binary data) and Module V (variable/continuous data with 4-phase workflow). The application emphasizes data integrity through SHA-256 hash verification, comprehensive audit logging, and automated validation reporting (IQ/OQ/PQ).

The implementation uses Python with NiceGUI for the web interface, Pydantic for data validation, SciPy for statistical computations, and ReportLab for PDF generation. Deployment is via Docker Compose with uv for package management.

## Tasks

- [x] 1. Project setup and infrastructure
  - Initialize Python project with uv package manager
  - Create directory structure (src/, tests/, logs/, config/)
  - Configure pyproject.toml with project metadata and dependencies
  - Add core dependencies: nicegui, pydantic, scipy, numpy, reportlab, hypothesis, pytest, playwright
  - Create .gitignore for Python project (exclude logs/, __pycache__, .venv/)
  - Set up uv.lock for hash-based dependency locking
  - _Requirements: 31.1, 31.2, 37.1_

- [x] 2. Core data models (Pydantic)
  - [x] 2.1 Create models.py with enums and base models
    - Define SpecificationType, TransformationMethod, AnalysisMethod enums
    - Create AttributeInputs model with validation (confidence, reliability, allowable_failures)
    - Create AttributeResults and SensitivityAnalysisResults models
    - _Requirements: 1.1, 1.2, 1.3, 37.4, 37.5_

  - [x] 2.2 Create Module V data models
    - Create SpecificationLimits model with validation for one-sided/two-sided specs
    - Create PilotDataInput model with dataset and statistics input methods
    - Create OutlierInfo model with exclusion tracking
    - Create Phase1Results, Phase2Results, Phase3Results, Phase4Results models
    - _Requirements: 5.2, 5.3, 6.3, 6.4, 6.8, 8.2_

  - [x] 2.3 Write property tests for data model validation
    - **Property 1: Input Validation Completeness**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

  - [x] 2.4 Create report data models
    - Create CalculationReport model for user reports
    - Create ValidationCertificate model for IQ/OQ/PQ reports
    - _Requirements: 27.2, 27.3, 27.4, 30.2, 30.3, 30.4_

- [x] 3. Calculation engine (calculations.py)
  - [x] 3.1 Implement Module A calculation methods
    - Implement success_run_theorem(confidence, reliability) using formula n = ceiling(ln(1-C)/ln(R))
    - Implement cumulative_binomial(confidence, reliability, allowable_failures) with iterative search
    - Implement sensitivity_analysis(confidence, reliability) for c=0,1,2,3
    - _Requirements: 2.1, 2.2, 3.1, 3.2, 3.3, 4.1, 4.2_

  - [x] 3.2 Write property tests for Module A calculations
    - **Property 2: Success Run Theorem Formula Correctness**
    - **Validates: Requirements 2.1, 2.2**

  - [x] 3.3 Write property tests for calculation idempotence and monotonicity
    - **Property 3: Calculation Idempotence**
    - **Validates: Requirements 2.3**
    - **Property 4: Cumulative Binomial Constraint Satisfaction**
    - **Validates: Requirements 3.1, 3.2, 3.3**
    - **Property 5: Sample Size Monotonicity with Allowable Failures**
    - **Validates: Requirements 3.4, 4.4**

  - [x] 3.4 Implement tolerance factor calculations
    - Implement one_sided_tolerance_factor(n, confidence, reliability) using non-central t-distribution
    - Implement two_sided_tolerance_factor(n, confidence, reliability) using Howe-Guenther approximation
    - Implement non_parametric_one_sided_sample_size(confidence, reliability)
    - Implement non_parametric_two_sided_sample_size(confidence, reliability)
    - _Requirements: 15.1, 15.2, 16.1, 16.2, 17.1, 18.1_

  - [x] 3.5 Write property tests for tolerance factor calculations
    - **Property 17: Sample Size Iteration Correctness**
    - **Validates: Requirements 15.3, 15.4, 16.3, 16.4**
    - **Property 18: Two-Sided Sample Size Monotonicity**
    - **Validates: Requirements 16.5, 18.4**
    - **Property 19: Non-Parametric Formula Consistency**
    - **Validates: Requirements 17.4**

- [x] 4. Transformation and statistical components
  - [x] 4.1 Create transformations.py with forward transformations
    - Implement log_transform(data) with positive value validation
    - Implement box_cox_transform(data) with lambda optimization
    - Implement yeo_johnson_transform(data) for all value ranges
    - _Requirements: 10.1, 10.2, 11.1, 11.2, 12.1, 12.2_

  - [x] 4.2 Implement inverse transformations
    - Implement inverse_log_transform(data)
    - Implement inverse_box_cox_transform(data, lambda_param)
    - Implement inverse_yeo_johnson_transform(data, lambda_param)
    - _Requirements: 22.1, 22.2, 22.3_

  - [x] 4.3 Write property tests for transformation round-trip
    - **Property 24: Back-Transformation Round-Trip**
    - **Validates: Requirements 22.1, 22.2, 22.3, 22.5**

  - [x] 4.4 Implement transformation cascade logic
    - Implement transformation_cascade(data, manual_method) with Shapiro-Wilk testing
    - Test original data, then Log → Box-Cox → Yeo-Johnson cascade
    - Lock first method achieving p-value > 0.05 or fallback to Non-Parametric
    - Support manual override for user-selected transformation
    - _Requirements: 9.3, 9.4, 10.3, 10.4, 11.3, 11.4, 12.3, 12.4, 13.1, 13.2_

  - [x] 4.5 Write property tests for transformation cascade
    - **Property 14: Transformation Cascade Logic**
    - **Validates: Requirements 10.1-10.5, 11.1-11.6, 12.1-12.4, 13.1**
    - **Property 15: Manual Override Functionality**
    - **Validates: Requirements 10.6, 10.7, 11.7, 11.8, 12.6, 13.5**

  - [x] 4.6 Create outliers.py for IQR-based detection
    - Implement detect_outliers(data) calculating Q1, Q3, IQR
    - Flag values < Q1 - 1.5*IQR or > Q3 + 1.5*IQR
    - Implement apply_exclusions(phase1_results, exclusions) with rationale validation
    - _Requirements: 7.1, 7.2, 7.3, 8.1, 8.2, 8.3, 8.5_

  - [x] 4.7 Write property tests for outlier detection
    - **Property 9: IQR Outlier Detection Correctness**
    - **Validates: Requirements 7.1, 7.2, 7.3**
    - **Property 10: Outlier Detection Idempotence**
    - **Validates: Requirements 7.5**
    - **Property 11: Outlier Exclusion Validation**
    - **Validates: Requirements 8.2, 8.3**

  - [x] 4.8 Create normality.py for Shapiro-Wilk testing
    - Implement shapiro_wilk_test(data) returning p-value
    - Implement is_normal(p_value, alpha=0.05) classification
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [x] 4.9 Write property tests for normality testing
    - **Property 13: Normality Testing and Classification**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4**

- [x] 5. Tolerance calculator (tolerance.py)
  - [x] 5.1 Implement capability margin calculation
    - Implement calculate_capability_margin(data, spec_limits, transformation_method, lambda_param)
    - Forward-transform specification limits based on transformation method
    - Calculate (mean_t - LSL_t)/std_t and (USL_t - mean_t)/std_t
    - Return minimum margin, raise ValueError if k_margin <= 0
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

  - [x] 5.2 Write property tests for capability margin
    - **Property 16: Capability Margin Calculation Correctness**
    - **Validates: Requirements 14.1, 14.2, 14.3, 14.4**

  - [x] 5.3 Implement sample size iteration
    - Implement calculate_required_sample_size(k_margin, confidence, reliability, spec_type, analysis_method)
    - Iterate N upward until k_factor(N) <= k_margin for parametric methods
    - Use direct formulas for non-parametric methods
    - Return Phase3Results with N, k_margin, k_factor, spec_type
    - _Requirements: 15.3, 15.4, 16.3, 16.4, 17.1, 17.2, 18.1, 18.2_

  - [x] 5.4 Implement tolerance limit calculation
    - Implement calculate_tolerance_limits(final_data, phase2_results, phase3_results, spec_limits)
    - Apply locked transformation to final data
    - Calculate parametric limits: mean_t ± k*std_t
    - Calculate non-parametric limits: min/max order statistics
    - Back-transform parametric limits to original space
    - _Requirements: 19.3, 20.1, 20.2, 20.3, 21.1, 21.2, 21.3_

  - [x] 5.5 Write property tests for tolerance calculations
    - **Property 20: Final Dataset Size Validation**
    - **Validates: Requirements 19.2**
    - **Property 21: Transformation Consistency**
    - **Validates: Requirements 19.3, 19.5**
    - **Property 22: Parametric Tolerance Limit Formula Correctness**
    - **Validates: Requirements 20.1, 20.2, 20.3**
    - **Property 23: Non-Parametric Tolerance Limits as Extreme Order Statistics**
    - **Validates: Requirements 21.1, 21.2, 21.3, 21.5**

  - [x] 5.6 Implement Pass/Fail determination and Ppk calculation
    - Compare back-transformed tolerance limits to specification limits
    - Set Pass if all limits within specs, Fail if any exceed
    - Calculate Ppk = min(Ppu, Ppl) for parametric methods
    - Return Phase4Results with limits, pass_fail, ppk
    - _Requirements: 23.1, 23.2, 23.3, 23.4, 23.5_

  - [x] 5.7 Write property tests for Pass/Fail and Ppk
    - **Property 25: Pass/Fail Determination Correctness**
    - **Validates: Requirements 23.1, 23.2, 23.3**
    - **Property 26: Ppk Calculation Formula**
    - **Validates: Requirements 23.4**

- [ ] 6. Checkpoint - Ensure all core calculation tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Hash verification and audit logging
  - [ ] 7.1 Create hash_verifier.py for SHA-256 verification
    - Implement calculate_file_hash(filepath) using hashlib.sha256
    - Implement get_engine_hash() for calculations.py
    - Implement get_validated_hash() and set_validated_hash(hash_value) using config/validated_hash.json
    - Implement is_validated_state() comparing current vs stored hash
    - _Requirements: 28.1, 28.3, 29.1, 29.4_

  - [ ]* 7.2 Write property tests for hash verification
    - **Property 28: Hash Calculation Idempotence**
    - **Validates: Requirements 28.4**
    - **Property 29: Validation State Determination**
    - **Validates: Requirements 29.1, 29.2, 29.3**

  - [ ] 7.3 Create audit_logger.py with comprehensive logging
    - Initialize logger with RotatingFileHandler (10MB limit, 90-day retention)
    - Implement log_ui_interaction(event_type, session_id, context)
    - Implement log_button_click(button_id, module, phase, session_id)
    - Implement log_input_change(field_id, old_value, new_value, validation_result, session_id)
    - Implement log_calculation(calc_type, inputs, outputs, engine_hash, session_id)
    - Implement log_validation_error(error_type, error_message, field_id, invalid_value, session_id)
    - Implement log_phase_transition(source_phase, dest_phase, trigger, session_id)
    - Implement log_method_lock(method, lambda_param, p_value, session_id)
    - Implement log_outlier_exclusion(outlier_value, rationale, session_id)
    - Implement log_report_generation(report_type, engine_hash, validation_state, session_id)
    - Use ISO 8601 timestamps and structured format: [TIMESTAMP] [LEVEL] [SESSION_ID] [EVENT_TYPE] {context_json}
    - _Requirements: 38.1, 38.2, 38.3, 38.4, 38.5, 38.6, 38.7, 38.8, 38.9, 38.10, 38.11, 38.12, 38.13, 38.14, 38.15, 38.16_

  - [ ]* 7.4 Write property tests for audit logging
    - **Property 34: Comprehensive Event Logging**
    - **Validates: Requirements 38.1, 38.2, 38.3, 38.4, 38.5, 38.6, 38.7, 38.8, 38.9**
    - **Property 35: Log Format Consistency**
    - **Validates: Requirements 38.11, 38.12, 38.16**
    - **Property 36: Logging Non-Idempotence**
    - **Validates: Requirements 38.17**

- [ ] 8. Report generation (ReportLab)
  - [ ] 8.1 Create report_generator.py with PDF generation
    - Implement generate_user_report(report_data) using ReportLab
    - Use Flowable paragraphs to prevent text overflow
    - Include header/footer with page numbers
    - Add sections: timestamp, inputs, results, method path, engine hash, validation state
    - Display "VALIDATED STATE: YES" or "VALIDATED STATE: NO - UNVERIFIED CHANGE"
    - _Requirements: 27.1, 27.2, 27.3, 27.4, 27.5, 27.6, 28.2, 29.2, 29.3, 29.5_

  - [ ]* 8.2 Write property tests for report generation
    - **Property 27: Report Completeness**
    - **Validates: Requirements 27.1, 27.2, 27.3, 27.4, 27.5, 28.1, 28.2, 28.3**

  - [ ] 8.3 Implement validation certificate generation
    - Implement generate_validation_certificate(cert_data)
    - Include test execution date, tester name, system info (OS, Python version)
    - Include VTM table with URS IDs, test IDs, and results
    - Include final validated hash
    - _Requirements: 30.1, 30.2, 30.3, 30.4, 30.5, 30.6, 30.7_

  - [ ]* 8.4 Write property tests for validation certificate
    - **Property 30: Validation Certificate Completeness**
    - **Validates: Requirements 30.2, 30.3, 30.4, 30.5, 30.6**

  - [ ] 8.5 Create vtm_generator.py for traceability matrix
    - Implement generate_vtm(test_results) returning DataFrame
    - Include columns: URS_ID, Requirement, Test_ID, Result
    - Implement export_vtm_csv(vtm, filepath)
    - Implement add_vtm_to_pdf(story, vtm) for PDF integration
    - _Requirements: 34.1, 34.2, 34.3, 34.4, 34.5_

  - [ ]* 8.6 Write property tests for VTM generation
    - **Property 31: Verification Traceability Matrix Completeness**
    - **Validates: Requirements 34.1, 34.2, 34.3, 34.5**

- [ ] 9. NiceGUI user interface
  - [ ] 9.1 Create ui_controller.py with session management
    - Initialize UIController with AuditLogger and session_id generation
    - Create tab-based layout with Module A and Module V tabs
    - Implement _generate_session_id() using uuid4
    - _Requirements: 36.2, 36.3, 36.5_

  - [ ] 9.2 Implement Module A UI tab
    - Create input fields: confidence, reliability, allowable_failures (optional)
    - Add tooltips for all statistical terms (500ms delay)
    - Add "Calculate Sample Size" button with click handler
    - Display results: method used, sample size (or sensitivity table for c=0,1,2,3)
    - Add "Generate PDF Report" button
    - Implement real-time validation with error messages
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 4.1, 4.2, 4.3, 26.1, 26.2, 26.3, 26.5_

  - [ ] 9.3 Implement Module V Phase 1 UI
    - Create specification type selector (One-Sided/Two-Sided radio buttons)
    - Create LSL and USL input fields with conditional visibility
    - Create confidence and reliability input fields
    - Create pilot data input method selector (Dataset/Estimated Statistics)
    - Create pilot dataset textarea and estimated mean/std inputs
    - Add "Analyze Pilot Data" button
    - Display outlier detection results: Q1, Q3, IQR, flagged outliers
    - Display warning if dataset < 30 points
    - Disable Phase 2 until Phase 1 complete
    - _Requirements: 5.1, 5.2, 5.3, 6.1, 6.2, 6.5, 7.4, 24.1_

  - [ ] 9.4 Implement Module V Phase 2 UI
    - Display detected outliers with exclude checkboxes
    - Add rationale text input for each outlier (required if excluded)
    - Add manual transformation override checkbox and method selector
    - Add "Process Normality Testing" button
    - Display transformation cascade results: p-values for each method tried
    - Display locked method and analysis method (Parametric/Non-Parametric)
    - Disable Phase 3 until Phase 2 complete
    - _Requirements: 8.1, 8.2, 10.6, 11.7, 12.6, 13.5, 24.2_

  - [ ] 9.5 Implement Module V Phase 3 UI
    - Display active method and specification type
    - Add "Calculate Required Sample Size" button
    - Display results: k_margin, k_factor, required sample size N
    - Display formula used (e.g., "Howe-Guenther Approximation")
    - Disable Phase 4 until Phase 3 complete
    - _Requirements: 24.3, 25.1, 25.2, 25.3_

  - [ ] 9.6 Implement Module V Phase 4 UI
    - Display required sample size and locked method
    - Create final validation dataset textarea
    - Add "Calculate Tolerance Limits" button
    - Display results in transformed and original space
    - Display tolerance limits, specification limits, Pass/Fail, Ppk
    - Add "Generate PDF Report" button
    - _Requirements: 19.1, 23.1, 23.2, 23.3, 24.4_

  - [ ] 9.7 Implement workflow enforcement and method transparency
    - Implement _enforce_sequential_workflow(current_phase) to enable/disable phase controls
    - Implement phase state invalidation: clear downstream phases when upstream modified
    - Implement _display_method_transparency(method_path) showing active mathematical path
    - Update transparency display dynamically as workflow progresses
    - _Requirements: 5.5, 24.1, 24.2, 24.3, 24.4, 24.5, 25.4, 25.5_

  - [ ]* 9.8 Write property tests for UI workflow and session isolation
    - **Property 6: Specification Validation**
    - **Validates: Requirements 5.2, 5.3**
    - **Property 7: Workflow State Invalidation**
    - **Validates: Requirements 5.5, 24.5**
    - **Property 33: Session Isolation**
    - **Validates: Requirements 36.5**

  - [ ] 9.9 Integrate event handlers with audit logging
    - Implement _handle_input_change(field_id, old_value, new_value) with validation and logging
    - Implement _handle_button_click(button_id, module, phase) with logging
    - Log all UI interactions through AuditLogger
    - Log phase transitions with source, destination, trigger
    - Log method locks with transformation details
    - _Requirements: 38.1, 38.2, 38.3, 38.6, 38.7_

  - [ ] 9.10 Integrate calculation engine and report generation
    - Wire Module A calculate button to CalculationEngine methods
    - Wire Module V phase buttons to respective calculation components
    - Wire report generation buttons to ReportGenerator
    - Include engine hash in all calculation logs
    - Display validation state in UI after calculations
    - _Requirements: 27.1, 28.1, 29.1, 38.4, 38.9_

- [ ] 10. Main application entry point
  - [ ] 10.1 Create main.py with NiceGUI app initialization
    - Initialize NiceGUI app with title "Sample Size Calculator"
    - Create UIController instance
    - Set up routing and page layout
    - Configure port (default 8080, configurable via environment)
    - Add startup logging
    - _Requirements: 35.4, 36.1, 36.2_

  - [ ] 10.2 Add error handling and graceful shutdown
    - Implement global exception handler
    - Log all unhandled exceptions
    - Ensure log files are flushed on shutdown
    - _Requirements: 38.14_

- [ ] 11. Checkpoint - Ensure UI and integration tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Validation test suite (IQ/OQ/PQ)
  - [ ] 12.1 Create tests/validation/test_iq.py for Installation Qualification
    - Test uv.lock file exists and has correct format
    - Test uv sync installs dependencies without conflicts
    - Verify scipy version 1.x.x is installed
    - Verify all required dependencies present (nicegui, pydantic, reportlab, numpy, hypothesis, pytest, playwright)
    - Use pytest markers: @pytest.mark.iq and @pytest.mark.urs("31.2", "31.3", "31.4", "31.5")
    - _Requirements: 31.2, 31.3, 31.4, 31.5, 32.2_

  - [ ] 12.2 Create tests/validation/test_oq.py for Operational Qualification
    - Test all Module A formulas against known standard values
    - Test Success Run Theorem: C=95%, R=95%, c=0 → n=59
    - Test Cumulative Binomial: C=95%, R=95%, c=1 → n=93
    - Test all Module V formulas against known values
    - Test transformation round-trip accuracy
    - Test tolerance factor calculations
    - Test edge cases: boundary values, zero/negative values, empty datasets
    - Use pytest markers linking each test to specific URS IDs
    - _Requirements: 32.1, 32.2, 32.3, 32.4, 32.5_

  - [ ] 12.3 Create tests/validation/test_pq.py for Performance Qualification
    - Set up playwright for automated UI testing
    - Test complete Module A workflow: input → calculate → verify output → generate report
    - Test complete Module V workflow: Phase 1 → Phase 2 → Phase 3 → Phase 4 → generate report
    - Test PDF report generation and verify content (timestamp, inputs, results, hash, validation state)
    - Verify calculated values appear correctly in UI
    - Test concurrent user sessions with independent state
    - Use pytest markers: @pytest.mark.pq and @pytest.mark.urs(...)
    - _Requirements: 33.1, 33.2, 33.3, 33.4, 33.5_

  - [ ] 12.4 Create validation report generation script
    - Create script to run full validation suite (IQ + OQ + PQ)
    - Collect test results with URS ID mapping
    - Generate VTM using vtm_generator
    - Generate validation certificate PDF with test results
    - Store validated hash in config/validated_hash.json
    - _Requirements: 30.1, 34.4_

- [ ] 13. Docker deployment
  - [ ] 13.1 Create Dockerfile with multi-stage build
    - Use python:3.11-slim as base image
    - Install uv in builder stage
    - Copy pyproject.toml and uv.lock
    - Run uv sync --frozen --no-dev
    - Create production stage with non-root user (appuser)
    - Copy .venv from builder
    - Copy src/ and config/ directories
    - Create logs/ directory with correct permissions
    - Expose port 8080
    - Add healthcheck using HTTP request to localhost:8080
    - Set CMD to run main.py
    - _Requirements: 35.1, 35.5_

  - [ ] 13.2 Create docker-compose.yml for deployment
    - Define sample-size-calculator service
    - Map port ${PORT:-8080}:8080
    - Mount volumes: ./logs:/app/logs and ./config:/app/config:ro
    - Set environment variables: LOG_LEVEL, LOG_RETENTION_DAYS
    - Configure restart: unless-stopped
    - Add healthcheck configuration
    - _Requirements: 35.1, 35.2, 35.4_

  - [ ] 13.3 Create .dockerignore file
    - Exclude __pycache__/, *.pyc, .venv/, logs/, .git/, tests/, .pytest_cache/
    - _Requirements: 35.5_

  - [ ] 13.4 Test Docker deployment
    - Build image: docker compose build
    - Start container: docker compose up -d
    - Verify web interface accessible at http://localhost:8080
    - Verify validated state after deployment
    - Test log file persistence in mounted volume
    - _Requirements: 35.2, 35.3_

- [ ] 14. Documentation and configuration
  - [ ] 14.1 Create comprehensive README.md
    - Add project overview and features
    - Add installation instructions (uv sync)
    - Add usage instructions for both modules
    - Add Docker deployment instructions
    - Add validation instructions (running IQ/OQ/PQ suite)
    - Add development setup instructions
    - Add architecture overview
    - Add troubleshooting section
    - _Requirements: 35.2_

  - [ ] 14.2 Create config/validated_hash.json template
    - Create JSON structure with validated_hash, validation_date, validator fields
    - Initialize with empty/placeholder values
    - _Requirements: 29.4_

  - [ ] 14.3 Create .env.example file
    - Add PORT=8080
    - Add LOG_LEVEL=INFO
    - Add LOG_RETENTION_DAYS=90
    - _Requirements: 35.4_

  - [ ] 14.4 Add inline code documentation
    - Add docstrings to all public functions and classes
    - Use Google docstring style
    - Include type information and examples
    - Add comments for complex statistical formulas with references
    - _Requirements: 26.4_

- [ ] 15. Final validation and testing
  - [ ] 15.1 Run complete test suite
    - Run unit tests: uv run pytest tests/unit/ -q
    - Run property tests: uv run pytest tests/property/ -q
    - Run integration tests: uv run pytest tests/integration/ -q
    - Verify all tests pass
    - _Requirements: 32.5_

  - [ ] 15.2 Run validation suite and generate certificate
    - Run IQ tests: uv run pytest tests/validation/test_iq.py -v
    - Run OQ tests: uv run pytest tests/validation/test_oq.py -v
    - Run PQ tests: uv run pytest tests/validation/test_pq.py -v
    - Generate validation certificate PDF
    - Store validated hash
    - _Requirements: 30.1, 31.3, 32.5_

  - [ ] 15.3 Run code quality checks
    - Run ruff linter: uv run ruff check src/
    - Run ruff formatter: uv run ruff format src/
    - Run type checker: uvx ty check src/
    - Fix all warnings and errors
    - _Requirements: Code quality standards_

  - [ ] 15.4 Verify Docker deployment end-to-end
    - Build and start: docker compose up -d
    - Access UI and perform Module A calculation
    - Access UI and perform Module V 4-phase workflow
    - Generate and download PDF reports
    - Verify logs are written to mounted volume
    - Verify validation state is YES
    - Stop: docker compose down
    - _Requirements: 35.2, 35.3_

- [ ] 16. Final checkpoint - System ready for deployment
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional property-based tests and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties using Hypothesis
- Unit tests validate specific examples and edge cases
- The validation suite (IQ/OQ/PQ) ensures QMS compliance for medical device software
- All code follows Python best practices: PEP 8, type hints, docstrings
- Package management uses uv exclusively with hash-based lockfile
- Docker deployment ensures consistent installation across environments
