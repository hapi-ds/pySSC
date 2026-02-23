# Implementation Plan

## Phase 1: Bug Condition Exploration Tests (BEFORE fixes)

- [ ] 1. Write bug condition exploration tests for all 9 bugs
  - **Property 1: Fault Condition** - Multi-Bug Exploration Suite
  - **CRITICAL**: These tests MUST FAIL on unfixed code - failures confirm bugs exist
  - **DO NOT attempt to fix tests or code when they fail**
  - **NOTE**: These tests encode expected behaviors - they validate fixes when passing after implementation
  - **GOAL**: Surface counterexamples demonstrating each bug exists
  - Write exploration test for Bug 1 (Phase 4 validation with N+5 samples)
  - Write exploration test for Bug 2 (Yeo-Johnson round-trip with lambda=-7.545)
  - Write exploration test for Bug 3 (Phase 3 controls remain enabled after completion)
  - Write exploration test for Bug 4 (Only 2 tabs visible, no Help tab)
  - Write exploration test for Bug 5 (Manual override shows only "Parametric")
  - Write exploration test for Bug 6 (No Q-Q, P-P, I-MR plots displayed)
  - Write exploration test for Bug 7 (Help tab empty or incomplete)
  - Write exploration test for Bug 8 (Only Shapiro-Wilk test, no Anderson-Darling)
  - Write exploration test for Bug 9 (PDF results in list format, not table)
  - Run all tests on UNFIXED code
  - **EXPECTED OUTCOME**: All 9 tests FAIL (confirms bugs exist)
  - Document counterexamples for each bug to understand root causes
  - Mark task complete when tests written, run, and failures documented
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9_

## Phase 2: Preservation Property Tests (BEFORE fixes)

- [ ] 2. Write preservation property tests for non-buggy behaviors
  - **Property 2: Preservation** - Multi-Bug Preservation Suite
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for all non-buggy inputs
  - Write property-based tests capturing observed behavior patterns
  - Test Preservation 1: Phase 4 rejects datasets with size < N
  - Test Preservation 2: Logarithmic and Box-Cox maintain round-trip accuracy
  - Test Preservation 3: Phase 1 and Phase 2 state management unchanged
  - Test Preservation 4: Phase 4 tolerance calculations produce correct results
  - Test Preservation 5: Module A and Module V tab navigation works properly
  - Test Preservation 6: Automatic method selection (non-manual override) works
  - Test Preservation 7: Phase 2 transformation parameters display correctly
  - Test Preservation 8: Module A and Module V interfaces function properly
  - Test Preservation 9: Shapiro-Wilk test continues displaying in results
  - Test Preservation 10: PDF non-table sections maintain formatting
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: All preservation tests PASS (confirms baseline behavior)
  - Mark task complete when tests written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10_


## Phase 3: Implementation

- [ ] 3. Fix Bug 1: Phase 4 Validation Too Strict

  - [ ] 3.1 Implement Phase 4 validation fix
    - Locate validation check in `ui_controller.py` Phase 4 handler
    - Change `len(final_data) == required_n` to `len(final_data) >= required_n`
    - Update error message to reflect "at least N" instead of "exactly N"
    - Add informational message if len > N (e.g., "Using all N+ samples")
    - _Bug_Condition: isBug1Condition(input) where len(final_dataset) > required_n_
    - _Expected_Behavior: Validation accepts data and proceeds with tolerance calculations_
    - _Preservation: Phase 4 must continue rejecting datasets with size < N (3.1)_
    - _Requirements: 2.1, 3.1_

  - [ ] 3.2 Verify Bug 1 exploration test now passes
    - **Property 1: Expected Behavior** - Phase 4 Accepts N or More Samples
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - Run Bug 1 exploration test with N+5 samples
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1_

  - [ ] 3.3 Verify Bug 1 preservation tests still pass
    - **Property 2: Preservation** - Phase 4 Rejects Insufficient Samples
    - **IMPORTANT**: Re-run relevant preservation tests from task 2
    - Run preservation test for Phase 4 rejection with size < N
    - Run preservation test for Phase 4 tolerance calculations
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)

- [ ] 4. Fix Bug 2: Yeo-Johnson Round-Trip Failure

  - [ ] 4.1 Implement Yeo-Johnson numerical stability fix
    - Locate `yeo_johnson_transform` and `inverse_yeo_johnson_transform` in `transformations.py`
    - Add numerical stability checks for extreme lambda values
    - Implement safeguards: clamp intermediate results to prevent overflow/underflow
    - Use `np.clip` or conditional logic for extreme values
    - Enhance inverse transform with epsilon tolerance for division operations
    - Handle edge cases where lambda is very negative or very positive
    - Consider log-space arithmetic for extreme values
    - Add round-trip validation with epsilon=1e-10 tolerance
    - _Bug_Condition: isBug2Condition(input) where round-trip fails with extreme lambda_
    - _Expected_Behavior: Round-trip returns values within epsilon=1e-10 of original_
    - _Preservation: Logarithmic and Box-Cox transformations maintain accuracy (3.2)_
    - _Requirements: 2.2, 3.2_

  - [ ] 4.2 Verify Bug 2 exploration test now passes
    - **Property 1: Expected Behavior** - Yeo-Johnson Round-Trip Accuracy
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - Run Bug 2 exploration test with lambda=-7.545 and data=[23.0, 24.0, 27.0]
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.2_

  - [ ] 4.3 Verify Bug 2 preservation tests still pass
    - **Property 2: Preservation** - Other Transformations Maintain Accuracy
    - **IMPORTANT**: Re-run relevant preservation tests from task 2
    - Run preservation tests for logarithmic and Box-Cox round-trip accuracy
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)


- [ ] 5. Fix Bug 3: Phase 3 UI State Not Disabled

  - [ ] 5.1 Implement Phase 3 state management fix
    - Locate `complete_phase3` method in `ModuleVState` class in `ui_controller.py`
    - Store references to Phase 3 input components in `_create_phase3_ui`
    - Add instance variables for Phase 3 controls (textboxes, buttons, dropdowns)
    - In `complete_phase3`, set `interactive=False` on all Phase 3 controls
    - Update `_enforce_sequential_workflow` to check Phase 3 completion status
    - Disable Phase 3 controls if phase is completed
    - _Bug_Condition: isBug3Condition(input) where phase3_completed and controls_enabled_
    - _Expected_Behavior: Phase 3 controls disabled after completion_
    - _Preservation: Phase 1 and Phase 2 state management unchanged (3.3)_
    - _Requirements: 2.3, 3.3_

  - [ ] 5.2 Verify Bug 3 exploration test now passes
    - **Property 1: Expected Behavior** - Phase 3 Controls Disabled After Completion
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - Run Bug 3 exploration test for Phase 3 completion
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.3_

  - [ ] 5.3 Verify Bug 3 preservation tests still pass
    - **Property 2: Preservation** - Phase 1 and Phase 2 State Management
    - **IMPORTANT**: Re-run relevant preservation tests from task 2
    - Run preservation tests for Phase 1 and Phase 2 state transitions
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)

- [ ] 6. Fix Bug 4: Missing Help Tab

  - [ ] 6.1 Implement Help tab creation
    - Create `create_help_tab` method in `UIController` class in `ui_controller.py`
    - Follow pattern of `create_module_a_tab` and `create_module_v_tab`
    - Use Gradio Markdown or HTML components for content display
    - Modify `create_app` method to add third tab after Module A and Module V
    - Call `create_help_tab()` in Tabs component creation
    - Structure Help content into sections (placeholder content for now)
    - _Bug_Condition: isBug4Condition(input) where "Help" NOT IN tab_list_
    - _Expected_Behavior: Third "Help" tab visible alongside Module A and Module V_
    - _Preservation: Module A and Module V tab navigation unchanged (3.5)_
    - _Requirements: 2.4, 3.5_

  - [ ] 6.2 Verify Bug 4 exploration test now passes
    - **Property 1: Expected Behavior** - Help Tab Exists
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - Run Bug 4 exploration test for tab list
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.4_

  - [ ] 6.3 Verify Bug 4 preservation tests still pass
    - **Property 2: Preservation** - Tab Navigation Functionality
    - **IMPORTANT**: Re-run relevant preservation tests from task 2
    - Run preservation tests for Module A and Module V tab navigation
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)


- [ ] 7. Fix Bug 5: Phase 2 Manual Override Limited to Parametric

  - [ ] 7.1 Implement manual override method selection fix
    - Locate manual override dropdown in `_create_phase2_ui` method in `ui_controller.py`
    - Update dropdown choices from ["Parametric"] to full method list
    - Set choices: ["None/Parametric", "Logarithmic", "Box-Cox", "Yeo-Johnson", "Non-Parametric/Wilks"]
    - Verify transformation_cascade function supports all method types
    - Update any conditional logic that assumes only "Parametric"
    - Test method name mapping to backend method identifiers
    - _Bug_Condition: isBug5Condition(input) where manual_override and only "Parametric" available_
    - _Expected_Behavior: All 5 methods selectable when manual override enabled_
    - _Preservation: Automatic method selection (non-override) unchanged (3.6)_
    - _Requirements: 2.5, 3.6_

  - [ ] 7.2 Verify Bug 5 exploration test now passes
    - **Property 1: Expected Behavior** - Manual Override Allows All Methods
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - Run Bug 5 exploration test for manual override method list
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.5_

  - [ ] 7.3 Verify Bug 5 preservation tests still pass
    - **Property 2: Preservation** - Automatic Method Selection
    - **IMPORTANT**: Re-run relevant preservation tests from task 2
    - Run preservation tests for automatic method selection without override
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)

- [ ] 8. Fix Bug 6: Missing Normality Diagnostic Plots

  - [ ] 8.1 Implement normality diagnostic plots
    - Create helper methods in `ui_controller.py` for plot generation
    - Add `_generate_qq_plot(data)` using `scipy.stats.probplot`
    - Add `_generate_pp_plot(data)` using cumulative distributions
    - Add `_generate_imr_chart(data)` for process stability (Individual and Moving Range)
    - Add three `gr.Plot()` or `gr.Image()` components in Phase 2 UI
    - Position plots below or alongside Shapiro-Wilk p-value display
    - Update normality test handler to generate all three plots
    - Return plot objects to display in UI
    - Maintain existing p-value display
    - _Bug_Condition: isBug6Condition(input) where normality_test and no plots displayed_
    - _Expected_Behavior: Q-Q, P-P, and I-MR plots displayed with p-value_
    - _Preservation: Transformation parameter display unchanged (3.7)_
    - _Requirements: 2.6, 3.7_

  - [ ] 8.2 Verify Bug 6 exploration test now passes
    - **Property 1: Expected Behavior** - Normality Diagnostic Plots Displayed
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - Run Bug 6 exploration test for normality testing display
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.6_

  - [ ] 8.3 Verify Bug 6 preservation tests still pass
    - **Property 2: Preservation** - Transformation Parameter Display
    - **IMPORTANT**: Re-run relevant preservation tests from task 2
    - Run preservation tests for Phase 2 transformation parameter display
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)


- [ ] 9. Fix Bug 7: Missing Help Page Content

  - [ ] 9.1 Implement comprehensive Help page content
    - Populate `create_help_tab` method with comprehensive documentation
    - Write Module A section: purpose, input requirements, calculation methodology, interpretation
    - Write Module V section: purpose, 4-phase workflow (Phase 1-4 detailed explanations)
    - Write Statistical Terms Glossary: Shapiro-Wilk, Anderson-Darling, transformations, plots, tolerance limits, Ppk
    - Write Step-by-Step Workflows: common use cases, decision trees, troubleshooting
    - Format content using Markdown for readability
    - Use headers, bullet points, code blocks for data examples
    - Consider using Gradio Accordion for collapsible sections
    - _Bug_Condition: isBug7Condition(input) where help_tab exists but content incomplete_
    - _Expected_Behavior: Comprehensive documentation with all 4 sections_
    - _Preservation: Module A and Module V interfaces unchanged (3.8)_
    - _Requirements: 2.7, 3.8_

  - [ ] 9.2 Verify Bug 7 exploration test now passes
    - **Property 1: Expected Behavior** - Help Page Contains Comprehensive Documentation
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - Run Bug 7 exploration test for Help content completeness
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.7_

  - [ ] 9.3 Verify Bug 7 preservation tests still pass
    - **Property 2: Preservation** - Module Interfaces Functionality
    - **IMPORTANT**: Re-run relevant preservation tests from task 2
    - Run preservation tests for Module A and Module V interface functionality
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)

- [ ] 10. Fix Bug 8: Missing Anderson-Darling Test

  - [ ] 10.1 Implement Anderson-Darling test
    - Create `anderson_darling_test` function in `normality.py`
    - Use `scipy.stats.anderson(data, dist='norm')`
    - Return tuple: (statistic, critical_values, significance_levels)
    - Update UI display in `ui_controller.py` Phase 2 normality testing
    - Call both `shapiro_wilk_test` and `anderson_darling_test`
    - Display both results in UI
    - Format Shapiro-Wilk: "statistic=X, p-value=Y"
    - Format Anderson-Darling: "statistic=X, critical values at [15%, 10%, 5%, 2.5%, 1%]"
    - Update transformation_cascade if normality decisions use test results
    - Document decision logic for using both tests
    - _Bug_Condition: isBug8Condition(input) where only Shapiro-Wilk performed_
    - _Expected_Behavior: Both Shapiro-Wilk and Anderson-Darling tests performed and displayed_
    - _Preservation: Shapiro-Wilk test continues displaying (3.9)_
    - _Requirements: 2.8, 3.9_

  - [ ] 10.2 Verify Bug 8 exploration test now passes
    - **Property 1: Expected Behavior** - Two Normality Tests Performed
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - Run Bug 8 exploration test for normality test count
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.8_

  - [ ] 10.3 Verify Bug 8 preservation tests still pass
    - **Property 2: Preservation** - Shapiro-Wilk Test Display
    - **IMPORTANT**: Re-run relevant preservation tests from task 2
    - Run preservation tests for Shapiro-Wilk test display
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)


- [ ] 11. Fix Bug 9: PDF Report List Format Instead of Table

  - [ ] 11.1 Implement PDF table formatting
    - Locate results section rendering in `report_generator.py` in `generate_user_report` method
    - Find list-based rendering code (likely using Paragraph with bullet points)
    - Replace with ReportLab Table class
    - Import: `from reportlab.platypus import Table, TableStyle` and `from reportlab.lib import colors`
    - Create table data structure with header row and data rows
    - Define table columns: ['Parameter', 'Value', 'Unit']
    - Apply professional table styling: header background, borders, alignment, fonts
    - Set column widths appropriately (e.g., [200, 150, 100])
    - Maintain other PDF sections unchanged (headers, metadata, charts, analysis text)
    - _Bug_Condition: isBug9Condition(input) where results_section_format == "list"_
    - _Expected_Behavior: Results displayed in professional table format_
    - _Preservation: PDF non-table sections maintain formatting (3.10)_
    - _Requirements: 2.9, 3.10_

  - [ ] 11.2 Verify Bug 9 exploration test now passes
    - **Property 1: Expected Behavior** - PDF Report Uses Table Format
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - Run Bug 9 exploration test for PDF report format
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.9_

  - [ ] 11.3 Verify Bug 9 preservation tests still pass
    - **Property 2: Preservation** - PDF Non-Table Sections Formatting
    - **IMPORTANT**: Re-run relevant preservation tests from task 2
    - Run preservation tests for PDF non-table sections (headers, metadata, charts, analysis)
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)

## Phase 4: Comprehensive Testing

- [ ] 12. Unit tests for all bug fixes

  - [ ] 12.1 Write unit tests for Bug 1 (Phase 4 validation)
    - Test with N samples (should accept)
    - Test with N+1 samples (should accept)
    - Test with N+10 samples (should accept)
    - Test with N-1 samples (should reject - preservation)
    - _Requirements: 2.1, 3.1_

  - [ ] 12.2 Write unit tests for Bug 2 (Yeo-Johnson round-trip)
    - Test with lambda values: -10, -7.545, -1, 0, 1, 7.545, 10
    - Test with various datasets: small, large, with zeros, with negatives
    - Verify round-trip accuracy within epsilon=1e-10
    - Test logarithmic and Box-Cox maintain accuracy (preservation)
    - _Requirements: 2.2, 3.2_

  - [ ] 12.3 Write unit tests for Bug 3 (Phase 3 state management)
    - Test Phase 3 completion disables all controls
    - Test Phase 1 and Phase 2 state transitions unchanged (preservation)
    - Verify Phase 4 enabled after Phase 3 completion
    - _Requirements: 2.3, 3.3_

  - [ ] 12.4 Write unit tests for Bug 4 (Help tab)
    - Test tab list contains exactly ["Module A", "Module V", "Help"]
    - Test tab navigation between all three tabs
    - Verify Module A and Module V navigation unchanged (preservation)
    - _Requirements: 2.4, 3.5_

  - [ ] 12.5 Write unit tests for Bug 5 (Manual override)
    - Test manual override dropdown contains all 5 methods
    - Test each method selection works correctly
    - Test automatic selection without override unchanged (preservation)
    - _Requirements: 2.5, 3.6_

  - [ ] 12.6 Write unit tests for Bug 6 (Diagnostic plots)
    - Test normality testing returns 3 plot objects (Q-Q, P-P, I-MR)
    - Verify plots are valid matplotlib figures
    - Test transformation parameter display unchanged (preservation)
    - _Requirements: 2.6, 3.7_

  - [ ] 12.7 Write unit tests for Bug 7 (Help content)
    - Test Help content has all 4 required sections
    - Verify each section has non-empty text
    - Test Module A and Module V interfaces unchanged (preservation)
    - _Requirements: 2.7, 3.8_

  - [ ] 12.8 Write unit tests for Bug 8 (Anderson-Darling)
    - Test normality assessment returns both test results
    - Verify Shapiro-Wilk and Anderson-Darling statistics present
    - Test Shapiro-Wilk continues displaying (preservation)
    - _Requirements: 2.8, 3.9_

  - [ ] 12.9 Write unit tests for Bug 9 (PDF table)
    - Test PDF report results section uses Table class
    - Verify table has proper structure (columns, rows, headers)
    - Test PDF non-table sections unchanged (preservation)
    - _Requirements: 2.9, 3.10_

  - [ ] 12.10 Run all unit tests
    - Execute: `uv run pytest -q tests/test_manual_fixes_unit.py`
    - Verify all tests pass
    - Check test coverage for modified functions (aim for >90%)


- [ ] 13. Property-based tests for fix verification

  - [ ] 13.1 Write PBT for Bug 1 (Phase 4 validation)
    - **Property 1: Expected Behavior** - Phase 4 Accepts N or More Samples
    - Generate random datasets with size >= N (use hypothesis strategies)
    - Verify all accepted and proceed with tolerance calculations
    - Test with N=10, 30, 50, 100 and dataset sizes up to N+50
    - _Requirements: 2.1_

  - [ ] 13.2 Write PBT for Bug 2 (Yeo-Johnson round-trip)
    - **Property 1: Expected Behavior** - Yeo-Johnson Round-Trip Accuracy
    - Generate random data (floats, including zeros and negatives)
    - Generate random lambda values in range [-10, 10]
    - Verify round-trip accuracy within epsilon=1e-10 for all combinations
    - Use hypothesis: `@given(st.lists(st.floats()), st.floats(min_value=-10, max_value=10))`
    - _Requirements: 2.2_

  - [ ] 13.3 Write PBT for Bug 3 (UI state management)
    - **Property 1: Expected Behavior** - Phase 3 Controls Disabled After Completion
    - Generate random phase completion sequences
    - Verify proper disabling after Phase 3 completion in all scenarios
    - _Requirements: 2.3_

  - [ ] 13.4 Write PBT for Bug 5 (Manual override)
    - **Property 1: Expected Behavior** - Manual Override Allows All Methods
    - Generate random manual override scenarios
    - Verify all 5 methods available in all cases
    - _Requirements: 2.5_

  - [ ] 13.5 Write PBT for Bug 6 (Diagnostic plots)
    - **Property 1: Expected Behavior** - Normality Diagnostic Plots Displayed
    - Generate random datasets for normality testing
    - Verify all 3 plots generated for all datasets
    - _Requirements: 2.6_

  - [ ] 13.6 Write PBT for Bug 8 (Anderson-Darling)
    - **Property 1: Expected Behavior** - Two Normality Tests Performed
    - Generate random datasets for normality assessment
    - Verify both tests performed and results returned for all datasets
    - _Requirements: 2.8_

  - [ ] 13.7 Run all property-based tests
    - Execute: `uv run pytest -q tests/test_manual_fixes_properties.py`
    - Use reasonable example counts (e.g., 100 examples per property)
    - Verify all properties hold

- [ ] 14. Property-based tests for preservation

  - [ ] 14.1 Write PBT for Preservation 1 (Phase 4 rejection)
    - **Property 2: Preservation** - Phase 4 Rejects Insufficient Samples
    - Generate random datasets with size < N
    - Verify rejection behavior maintained (same as original)
    - _Requirements: 3.1_

  - [ ] 14.2 Write PBT for Preservation 2 (Other transformations)
    - **Property 2: Preservation** - Other Transformations Maintain Accuracy
    - Generate random data for logarithmic and Box-Cox transformations
    - Verify round-trip accuracy maintained (same as original)
    - _Requirements: 3.2_

  - [ ] 14.3 Write PBT for Preservation 3 (Phase 1/2 state)
    - **Property 2: Preservation** - Phase 1 and Phase 2 State Management
    - Generate random Phase 1 and Phase 2 completion events
    - Verify state transitions unchanged (same as original)
    - _Requirements: 3.3_

  - [ ] 14.4 Write PBT for Preservation 4 (Phase 4 calculations)
    - **Property 2: Preservation** - Phase 4 Calculation Correctness
    - Generate random valid Phase 4 data
    - Verify tolerance limits, pass/fail, Ppk unchanged (same as original)
    - _Requirements: 3.4_

  - [ ] 14.5 Write PBT for Preservation 6 (Automatic selection)
    - **Property 2: Preservation** - Automatic Method Selection
    - Generate random data without manual override
    - Verify automatic method selection unchanged (same as original)
    - _Requirements: 3.6_

  - [ ] 14.6 Run all preservation property-based tests
    - Execute: `uv run pytest -q tests/test_manual_fixes_preservation.py`
    - Verify all preservation properties hold
    - Confirm no regressions introduced


- [ ] 15. Integration tests for end-to-end workflows

  - [ ] 15.1 Test complete Module V workflow with N+ samples
    - Phase 1: Upload initial data with outliers
    - Phase 2: Perform normality testing, verify diagnostic plots and both tests displayed
    - Phase 3: Calculate sample size N
    - Phase 4: Upload N+5 samples, verify acceptance and correct tolerance calculations
    - Generate PDF report, verify table formatting
    - Validates: Bugs 1, 6, 8, 9 in realistic workflow
    - _Requirements: 2.1, 2.6, 2.8, 2.9_

  - [ ] 15.2 Test manual override full workflow
    - Phase 1: Upload data
    - Phase 2: Enable manual override, verify all 5 methods available
    - Select each method sequentially (None/Parametric, Logarithmic, Box-Cox, Yeo-Johnson, Non-Parametric/Wilks)
    - Verify transformations work for each method
    - Phase 3: Calculate sample size
    - Phase 4: Complete validation
    - Validates: Bug 5 with complete workflow
    - _Requirements: 2.5_

  - [ ] 15.3 Test UI state management workflow
    - Phase 1: Complete, verify Phase 2 enabled
    - Phase 2: Complete, verify Phase 3 enabled
    - Phase 3: Complete, verify controls disabled and Phase 4 enabled
    - Attempt to modify Phase 3, verify prevented
    - Phase 4: Complete workflow
    - Validates: Bug 3 with full state transitions
    - _Requirements: 2.3_

  - [ ] 15.4 Test Yeo-Johnson extreme values workflow
    - Phase 1: Upload data that triggers Yeo-Johnson selection
    - Phase 2: Force Yeo-Johnson with extreme lambda values (-7.545, -10, 10)
    - Verify round-trip accuracy maintained
    - Phase 3: Calculate sample size
    - Phase 4: Complete with transformed data
    - Validates: Bug 2 in realistic transformation scenario
    - _Requirements: 2.2_

  - [ ] 15.5 Test Help system integration
    - Launch application, verify 3 tabs visible
    - Access Help tab, verify all 4 content sections present
    - Navigate to Module A, perform calculation, return to Help
    - Navigate to Module V, perform workflow, return to Help
    - Verify Help content remains accessible and correct
    - Validates: Bugs 4, 7 with tab navigation
    - _Requirements: 2.4, 2.7_

  - [ ] 15.6 Test cross-module preservation
    - Perform Module A calculation (attribute data)
    - Switch to Module V, perform complete workflow
    - Switch back to Module A, verify state preserved
    - Generate reports from both modules
    - Verify no interference between modules
    - Validates: Preservation requirements 5, 8
    - _Requirements: 3.5, 3.8_

  - [ ] 15.7 Run all integration tests
    - Execute: `uv run pytest -q tests/test_manual_fixes_integration.py`
    - Verify all end-to-end workflows pass
    - Check for any unexpected interactions between fixes

## Phase 5: Documentation and Validation

- [ ] 16. Update documentation

  - [ ] 16.1 Update user documentation
    - Document new Help tab and its contents
    - Document new diagnostic plots in Phase 2 (Q-Q, P-P, I-MR)
    - Document Anderson-Darling test interpretation
    - Document Phase 4 acceptance of N+ samples
    - Document manual override method selection options
    - Update PDF report examples with table format

  - [ ] 16.2 Update developer documentation
    - Document Yeo-Johnson numerical stability improvements
    - Document UI state management changes for Phase 3
    - Document Help tab implementation
    - Document PDF table formatting implementation
    - Add code comments for complex business logic

  - [ ] 16.3 Update README if needed
    - Add any new dependencies (if matplotlib or other packages added)
    - Update feature list to reflect bug fixes
    - Update screenshots if UI changed significantly

- [ ] 17. Code review and quality checks

  - [ ] 17.1 Verify all fixes implemented correctly
    - Phase 4 validation uses `>=` not `==`
    - Yeo-Johnson handles extreme lambda values safely
    - Phase 3 completion disables all Phase 3 controls
    - Help tab exists and is populated with all 4 sections
    - Manual override dropdown has all 5 methods
    - Normality testing generates 3 diagnostic plots
    - Both Shapiro-Wilk and Anderson-Darling tests run
    - PDF results use Table class, not list formatting

  - [ ] 17.2 Run linting and formatting
    - Execute: `uv run ruff check src/`
    - Execute: `uv run ruff format src/`
    - Fix any warnings or errors

  - [ ] 17.3 Run type checking
    - Execute: `uvx ty check`
    - Fix any type errors

  - [ ] 17.4 Check test coverage
    - Execute: `uv run pytest --cov=src --cov-report=term-missing`
    - Verify >90% coverage for modified functions
    - Add tests for any uncovered code paths

- [ ] 18. Manual testing checklist

  - [ ] 18.1 Test Bug 1 fix manually
    - Test Phase 4 with N samples (should accept)
    - Test Phase 4 with N+1 samples (should accept)
    - Test Phase 4 with N+10 samples (should accept)
    - Test Phase 4 with N-1 samples (should reject)

  - [ ] 18.2 Test Bug 2 fix manually
    - Test Yeo-Johnson with lambda=-10 (should maintain round-trip)
    - Test Yeo-Johnson with lambda=-7.545 (should maintain round-trip)
    - Test Yeo-Johnson with lambda=0 (should maintain round-trip)
    - Test Yeo-Johnson with lambda=10 (should maintain round-trip)

  - [ ] 18.3 Test Bug 3 fix manually
    - Complete Phase 3 calculation
    - Verify all Phase 3 controls disabled
    - Attempt to modify Phase 3 inputs (should be prevented)

  - [ ] 18.4 Test Bug 4 fix manually
    - Launch application
    - Verify 3 tabs visible: Module A, Module V, Help
    - Click each tab to verify navigation works

  - [ ] 18.5 Test Bug 5 fix manually
    - Navigate to Phase 2
    - Enable manual override
    - Verify dropdown shows all 5 methods: None/Parametric, Logarithmic, Box-Cox, Yeo-Johnson, Non-Parametric/Wilks
    - Select each method and verify it works

  - [ ] 18.6 Test Bug 6 fix manually
    - Perform Phase 2 normality testing
    - Verify Q-Q plot displayed
    - Verify P-P plot displayed
    - Verify I-MR chart displayed
    - Verify plots are readable and correct

  - [ ] 18.7 Test Bug 7 fix manually
    - Access Help tab
    - Verify Module A guide section present and comprehensive
    - Verify Module V workflow section present and comprehensive
    - Verify Statistical terms glossary present and comprehensive
    - Verify Step-by-step guidance present and comprehensive

  - [ ] 18.8 Test Bug 8 fix manually
    - Perform Phase 2 normality assessment
    - Verify Shapiro-Wilk test results displayed
    - Verify Anderson-Darling test results displayed
    - Verify both test statistics and p-values/critical values shown

  - [ ] 18.9 Test Bug 9 fix manually
    - Generate PDF report with calculation results
    - Open PDF and verify results section
    - Verify results displayed in table format (not list)
    - Verify table has proper columns, rows, headers, alignment

- [ ] 19. Checkpoint - Ensure all tests pass
  - Run complete test suite: `uv run pytest -q`
  - Verify all unit tests pass
  - Verify all property-based tests pass
  - Verify all integration tests pass
  - Verify all manual testing completed successfully
  - Ask user if any questions or issues arise

