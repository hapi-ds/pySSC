# User Requirement Specification (URS)

**Project:** Sample Size Estimator (Python) **Version:** 1.0 **Classification:** QMS Software (ISO/TR 80002-2)

## 1\. Introduction

The system is a Python-based web application designed to determine statistically valid sample sizes for medical device design verification and process validation. It utilizes the NiceGUI framework to provide a user-friendly interface for advanced stochastic models. The application is critical for Quality Management Systems (QMS) to ensure compliance with risk-based statistical rationale requirements.

## 2\. Functional Requirements (Statistical Engine)

### 2.1 Module A: Attribute Data Analysis (Tab 1\)

**Context:** Used for binary data (Pass/Fail, Go/No-Go) derived from the Binomial Distribution.

| ID | Requirement Description | Acceptance Criteria / Formula Logic |
| :---- | :---- | :---- |
| **URS-FUNC\_A-01** | The system shall accept user inputs for **Confidence ($C$)**, **Reliability ($R$)**, and optionally **Allowable Failures ($c$)**. | Inputs validated: $0 \< C \< 100$ %, $0 \< R \< 100$ %, $c \\ge 0$ (integer). |
| **URS-FUNC\_A-02** | If allowable failures are zero ($c=0$), the system shall calculate the minimum sample size ($n$) using the **Success Run Theorem**. | Formula: $n \= \\lceil \\frac{\\ln(1-C)}{\\ln(R)} \\rceil$. |
| **URS-FUNC\_A-03** | If allowable failures are specified ($c \> 0$), the system shall calculate $n$ using the cumulative Binomial distribution. | Iteratively solve for smallest $n$ where: $\\sum\_{k=0}^{c} \\binom{n}{k} (1-R)^k R^{n-k} \\le 1-C$. |
| **URS-FUNC\_A-04** | **Sensitivity Analysis:** If the user leaves the Allowable Failures ($c$) input empty, the system shall automatically calculate and display sample sizes for $c=0, 1, 2, 3$. | Output must be a table with two columns: $c$ (0 to 3\) and required $n$. |

### 2.2 Module V: Variable Data Analysis Workflow (Tab 2\)

**Context:** Used for continuous measurements. This module follows a strict, 4-phase sequential pipeline to prevent statistical errors.

#### Phase 1: Setup & Data Pre-Processing

| ID | Requirement Description | Acceptance Criteria / Mathematical Logic |
| :---- | :---- | :---- |
| **URS-V-01** | **Specification Constraints:** The system shall require the user to explicitly define the specification as **One-Sided** (LSL or USL) or **Two-Sided** (LSL and USL). | Calculations cannot proceed without this definition. |
| **URS-V-02** | **Pilot Data Input:** The system shall accept an initial pilot dataset (continuous numeric values). | Required for estimating variance and required sample sizes. |
| **URS-V-03** | **Outlier Evaluation:** The system shall detect outliers in the active dataset using the Interquartile Range (IQR) method. | Flags values $\< Q1 \- 1.5 \\times IQR$ or $\> Q3 \+ 1.5 \\times IQR$. |
| **URS-V-04** | **Outlier Handling:** The system shall allow users to manually exclude detected outliers. | Exclusions MUST trigger a mandatory "Engineering Rationale" text field and be permanently flagged in the final report. |

#### Phase 2: Normality & Transformation Engine

| ID | Requirement Description | Acceptance Criteria / Mathematical Logic |
| :---- | :---- | :---- |
| **URS-V-05** | **Primary Normality Test:** The system shall evaluate the active, cleaned pilot dataset using the **Shapiro-Wilk Test**. | If $p \> 0.05$, the data is assumed Normal. Lock method as "Parametric". |
| **URS-V-06** | **Transformation Cascade:** If $p \\le 0.05$, the system shall automatically attempt mathematically normalizing the data in the following strict hierarchy: | 1\. **Logarithmic ($ln(X)$)** (if all $X\>0$). 2\. **Box-Cox** (optimizing $\\lambda$, if all $X\>0$). 3\. **Yeo-Johnson** (optimizing $\\lambda$, handles $X \\le 0$). |
| **URS-V-07** | **Transformation Verification:** Each transformation attempt must be re-tested with Shapiro-Wilk. | The first transformation to yield $p \> 0.05$ is locked as the "Active Transformation Method" alongside its specific $\\lambda$. |
| **URS-V-08** | **Non-Parametric Fallback:** If all transformations fail to achieve $p \> 0.05$, the system shall lock the method as "Non-Parametric (Wilks)". | Data cannot be normalized. Continuous distribution models are abandoned. |

#### Phase 3: Predictive Sample Size Estimation

| ID | Requirement Description | Acceptance Criteria / Mathematical Logic |
| :---- | :---- | :---- |
| **URS-V-09** | **Capability Margin ($k\_{margin}$):** For parametric/transformed data, the system shall forward-transform the Specification Limits and calculate the physical capability margin of the pilot data. | $k\_{margin} \= \\min(\\text{distance to LSL}\_t / S\_t, \\text{distance to USL}\_t / S\_t)$. If $\\le 0$, display FATAL ERROR: Process Incapable. |
| **URS-V-10** | **Parametric N Iteration:** The system shall iterate the target sample size ($N$) until the statistical tolerance factor ($k$) is smaller than the capability margin ($k\_{margin}$). | **1-Sided Spec:** Iterate until $k\_1(N) \\le k\_{margin}$. **2-Sided Spec:** Iterate until $k\_2(N) \\le k\_{margin}$. |
| **URS-V-11** | **Non-Parametric N Calculation:** If the method is Non-Parametric, the system shall output the fixed sample size required to use extreme order statistics. | **1-Sided Spec:** $N \= \\lceil \\frac{\\ln(1-C)}{\\ln(R)} \\rceil$. **2-Sided Spec:** Iterate $N$ until $1 \- N R^{N-1} \+ (N-1)R^N \\ge C$. |

#### Phase 4: Final Validation & Tolerance Intervals

| ID | Requirement Description | Acceptance Criteria / Mathematical Logic |
| :---- | :---- | :---- |
| **URS-V-12** | **Final Data Execution:** The system shall accept the Final Validation dataset (size $N$) and strictly apply the exact Transformation Method and $\\lambda$ locked during Phase 2\. | Data is mathematically translated into the locked normalized space. |
| **URS-V-13** | **Parametric Tolerance Limits:** If Parametric, the system shall compute tolerance limits in the normalized space using the appropriate $k$-factor. | **1-Sided limits:** Uses exact non-central t-distribution ($k\_1$). **2-Sided limits:** Uses Howe-Guenther approx ($k\_2$). $Limits\_t \= \\bar{X}\_t \\pm (k \\times S\_t)$. |
| **URS-V-14** | **Non-Parametric Limits:** If Non-Parametric, the system shall define limits strictly using the order statistics (min/max) of the final sample. | **1-Sided LSL:** Limit \= $\\min(X)$. **1-Sided USL:** Limit \= $\\max(X)$. **2-Sided:** Limits \= $\[\\min(X), \\max(X)\]$. |
| **URS-V-15** | **Back-Transformation:** The system MUST mathematically back-transform calculated parametric limits to the original engineering units. | Example (Box-Cox): $Limit\_{orig} \= (\\lambda \\cdot Limit\_t \+ 1)^{1/\\lambda}$. |
| **URS-V-16** | **Pass/Fail & Capability:** The system shall compare the back-transformed limits to the original specifications to output Pass/Fail, and calculate Process Capability ($P\_{pk}$) for normal/transformed data. | $P\_{pk} \= \\min(P\_{pu}, P\_{pl})$. (Hidden for Non-Parametric data). |

---

## 3\. User Interface (UI) Requirements

| ID | Requirement Description | Implementation Detail |
| :---- | :---- | :---- |
| **URS-UI-01** | **Sequential Workflow Enforcer:** Tab 2 (Variable Data) must prevent the user from progressing to Phase 3/4 until Phase 1/2 are fully executed. | UI elements for Final Validation remain disabled until Pilot Data is normalized. |
| **URS-UI-02** | **Method Transparency:** The UI shall display a prominent dynamic text block showing the active mathematical path. | E.g., *"Path: Log-Transformed $\\rightarrow$ 2-Sided Spec ($k\_2$) $\\rightarrow$ Back-Transformed Limit."* |
| **URS-UI-03** | **Contextual Tooltips:** Every statistical input/output must feature a tooltip explaining its function. | E.g., Hovering on $k\_2$ displays: "Two-sided tolerance factor based on Howe-Guenther approximation." |

---

## 4\. Reporting & Data Integrity Requirements

| ID | Requirement Description | Acceptance Criteria |
| :---- | :---- | :---- |
| **URS-REP-01** | **User Calculation Report:** The system shall generate a downloadable PDF report summarizing the current session. | **Content:** Date/Time, User Inputs ($C, R, c$), Calculated Results ($n, k, Limits, P\_{pk}$), and Method Used. |
| **URS-REP-02** | **Validation State Reference:** The User Calculation Report must display the **SHA-256 Hash** of the current calculation engine file (calculations.py). | The report must clearly state: "Engine Hash: \[HashValue\]" to prove the code has not been altered since validation. |
| **URS-REP-03** | **Integrity Check:** The User Calculation Report must compare the current Engine Hash against a stored "Validated Hash". | If hashes match: Print "VALIDATED STATE: YES". If mismatch: Print "VALIDATED STATE: NO \- UNVERIFIED CHANGE". |
| **URS-REP-04** | **Automated Validation Report:** The IQ/OQ/PQ test suite must generate a self-contained PDF report ("Validation Certificate"). | **Content:** Test Date, Tester Name, System Info (OS, Python Ver), List of all URS IDs tested, Pass/Fail status for each, and the final "Validated Hash" of the engine. |

---

## 5\. Automated Validation Requirements (IQ/OQ/PQ)

| ID | Requirement Description | Acceptance Criteria |
| :---- | :---- | :---- |
| **URS-IQ-01** | **Installation Qualification (IQ):** Dependencies must be strictly version-locked using a hash-based lockfile. | `uv sync` must succeed without conflict. Environment check script confirms `scipy==1.x.x` version. |
| **URS-OQ-01** | **Operational Qualification (OQ):** A `pytest` suite shall verify all mathematical models against known standard values. | Tests must carry markers linking to URS IDs (e.g., `@pytest.mark.urs("URS-FUNC_A-02")`). All tests must PASS. |
| **URS-PQ-01** | **Performance Qualification (PQ):** An automated UI test (using `Playwright`) shall simulate a user workflow. All paths should be tested e2e including generated pdf-reports. | Open Tab \-\> Enter Data \-\> Click Calculate \-\> Verify Output Text appears-\> generate report-\>read and verify contend. |

---

## 6\. Verification Traceability Matrix (VTM) Structure

| ID | Requirement Description | Acceptance Criteria |
| :---- | :---- | :---- |
| **URS-VTM-01** | The VTM must include the URS ID AND corresponding text | `URS-IQ-01:` **Installation Qualification (IQ):** Dependencies must be strictly version-locked using a hash-based lockfile. |
| **URS-VTM-02** | The VTM must include the test id | tests/test\_a:xy |
| **URS-VTM-03** | The VTM must include the test result | passed/failed |

---

## 7\. Non-traceable requirements

| ID | Requirement Description | Acceptance Criteria |
| :---- | :---- | :---- |
| **x** | GUI Framework: NiceGUI | NiceGUI |
| **x** | Data models: one point of truth | \- |
| **x** | Package manager: uv | uv |
| **x** | Test Framework: pytest | pytest |
| **x** | UI Testframework: playwright | playwright |
| **x** | Real e2e test of ui and reports |  |
| **x** | aggregated test (ui+report) |  |
| **x** | Reports: generated with reportlab, line-break in tables with flowable paragraph | no overflow in table cells |
| **x** | easy installable via docker compose | no manual intervention needed for validated system state |

---

