# **1. Risk Assessment (ISO 14971 / ISO/TR 80002‑2 Framework)**

The Sample Size Estimator is classified as **Medium Risk QMS Support Software**, as it influences quality and regulatory decisions but does not directly control devices or processes affecting patients. The following synthesis consolidates identified hazards, risk control measures, and residual risk outcomes from all model inputs.

## **Foundational Risk Classification**
| Risk Parameter | Description |
|-----------------|--------------|
| **Software Category** | QMS-relevant (Statistical support software) |
| **Risk Level** | Medium |
| **Primary Standards Basis** | ISO 14971, ISO/TR 80002‑2, IEC 62304, GAMP 5 |
| **Rationale** | Incorrect sample size outputs could compromise device validation evidence and indirectly affect product safety or regulatory compliance. |

## **Major Hazard Categories and Controls**

| **Hazard Category** | **Description / Potential Harm** | **Risk Controls (URS-Derived)** | **Residual Risk** |
|----------------------|----------------------------------|----------------------------------|--------------------|
| **1. Algorithm Implementation Errors** | Fault in statistical formulae (e.g., binomial, tolerance intervals, k-factor, or transformation back-calculations) could yield incorrect sample sizes. | Independent algorithm review; unit/validation testing; traceability matrix linking URS to verification tests; documented peer review. | Acceptable post-validation. |
| **2. User Input / Workflow Errors** | Incorrect sequence or invalid parameter progression could produce statistically invalid results. | Sequential workflow enforcement (URS‑UI‑01), real-time validation (URS‑DV series). | Acceptable with procedural training. |
| **3. Method Opaqueness / Misinterpretation** | Users misapply statistical methods due to lack of clarity about which approach is active. | Display of active method (“method transparency,” URS‑UI‑02), contextual tooltips (URS‑UI‑03). | Low residual risk; mitigated through interface controls and training. |
| **4. Data Integrity & Reporting Failures** | Loss, corruption, or incomplete record generation may hinder regulatory traceability. | Version control, configuration management, audit trail functionality (recommended enhancement), report export verification. | Acceptable if audit trail and retention controls are implemented. |
| **5. Documentation / Tooltip Errors** | Missing or inaccurate explanations lead to parameter misuse. | QA review of UI documentation; change control for tooltip content. | Acceptable with documented review. |
| **6. Configuration Management or Change Control Failures** | Post-release updates without verification introduce new calculation or interface errors. | Controlled change management process; revalidation upon major updates. | Acceptable contingent on ongoing validation practices. |

## **Risk Control Framework**
- **Software Validation:** Compliance with ISO /TR 80002‑2 & FDA guidance through full verification testing and traceability documentation.  
- **User Interface & Usability Controls:** Sequential UI, contextual help, and data validation logic reduce operator error.  
- **Configuration Management:** Enforced versioning, documented changes, and configuration release controls.  
- **Training and Documentation:** Clear user instructions, statistical method explanation, and examples improve correct usage.  
- **Data Handling Controls (Recommended Enhancements):**  
  - Implement **user authentication** and **audit trail logging** for multi-user environments.  
  - Define **data retention** format and duration for generated reports.  
  - Include **software version display** and **backup/recovery** requirements.  

---

# **2. Residual Risk and Overall Acceptability**

After application of controls and completion of formal validation:  
- **Residual Risk Level:** *Acceptable for use* by professionals as validated docker image.  
- **Key Acceptance Conditions:**  
  - Validation and verification completed and documented per URS.  
  - Users are trained and qualified.  
  - Configuration and change controls are enforced.  
  - Periodic risk review and software revalidation occur per QMS schedule.  

---

# **3. Summary**

**The Sample Size Estimator** serves as a validated, QMS-integrated statistical tool that supports compliance with regulatory expectations for design verification and process validation sample size determination.  
By combining robust mathematical transparency, guided workflows, and validated statistical computation, it ensures scientifically defensible sampling plans while maintaining acceptable residual risk under ISO 14971 principles.  

Future URS development should reinforce **audit trail, authentication, data retention, and versioning** requirements to sustain compliance as the software evolves.