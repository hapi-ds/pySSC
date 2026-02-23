# Manual Testing Fixes Bugfix Design

## Overview

This design addresses 9 bugs discovered during manual testing of the Sample Size Calculator application. The bugs span validation logic (Phase 4 sample size validation), numerical stability (Yeo-Johnson transformation round-trip), UI workflow management (Phase 3 state control), user experience (Help tab and documentation), feature completeness (Phase 2 manual override, normality diagnostic plots, Anderson-Darling test), and report formatting (PDF table layout). The fixes ensure correct validation behavior, numerical accuracy, proper workflow state management, comprehensive user guidance, and professional report presentation.

## Glossary

- **Bug_Condition (C)**: The conditions that trigger each of the 9 bugs
- **Property (P)**: The desired correct behavior for each bug condition
- **Preservation**: Existing functionality that must remain unchanged
- **Phase 4 Validation**: Final validation step that checks sample size adequacy
- **Yeo-Johnson Transform**: Power transformation that handles zero and negative values
- **Round-trip Transformation**: Transform then inverse transform should return original values
- **UI State Management**: Control enabling/disabling based on workflow phase completion
- **Manual Override**: User ability to manually select transformation method in Phase 2
- **Normality Diagnostics**: Visual plots (Q-Q, P-P, I-MR) for assessing normality
- **Anderson-Darling Test**: Alternative normality test to complement Shapiro-Wilk
- **PDF Table Formatting**: Professional table layout with columns, rows, headers

## Bug Details

### Bug 1: Phase 4 Validation Too Strict


**Fault Condition:**
```
FUNCTION isBug1Condition(input)
  INPUT: input of type (final_dataset: list[float], required_sample_size: int)
  OUTPUT: boolean
  
  RETURN len(input.final_dataset) > input.required_sample_size
         AND validation_rejects_data(input)
END FUNCTION
```

**Example:**
- Required sample size N = 30
- User provides 35 data points
- Current: System rejects with "Final dataset must contain exactly N data points"
- Expected: System accepts and proceeds with tolerance calculations

### Bug 2: Yeo-Johnson Round-Trip Failure

**Fault Condition:**
```
FUNCTION isBug2Condition(input)
  INPUT: input of type (data: list[float], lambda: float)
  OUTPUT: boolean
  
  transformed := yeo_johnson_transform(input.data, input.lambda)
  inverse := inverse_yeo_johnson_transform(transformed, input.lambda)
  
  RETURN NOT values_within_tolerance(inverse, input.data, epsilon=1e-10)
END FUNCTION
```

**Example:**
- Data: [23.0, 24.0, 27.0]
- Lambda: -7.545504735605443
- Current: Round-trip fails, inverse transform does not return original values
- Expected: Round-trip succeeds within numerical precision (epsilon=1e-10)


### Bug 3: Phase 3 UI State Not Disabled

**Fault Condition:**
```
FUNCTION isBug3Condition(input)
  INPUT: input of type (phase3_completed: bool, phase3_controls_enabled: bool)
  OUTPUT: boolean
  
  RETURN input.phase3_completed == True
         AND input.phase3_controls_enabled == True
END FUNCTION
```

**Example:**
- User completes Phase 3 sample size calculation
- Current: Phase 3 controls remain enabled, user can recalculate
- Expected: Phase 3 controls disabled to prevent invalidating Phase 4 results

### Bug 4: Missing Help Tab

**Fault Condition:**
```
FUNCTION isBug4Condition(input)
  INPUT: input of type (tab_list: list[str])
  OUTPUT: boolean
  
  RETURN "Help" NOT IN input.tab_list
         AND len(input.tab_list) == 2
         AND "Module A" IN input.tab_list
         AND "Module V" IN input.tab_list
END FUNCTION
```

**Example:**
- Current: Only "Module A" and "Module V" tabs visible
- Expected: Third "Help" tab with documentation and guidance


### Bug 5: Phase 2 Manual Override Limited to Parametric

**Fault Condition:**
```
FUNCTION isBug5Condition(input)
  INPUT: input of type (manual_override_enabled: bool, available_methods: list[str])
  OUTPUT: boolean
  
  RETURN input.manual_override_enabled == True
         AND input.available_methods == ["Parametric"]
         AND expected_methods := ["None/Parametric", "Logarithmic", "Box-Cox", 
                                   "Yeo-Johnson", "Non-Parametric/Wilks"]
         AND input.available_methods != expected_methods
END FUNCTION
```

**Example:**
- User enables Manual Override in Phase 2
- Current: Only "Parametric" method selectable
- Expected: All methods selectable (None/Parametric, Logarithmic, Box-Cox, Yeo-Johnson, Non-Parametric/Wilks)

### Bug 6: Missing Normality Diagnostic Plots

**Fault Condition:**
```
FUNCTION isBug6Condition(input)
  INPUT: input of type (normality_test_performed: bool, plots_displayed: list[str])
  OUTPUT: boolean
  
  RETURN input.normality_test_performed == True
         AND "Q-Q Plot" NOT IN input.plots_displayed
         AND "P-P Plot" NOT IN input.plots_displayed
         AND "I-MR Chart" NOT IN input.plots_displayed
END FUNCTION
```

**Example:**
- Phase 2 normality testing performed
- Current: Only Shapiro-Wilk p-value displayed
- Expected: Q-Q plot, P-P plot, and I-MR chart displayed alongside p-value


### Bug 7: Missing Help Page Content

**Fault Condition:**
```
FUNCTION isBug7Condition(input)
  INPUT: input of type (help_tab_exists: bool, help_content: dict)
  OUTPUT: boolean
  
  RETURN input.help_tab_exists == True
         AND ("module_a_guide" NOT IN input.help_content
              OR "module_v_workflow" NOT IN input.help_content
              OR "statistical_terms" NOT IN input.help_content
              OR "step_by_step_guidance" NOT IN input.help_content)
END FUNCTION
```

**Example:**
- Help tab created but empty or incomplete
- Current: No comprehensive documentation displayed
- Expected: Module A guide, Module V 4-phase workflow, statistical terms, step-by-step guidance

### Bug 8: Missing Anderson-Darling Test

**Fault Condition:**
```
FUNCTION isBug8Condition(input)
  INPUT: input of type (normality_tests_performed: list[str])
  OUTPUT: boolean
  
  RETURN "Shapiro-Wilk" IN input.normality_tests_performed
         AND "Anderson-Darling" NOT IN input.normality_tests_performed
         AND len(input.normality_tests_performed) < 2
END FUNCTION
```

**Example:**
- Phase 2 normality assessment performed
- Current: Only Shapiro-Wilk test performed
- Expected: Both Shapiro-Wilk and Anderson-Darling tests performed and displayed


### Bug 9: PDF Report List Format Instead of Table

**Fault Condition:**
```
FUNCTION isBug9Condition(input)
  INPUT: input of type (pdf_report: bytes, results_section_format: str)
  OUTPUT: boolean
  
  RETURN input.results_section_format == "list"
         AND NOT is_table_format(input.results_section_format)
END FUNCTION
```

**Example:**
- PDF report generated with calculation results
- Current: Results displayed as list items
- Expected: Results displayed in professional table with columns, rows, headers, alignment

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Phase 4 must continue to reject datasets with sample size LESS than required N (3.1)
- Logarithmic and Box-Cox transformations must maintain round-trip accuracy (3.2)
- Phase 1 and Phase 2 completion must continue proper workflow state management (3.3)
- Phase 4 tolerance calculations must produce correct results with valid data (3.4)
- Module A and Module V tab navigation must continue working properly (3.5)
- Automatic method selection (non-manual override) must continue working (3.6)
- Phase 2 transformation parameters must continue displaying correctly (3.7)
- Module A and Module V interfaces must continue functioning properly (3.8)
- Shapiro-Wilk test results must continue displaying as part of normality assessment (3.9)
- PDF report non-table sections must maintain correct formatting (3.10)


**Scope:**
All inputs that do NOT involve the 9 specific bug conditions should be completely unaffected by these fixes. This includes:
- Normal Phase 4 validation with exact sample size N
- All other transformation methods and their round-trip behavior
- Phase 1, Phase 2, and Phase 4 state management
- Existing Module A and Module V functionality
- Automatic transformation method selection
- All non-results sections of PDF reports

## Hypothesized Root Cause

Based on the bug descriptions, the most likely issues are:

### Bug 1: Phase 4 Validation Logic
1. **Overly Strict Equality Check**: The validation logic uses `len(data) == N` instead of `len(data) >= N`
   - Located in Phase 4 validation function in `ui_controller.py` or `tolerance.py`
   - Should accept datasets with N or more samples

### Bug 2: Yeo-Johnson Numerical Stability
1. **Extreme Lambda Values**: Lambda values far from zero (e.g., -7.545) cause numerical overflow/underflow
   - Located in `transformations.py` in `inverse_yeo_johnson_transform` function
   - May need numerical stability improvements (clamping, log-space computation)

2. **Precision Loss**: Floating-point arithmetic accumulates errors in extreme cases
   - May need higher precision or alternative computation methods


### Bug 3: UI State Management
1. **Missing Disable Logic**: Phase 3 completion handler does not disable Phase 3 controls
   - Located in `ui_controller.py` in `complete_phase3` or `_enforce_sequential_workflow`
   - Should disable Phase 3 inputs/buttons after completion

### Bug 4: Missing Help Tab
1. **Tab Creation Not Implemented**: Help tab creation code not present in UI initialization
   - Located in `ui_controller.py` in `create_app` method
   - Need to add `create_help_tab` method similar to `create_module_a_tab` and `create_module_v_tab`

### Bug 5: Manual Override Method Restriction
1. **Hardcoded Method List**: Manual override dropdown populated with only "Parametric"
   - Located in `ui_controller.py` in `_create_phase2_ui` method
   - Should populate with all available methods when manual override enabled

### Bug 6: Missing Diagnostic Plots
1. **Plot Generation Not Implemented**: Q-Q, P-P, and I-MR plot generation code not present
   - Located in `ui_controller.py` in Phase 2 normality testing section
   - Need to add plot generation using matplotlib/scipy and display in Gradio


### Bug 7: Missing Help Content
1. **Empty Help Tab**: Help tab exists but content not populated
   - Located in `ui_controller.py` in `create_help_tab` method (to be created)
   - Need comprehensive markdown/HTML content for all documentation sections

### Bug 8: Missing Anderson-Darling Test
1. **Single Test Implementation**: Only Shapiro-Wilk test implemented
   - Located in `normality.py` - only `shapiro_wilk_test` function exists
   - Need to add `anderson_darling_test` function using `scipy.stats.anderson`
   - Need to update UI to display both test results

### Bug 9: PDF List Format
1. **List-Based Results Rendering**: Results section uses list items instead of table
   - Located in `report_generator.py` in `generate_user_report` method
   - Need to use ReportLab Table class for structured table layout

## Correctness Properties

Property 1: Fault Condition - Phase 4 Accepts N or More Samples

_For any_ Phase 4 validation input where the final dataset size is greater than or equal to the required sample size N, the fixed validation function SHALL accept the data and proceed with tolerance limit calculations.

**Validates: Requirements 2.1**


Property 2: Fault Condition - Yeo-Johnson Round-Trip Accuracy

_For any_ Yeo-Johnson transformation input with valid lambda parameter and dataset, the fixed transformation functions SHALL ensure round-trip transformation (transform then inverse) returns values within numerical precision (epsilon=1e-10) of original values.

**Validates: Requirements 2.2**

Property 3: Fault Condition - Phase 3 Controls Disabled After Completion

_For any_ Phase 3 completion event, the fixed UI state management SHALL disable Phase 3 controls to prevent recalculation that would invalidate Phase 4 results.

**Validates: Requirements 2.3**

Property 4: Fault Condition - Help Tab Exists

_For any_ application initialization, the fixed UI creation SHALL display a third "Help" tab alongside "Module A" and "Module V" tabs.

**Validates: Requirements 2.4**

Property 5: Fault Condition - Manual Override Allows All Methods

_For any_ Phase 2 manual override activation, the fixed UI SHALL allow selection from all available transformation/analysis methods (None/Parametric, Logarithmic, Box-Cox, Yeo-Johnson, Non-Parametric/Wilks).

**Validates: Requirements 2.5**


Property 6: Fault Condition - Normality Diagnostic Plots Displayed

_For any_ Phase 2 normality testing event, the fixed UI SHALL display Q-Q plot, P-P plot, and I-MR chart alongside the Shapiro-Wilk p-value to help users assess normality visually.

**Validates: Requirements 2.6**

Property 7: Fault Condition - Help Page Contains Comprehensive Documentation

_For any_ Help tab access, the fixed UI SHALL display comprehensive documentation including Module A usage guide, Module V 4-phase workflow explanation, statistical terms glossary, and step-by-step guidance for common workflows.

**Validates: Requirements 2.7**

Property 8: Fault Condition - Two Normality Tests Performed

_For any_ Phase 2 normality assessment, the fixed system SHALL perform both Shapiro-Wilk and Anderson-Darling tests and display all test results with their respective statistics and p-values/critical values.

**Validates: Requirements 2.8**

Property 9: Fault Condition - PDF Report Uses Table Format

_For any_ PDF report generation with calculation results, the fixed report generator SHALL display results in a professional table format with proper columns, rows, headers, and alignment.

**Validates: Requirements 2.9**


Property 10: Preservation - Phase 4 Rejects Insufficient Samples

_For any_ Phase 4 validation input where the final dataset size is LESS than the required sample size N, the fixed validation function SHALL produce the same rejection behavior as the original function, preserving the requirement for minimum sample size.

**Validates: Requirements 3.1**

Property 11: Preservation - Other Transformations Maintain Accuracy

_For any_ logarithmic or Box-Cox transformation, the fixed transformation functions SHALL produce the same round-trip accuracy as the original functions, preserving numerical stability for non-Yeo-Johnson methods.

**Validates: Requirements 3.2**

Property 12: Preservation - Phase 1 and Phase 2 State Management

_For any_ Phase 1 or Phase 2 completion event, the fixed UI state management SHALL produce the same workflow state transitions as the original implementation, preserving proper phase enabling/disabling logic.

**Validates: Requirements 3.3**

Property 13: Preservation - Phase 4 Calculation Correctness

_For any_ Phase 4 tolerance calculation with valid data, the fixed system SHALL produce the same correct tolerance limits, pass/fail results, and Ppk values as the original implementation.

**Validates: Requirements 3.4**


Property 14: Preservation - Tab Navigation Functionality

_For any_ tab navigation between Module A and Module V, the fixed UI SHALL produce the same tab switching behavior as the original implementation, preserving proper state management.

**Validates: Requirements 3.5**

Property 15: Preservation - Automatic Method Selection

_For any_ Phase 2 analysis without manual override enabled, the fixed system SHALL produce the same automatic transformation method selection as the original implementation.

**Validates: Requirements 3.6**

Property 16: Preservation - Transformation Parameter Display

_For any_ Phase 2 normality testing with transformations applied, the fixed UI SHALL continue displaying Shapiro-Wilk p-value and transformation parameters as in the original implementation.

**Validates: Requirements 3.7**

Property 17: Preservation - Module Interfaces Functionality

_For any_ Module A or Module V tab access, the fixed UI SHALL display the same functional interfaces as the original implementation.

**Validates: Requirements 3.8**

Property 18: Preservation - Shapiro-Wilk Test Display

_For any_ Phase 2 normality assessment, the fixed system SHALL continue displaying Shapiro-Wilk test statistic and p-value as part of the results.

**Validates: Requirements 3.9**


Property 19: Preservation - PDF Non-Table Sections Formatting

_For any_ PDF report generation with non-results content (headers, metadata, charts, analysis text), the fixed report generator SHALL format those sections identically to the original implementation, preserving overall PDF structure and layout.

**Validates: Requirements 3.10**

## Fix Implementation

### Bug 1: Phase 4 Validation Logic

**File**: `src/sample_size_calculator/ui_controller.py`

**Function**: `_create_phase4_ui` (validation logic within Phase 4 handler)

**Specific Changes**:
1. **Locate Validation Check**: Find the validation logic that checks `len(final_data) == required_n`
2. **Change to Greater-Than-Or-Equal**: Replace with `len(final_data) >= required_n`
3. **Update Error Message**: Change error message to reflect "at least N" instead of "exactly N"
4. **Add Informational Message**: If len > N, inform user that first N samples will be used or all samples accepted

**Code Location**: Search for Phase 4 validation in the button click handler for final validation


### Bug 2: Yeo-Johnson Numerical Stability

**File**: `src/sample_size_calculator/transformations.py`

**Functions**: `yeo_johnson_transform` and `inverse_yeo_johnson_transform`

**Specific Changes**:
1. **Add Numerical Stability Checks**: Implement safeguards for extreme lambda values
   - Clamp intermediate results to prevent overflow/underflow
   - Use `np.clip` or conditional logic to handle extreme values
   
2. **Improve Inverse Transform**: Enhance `inverse_yeo_johnson_transform` function
   - Add epsilon tolerance for division operations
   - Handle edge cases where lambda is very negative or very positive
   - Consider using log-space arithmetic for extreme values

3. **Add Round-Trip Validation**: Optionally add internal validation
   - Check round-trip accuracy after transformation
   - Log warnings if accuracy degrades beyond threshold

**Root Cause**: Extreme lambda values (e.g., -7.545) cause numerical instability in power operations


### Bug 3: Phase 3 UI State Management

**File**: `src/sample_size_calculator/ui_controller.py`

**Functions**: `complete_phase3` in `ModuleVState` class and `_enforce_sequential_workflow`

**Specific Changes**:
1. **Add Control Disabling in complete_phase3**: After storing Phase 3 results, disable Phase 3 controls
   - Store references to Phase 3 input components (textboxes, buttons, dropdowns)
   - Set `interactive=False` on all Phase 3 controls
   
2. **Update _enforce_sequential_workflow**: Ensure Phase 3 controls are disabled when phase is completed
   - Add logic to check if Phase 3 is completed
   - Disable controls if completed

3. **Store Component References**: In `_create_phase3_ui`, store references to all interactive components
   - Add instance variables for Phase 3 controls
   - Use these references in disable logic

**Code Pattern**: Similar to how Phase 1 and Phase 2 likely handle state transitions


### Bug 4: Missing Help Tab

**File**: `src/sample_size_calculator/ui_controller.py`

**Function**: `create_app` and new `create_help_tab` method

**Specific Changes**:
1. **Create create_help_tab Method**: Add new method to UIController class
   - Follow pattern of `create_module_a_tab` and `create_module_v_tab`
   - Use Gradio Markdown or HTML components for content display
   
2. **Add Tab in create_app**: Modify the Tabs component creation
   - Add third tab after Module A and Module V
   - Call `create_help_tab()` to populate content

3. **Structure Help Content**: Organize into sections
   - Module A usage guide
   - Module V 4-phase workflow
   - Statistical terms glossary
   - Step-by-step guidance

**Implementation**: Use Gradio `gr.Markdown()` or `gr.HTML()` for rich content display


### Bug 5: Phase 2 Manual Override Method Selection

**File**: `src/sample_size_calculator/ui_controller.py`

**Function**: `_create_phase2_ui` (manual override dropdown population)

**Specific Changes**:
1. **Locate Manual Override Dropdown**: Find the dropdown component for method selection
   - Currently populated with only ["Parametric"]
   
2. **Update Choices List**: Change to full method list
   - Replace with: ["None/Parametric", "Logarithmic", "Box-Cox", "Yeo-Johnson", "Non-Parametric/Wilks"]
   
3. **Update Handler Logic**: Ensure the handler can process all method types
   - Verify transformation_cascade function supports all methods
   - Update any conditional logic that assumes only "Parametric"

4. **Test Method Mapping**: Ensure UI method names map correctly to backend method identifiers

**Root Cause**: Dropdown choices hardcoded to single option instead of full list


### Bug 6: Missing Normality Diagnostic Plots

**File**: `src/sample_size_calculator/ui_controller.py`

**Function**: `_create_phase2_ui` (normality testing display section)

**New Dependency**: May need `matplotlib` for plot generation (likely already available)

**Specific Changes**:
1. **Add Plot Generation Functions**: Create helper methods for each plot type
   - `_generate_qq_plot(data)`: Q-Q plot using `scipy.stats.probplot`
   - `_generate_pp_plot(data)`: P-P plot using cumulative distributions
   - `_generate_imr_chart(data)`: I-MR chart for process stability

2. **Add Plot Display Components**: In Phase 2 UI
   - Add three `gr.Plot()` or `gr.Image()` components
   - Position below or alongside Shapiro-Wilk p-value display

3. **Update Normality Test Handler**: When normality test runs
   - Generate all three plots
   - Return plot objects to display in UI
   - Maintain existing p-value display

4. **Plot Specifications**:
   - Q-Q Plot: Quantile-Quantile comparing data vs theoretical normal
   - P-P Plot: Probability-Probability for cumulative distribution
   - I-MR Chart: Individual values and Moving Range for stability


### Bug 7: Missing Help Page Content

**File**: `src/sample_size_calculator/ui_controller.py`

**Function**: `create_help_tab` (to be created in Bug 4 fix)

**Specific Changes**:
1. **Create Comprehensive Documentation Content**: Write detailed help text covering:
   
   **Module A Section**:
   - Purpose: Attribute data analysis for pass/fail characteristics
   - Input requirements
   - Calculation methodology
   - Interpretation of results
   
   **Module V Section**:
   - Purpose: Variable data analysis with 4-phase workflow
   - Phase 1: Initial data collection and outlier detection
   - Phase 2: Normality testing and transformation selection
   - Phase 3: Sample size calculation based on statistical requirements
   - Phase 4: Final validation and tolerance limit calculation
   
   **Statistical Terms Glossary**:
   - Shapiro-Wilk test, Anderson-Darling test
   - Box-Cox, Yeo-Johnson, Logarithmic transformations
   - Q-Q plot, P-P plot, I-MR chart
   - Tolerance limits, Ppk, confidence levels
   
   **Step-by-Step Workflows**:
   - Common use cases with example data
   - Decision trees for method selection
   - Troubleshooting guidance

2. **Format Content**: Use Markdown for readability
   - Headers, bullet points, code blocks for data examples
   - Consider collapsible sections using Gradio Accordion


### Bug 8: Missing Anderson-Darling Test

**File**: `src/sample_size_calculator/normality.py`

**New Function**: `anderson_darling_test`

**Specific Changes**:
1. **Add Anderson-Darling Test Function**: Create new function in normality.py
   ```python
   def anderson_darling_test(data: list[float]) -> tuple[float, list[float], list[float]]:
       """Perform Anderson-Darling test for normality.
       
       Returns:
           tuple: (statistic, critical_values, significance_levels)
       """
       result = stats.anderson(data, dist='norm')
       return result.statistic, result.critical_values, result.significance_levels
   ```

2. **Update UI Display**: In `ui_controller.py` Phase 2 normality testing
   - Call both `shapiro_wilk_test` and `anderson_darling_test`
   - Display both results in UI
   - Format: "Shapiro-Wilk: statistic=X, p-value=Y"
   - Format: "Anderson-Darling: statistic=X, critical values at [15%, 10%, 5%, 2.5%, 1%]"

3. **Update transformation_cascade**: If normality decisions use test results
   - Consider both tests in normality assessment
   - Document decision logic (e.g., both must pass, or either can pass)

**Dependency**: `scipy.stats.anderson` (already available in scipy)


### Bug 9: PDF Report Table Formatting

**File**: `src/sample_size_calculator/report_generator.py`

**Function**: `generate_user_report` (ReportGenerator class)

**Specific Changes**:
1. **Locate Results Section**: Find where calculation results are rendered as list items
   - Search for list-based rendering code (likely using Paragraph with bullet points)

2. **Replace with Table**: Use ReportLab Table class
   ```python
   from reportlab.platypus import Table, TableStyle
   from reportlab.lib import colors
   
   # Create table data structure
   table_data = [
       ['Parameter', 'Value', 'Unit'],  # Header row
       ['Sample Size', str(n), 'samples'],
       ['Mean', f'{mean:.4f}', 'units'],
       # ... more rows
   ]
   
   # Create table with styling
   table = Table(table_data, colWidths=[200, 150, 100])
   table.setStyle(TableStyle([
       ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
       ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
       ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
       ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
       ('FONTSIZE', (0, 0), (-1, 0), 12),
       ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
       ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
       ('GRID', (0, 0), (-1, -1), 1, colors.black)
   ]))
   ```

3. **Maintain Other Sections**: Ensure headers, metadata, charts, and analysis text remain unchanged


## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate each bug on unfixed code, then verify all fixes work correctly and preserve existing behavior. Given the multi-bug nature of this fix, testing is organized by bug category.

### Exploratory Fault Condition Checking

**Goal**: Surface counterexamples that demonstrate each bug BEFORE implementing fixes. Confirm or refute the root cause analysis for each bug.

**Test Plan**: Write tests that exercise each bug condition on UNFIXED code to observe failures and understand root causes.

**Test Cases**:

1. **Bug 1 - Phase 4 Validation**: Test with sample size > N (will fail on unfixed code)
   - Input: required_n=30, provide 35 data points
   - Expected failure: Validation rejects data
   - Confirms: Overly strict equality check

2. **Bug 2 - Yeo-Johnson Round-Trip**: Test with extreme lambda values (will fail on unfixed code)
   - Input: data=[23.0, 24.0, 27.0], lambda=-7.545504735605443
   - Expected failure: Round-trip does not return original values
   - Confirms: Numerical instability with extreme lambda

3. **Bug 3 - Phase 3 State**: Test Phase 3 completion (will fail on unfixed code)
   - Input: Complete Phase 3 calculation
   - Expected failure: Controls remain enabled
   - Confirms: Missing disable logic


4. **Bug 4 - Help Tab**: Test tab list (will fail on unfixed code)
   - Input: Launch application
   - Expected failure: Only 2 tabs visible
   - Confirms: Help tab not created

5. **Bug 5 - Manual Override**: Test method selection with override enabled (will fail on unfixed code)
   - Input: Enable manual override in Phase 2
   - Expected failure: Only "Parametric" available
   - Confirms: Hardcoded method list

6. **Bug 6 - Diagnostic Plots**: Test normality testing display (will fail on unfixed code)
   - Input: Perform Phase 2 normality test
   - Expected failure: No Q-Q, P-P, or I-MR plots displayed
   - Confirms: Plot generation not implemented

7. **Bug 7 - Help Content**: Test Help tab content (will fail on unfixed code)
   - Input: Access Help tab (after Bug 4 fix)
   - Expected failure: Empty or incomplete content
   - Confirms: Documentation not written

8. **Bug 8 - Anderson-Darling**: Test normality test results (will fail on unfixed code)
   - Input: Perform Phase 2 normality assessment
   - Expected failure: Only Shapiro-Wilk displayed
   - Confirms: Anderson-Darling not implemented

9. **Bug 9 - PDF Table**: Test PDF report generation (will fail on unfixed code)
   - Input: Generate PDF report with results
   - Expected failure: Results in list format
   - Confirms: Table formatting not implemented


**Expected Counterexamples**:
- Phase 4 rejects valid data with N+ samples
- Yeo-Johnson fails round-trip with extreme lambda
- Phase 3 controls remain interactive after completion
- Application shows only 2 tabs
- Manual override dropdown shows only 1 method
- Normality testing shows no diagnostic plots
- Help tab has no comprehensive content
- Only one normality test performed
- PDF results formatted as list

### Fix Checking

**Goal**: Verify that for all inputs where each bug condition holds, the fixed functions produce the expected behavior.

**Pseudocode for Each Bug**:

```
# Bug 1: Phase 4 Validation
FOR ALL input WHERE len(final_data) >= required_n DO
  result := validate_phase4_fixed(input)
  ASSERT result.accepted == True
END FOR

# Bug 2: Yeo-Johnson Round-Trip
FOR ALL input WHERE is_valid_yeo_johnson_input(input) DO
  transformed := yeo_johnson_transform_fixed(input.data, input.lambda)
  inverse := inverse_yeo_johnson_transform_fixed(transformed, input.lambda)
  ASSERT all_close(inverse, input.data, epsilon=1e-10)
END FOR

# Bug 3: Phase 3 State
FOR ALL input WHERE phase3_completed == True DO
  state := get_phase3_controls_state_fixed()
  ASSERT state.all_disabled == True
END FOR
```


```
# Bug 4: Help Tab
FOR ALL input WHERE application_initialized == True DO
  tabs := get_tab_list_fixed()
  ASSERT "Help" IN tabs AND len(tabs) == 3
END FOR

# Bug 5: Manual Override
FOR ALL input WHERE manual_override_enabled == True DO
  methods := get_available_methods_fixed()
  ASSERT methods == ["None/Parametric", "Logarithmic", "Box-Cox", 
                     "Yeo-Johnson", "Non-Parametric/Wilks"]
END FOR

# Bug 6: Diagnostic Plots
FOR ALL input WHERE normality_test_performed == True DO
  plots := get_displayed_plots_fixed()
  ASSERT "Q-Q Plot" IN plots AND "P-P Plot" IN plots AND "I-MR Chart" IN plots
END FOR

# Bug 7: Help Content
FOR ALL input WHERE help_tab_accessed == True DO
  content := get_help_content_fixed()
  ASSERT has_module_a_guide(content) AND has_module_v_workflow(content)
         AND has_statistical_terms(content) AND has_step_by_step(content)
END FOR

# Bug 8: Anderson-Darling
FOR ALL input WHERE normality_assessment_performed == True DO
  tests := get_normality_tests_fixed()
  ASSERT "Shapiro-Wilk" IN tests AND "Anderson-Darling" IN tests
END FOR

# Bug 9: PDF Table
FOR ALL input WHERE pdf_generated == True DO
  format := get_results_format_fixed(input.pdf)
  ASSERT format == "table" AND has_proper_structure(format)
END FOR
```


### Preservation Checking

**Goal**: Verify that for all inputs where bug conditions do NOT hold, the fixed functions produce the same results as the original functions.

**Pseudocode**:

```
# Preservation 1: Phase 4 rejects insufficient samples
FOR ALL input WHERE len(final_data) < required_n DO
  ASSERT validate_phase4_original(input) == validate_phase4_fixed(input)
END FOR

# Preservation 2: Other transformations maintain accuracy
FOR ALL input WHERE transformation IN ["logarithmic", "box-cox"] DO
  ASSERT transform_original(input) == transform_fixed(input)
END FOR

# Preservation 3: Phase 1 and Phase 2 state management
FOR ALL input WHERE phase IN [1, 2] AND phase_completed == True DO
  ASSERT get_workflow_state_original(input) == get_workflow_state_fixed(input)
END FOR

# Preservation 4: Phase 4 calculations
FOR ALL input WHERE is_valid_phase4_data(input) DO
  ASSERT calculate_tolerance_original(input) == calculate_tolerance_fixed(input)
END FOR

# Preservation 5: Tab navigation
FOR ALL input WHERE tab_switch_event(input) DO
  ASSERT handle_tab_switch_original(input) == handle_tab_switch_fixed(input)
END FOR
```


```
# Preservation 6: Automatic method selection
FOR ALL input WHERE manual_override_enabled == False DO
  ASSERT select_method_original(input) == select_method_fixed(input)
END FOR

# Preservation 7: Transformation parameter display
FOR ALL input WHERE transformation_applied == True DO
  ASSERT display_params_original(input) == display_params_fixed(input)
END FOR

# Preservation 8: Module interfaces
FOR ALL input WHERE module IN ["A", "V"] AND tab_accessed == True DO
  ASSERT render_interface_original(input) == render_interface_fixed(input)
END FOR

# Preservation 9: Shapiro-Wilk display
FOR ALL input WHERE normality_test_performed == True DO
  result_original := get_shapiro_wilk_original(input)
  result_fixed := get_shapiro_wilk_fixed(input)
  ASSERT result_original IN result_fixed  # Fixed includes original
END FOR

# Preservation 10: PDF non-table sections
FOR ALL input WHERE pdf_generated == True DO
  sections := ["header", "metadata", "charts", "analysis"]
  FOR EACH section IN sections DO
    ASSERT render_section_original(section) == render_section_fixed(section)
  END FOR
END FOR
```


**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs
- With 9 bugs and 10 preservation requirements, automated testing is essential

**Test Plan**: For each preservation requirement, observe behavior on UNFIXED code first, then write property-based tests capturing that behavior.

### Unit Tests

**Bug-Specific Unit Tests**:
1. **Bug 1**: Test Phase 4 validation with N, N+1, N+10, N-1 samples
2. **Bug 2**: Test Yeo-Johnson round-trip with lambda values: -10, -7.545, -1, 0, 1, 7.545, 10
3. **Bug 3**: Test Phase 3 state after completion, verify all controls disabled
4. **Bug 4**: Test tab list contains exactly ["Module A", "Module V", "Help"]
5. **Bug 5**: Test manual override dropdown contains all 5 methods
6. **Bug 6**: Test normality testing returns 3 plot objects (Q-Q, P-P, I-MR)
7. **Bug 7**: Test Help content has all 4 required sections with non-empty text
8. **Bug 8**: Test normality assessment returns both Shapiro-Wilk and Anderson-Darling results
9. **Bug 9**: Test PDF report results section uses Table class, not list items

**Preservation Unit Tests**:
1. Test Phase 4 rejection with N-1 samples (should still reject)
2. Test logarithmic and Box-Cox round-trip accuracy (should maintain)
3. Test Phase 1/2 state transitions (should maintain)
4. Test Phase 4 tolerance calculations with valid data (should maintain correctness)
5. Test Module A and Module V functionality (should maintain)


### Property-Based Tests

**Fix Verification Properties**:
1. **Phase 4 Validation**: Generate random datasets with size >= N, verify all accepted
2. **Yeo-Johnson Round-Trip**: Generate random data and lambda values, verify round-trip accuracy
3. **UI State Management**: Generate random phase completion sequences, verify proper disabling
4. **Method Selection**: Generate random manual override scenarios, verify all methods available
5. **Normality Plots**: Generate random datasets, verify all 3 plots generated
6. **Normality Tests**: Generate random datasets, verify both tests performed

**Preservation Properties**:
1. **Phase 4 Rejection**: Generate random datasets with size < N, verify rejection maintained
2. **Other Transformations**: Generate random data for log/Box-Cox, verify accuracy maintained
3. **Workflow State**: Generate random Phase 1/2 completions, verify state transitions maintained
4. **Tolerance Calculations**: Generate random valid Phase 4 data, verify results unchanged
5. **Automatic Selection**: Generate random data without override, verify method selection unchanged

**Test Execution**: Use pytest with hypothesis library for property-based testing
- Run with `uv run pytest -q tests/test_manual_fixes.py`
- Use `@given` decorators with appropriate strategies
- Set reasonable example counts (e.g., 100 examples per property)


### Integration Tests

**End-to-End Workflow Tests**:

1. **Complete Module V Workflow with N+ Samples**:
   - Phase 1: Upload initial data with outliers
   - Phase 2: Perform normality testing, observe diagnostic plots and both tests
   - Phase 3: Calculate sample size N
   - Phase 4: Upload N+5 samples, verify acceptance and correct tolerance calculations
   - Generate PDF report, verify table formatting
   - Validates: Bugs 1, 6, 8, 9 in realistic workflow

2. **Manual Override Full Workflow**:
   - Phase 1: Upload data
   - Phase 2: Enable manual override, verify all 5 methods available
   - Select each method sequentially, verify transformations work
   - Phase 3: Calculate sample size
   - Phase 4: Complete validation
   - Validates: Bug 5 with complete workflow

3. **UI State Management Workflow**:
   - Phase 1: Complete, verify Phase 2 enabled
   - Phase 2: Complete, verify Phase 3 enabled
   - Phase 3: Complete, verify controls disabled and Phase 4 enabled
   - Attempt to modify Phase 3, verify prevented
   - Phase 4: Complete workflow
   - Validates: Bug 3 with full state transitions


4. **Yeo-Johnson Extreme Values Workflow**:
   - Phase 1: Upload data that triggers Yeo-Johnson selection
   - Phase 2: Force Yeo-Johnson with extreme lambda values
   - Verify round-trip accuracy maintained
   - Phase 3: Calculate sample size
   - Phase 4: Complete with transformed data
   - Validates: Bug 2 in realistic transformation scenario

5. **Help System Integration**:
   - Launch application, verify 3 tabs visible
   - Access Help tab, verify all 4 content sections present
   - Navigate to Module A, perform calculation, return to Help
   - Navigate to Module V, perform workflow, return to Help
   - Verify Help content remains accessible and correct
   - Validates: Bugs 4, 7 with tab navigation

6. **Cross-Module Preservation Test**:
   - Perform Module A calculation (attribute data)
   - Switch to Module V, perform complete workflow
   - Switch back to Module A, verify state preserved
   - Generate reports from both modules
   - Verify no interference between modules
   - Validates: Preservation requirements 5, 8

**Test Execution Strategy**:
- Run unit tests first: `uv run pytest -q tests/test_manual_fixes_unit.py`
- Run property-based tests: `uv run pytest -q tests/test_manual_fixes_properties.py`
- Run integration tests: `uv run pytest -q tests/test_manual_fixes_integration.py`
- Use `--tb=short` for concise error reporting
- Use `-k "test_name"` to run specific test categories


### Regression Prevention Measures

**Code Review Checklist**:
1. Verify Phase 4 validation uses `>=` not `==`
2. Verify Yeo-Johnson handles extreme lambda values safely
3. Verify Phase 3 completion disables all Phase 3 controls
4. Verify Help tab exists and is populated
5. Verify manual override dropdown has all 5 methods
6. Verify normality testing generates 3 diagnostic plots
7. Verify Help content has all 4 required sections
8. Verify both Shapiro-Wilk and Anderson-Darling tests run
9. Verify PDF results use Table class, not list formatting

**Automated Test Coverage**:
- Maintain >90% code coverage for modified functions
- Add tests to CI/CD pipeline to catch regressions
- Use property-based tests to cover edge cases automatically
- Monitor test execution time, optimize if needed

**Documentation Updates**:
- Update user documentation to reflect new Help tab
- Document new diagnostic plots in Phase 2
- Document Anderson-Darling test interpretation
- Update PDF report examples with table format

**Manual Testing Checklist** (before release):
- [ ] Test Phase 4 with N, N+1, N+10 samples
- [ ] Test Yeo-Johnson with lambda values: -10, -5, 0, 5, 10
- [ ] Test Phase 3 completion disables controls
- [ ] Verify Help tab accessible and complete
- [ ] Test manual override with all 5 methods
- [ ] Verify Q-Q, P-P, I-MR plots display correctly
- [ ] Verify Help content comprehensive and accurate
- [ ] Verify both normality tests display results
- [ ] Generate PDF and verify table formatting
- [ ] Test complete Module V workflow end-to-end

