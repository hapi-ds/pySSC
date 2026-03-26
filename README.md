<p align="center">
  <a href="https://github.com/hapi-ds/pySSC/releases">
    <img src="https://img.shields.io/github/v/release/hapi-ds/pySSC?style=flat-square&color=blue" alt="Latest Release">
  </a>
  <img src="https://img.shields.io/badge/python-3.11%20%7C%203.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python Version">
  <a href="https://github.com/hapi-ds/pySSC/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/hapi-ds/pySSC?style=flat-square" alt="License">
  </a>
</p>

# Sample Size Calculator

Medical device design verification and process validation sample size calculator compliant with ISO/TR 80002-2 standards.

## Motivation

Test project for:

- Spec-Driven Development (SDD) with coding-agents (I used Kiro, Antigravity, Opencode with different local llms)
- The feasibility of self-validating software (complient with ISO/TR 80002-2)

## Result and Current Status

- Main functionality provided
- Software validation still far from complete
- Example applications are explained in a Jupyter Notebook (see ./testdata), including the generation of corresponding test data.

SDD development with coding agents is incredibly fast and virtually a must for any commercial software development. In some simple things, however, it's almost unbearable because of sheer stupidity. The problem here is that you often get “stuck” in the workflow (=lazy) and spend too much time looking for ways to solve it with the coding agent. But coding agents are improving so rapidly that this problem will quickly resolve itself.

The three encoding agents are in a neck-and-neck race. Especially with the latest update of the qwen3-coder-next LLM, my local assistant feels like it's on par with the “big ones”—I would even say that it works better in some ways.
But this is constantly changing—at times, the same version worked better on Windows, then again on Linux. This shows how rapidly this technology is developing.

BUT

Without human support, even such a small, simple project is not possible. And SW validation and E2E testing with meaningful data are definitely not the strong points of current agents. In principle, however, the approach of self-validating software is feasible and, in my view, also more secure than other approaches - I'll stay on it.


## Overview

The Sample Size Calculator is a Python-based web application for determining statistically valid sample sizes for medical device design verification and process validation. This is critical QMS (Quality Management System) software that ensures compliance with ISO/TR 80002-2 standards through comprehensive validation, hash-based integrity verification, and complete audit trail logging.

### Key Features

- **Module A (Attribute Data Analysis)**: Binary Pass/Fail data analysis using Success Run Theorem and Cumulative Binomial Distribution
- **Module V (Variable Data Analysis)**: Continuous measurement analysis with strict 4-phase sequential workflow
  - Phase 1: Specification definition and pilot data input with IQR-based outlier detection
  - Phase 2: Outlier exclusion and automatic transformation cascade (Log → Box-Cox → Yeo-Johnson)
  - Phase 3: Sample size calculation using parametric or non-parametric methods
  - Phase 4: Final validation data analysis with tolerance interval calculation
- **SHA-256 Hash Verification**: Ensures calculation engine integrity and validated state tracking
- **Comprehensive Audit Trail**: All user interactions and system events logged with timestamps
- **Automated Validation Suite**: IQ/OQ/PQ testing with Verification Traceability Matrix (VTM) generation
- **PDF Report Generation**: User calculation reports, validation certificates, and comprehensive full reports
- **Method Transparency**: Clear display of active mathematical paths and statistical methods

## Installation

### Recommended

Docker Compose (no need to install playwright)

```bash
# build it
docker compose build
# start it
docker compose up -d
# optional validate it - need some time
docker compose exec sample-size-calculator uv run python scripts/run_validation.py --tester "Your Name"
# connect to it / use it
http://localhost:8080
# shut down
docker compose down
```

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Local Installation

```bash
# Clone the repository
git clone <repository-url>
cd sample-size-calculator

# Install dependencies using uv
uv sync

# Install with development dependencies (for testing and validation)
uv sync --all-groups
```

### Verify Installation

```bash
# Check Python version
uv run python --version

# Run a quick test
uv run pytest tests/validation/test_iq.py -q
```

## Usage

### Local Development

Start the application locally:

```bash
uv run python src/sample_size_calculator/main.py
```

The web interface will be available at **http://localhost:8080**

### Module A: Attribute Data Analysis

Module A is designed for binary (Pass/Fail) test scenarios.

**Workflow:**

1. Navigate to the **Module A** tab
2. Enter **Confidence Level** (e.g., 95%)
3. Enter **Reliability Level** (e.g., 95%)
4. Enter **Allowable Failures** (c):
   - Enter a specific value (e.g., 0, 1, 2) for single calculation
   - Leave empty for sensitivity analysis (calculates for c=0, 1, 2, 3)
5. Click **Calculate Sample Size**
6. Review results showing required sample size
7. Click **Generate PDF Report** to create documentation

**Example Use Case:**
- Confidence: 95%
- Reliability: 95%
- Allowable Failures: 0
- Result: n = 59 samples (Success Run Theorem)

### Module V: Variable Data Analysis

Module V provides a comprehensive 4-phase workflow for continuous measurement data.

#### Phase 1: Specification Definition and Pilot Data

1. Select **Specification Type**:
   - **One-Sided**: Define either Lower Specification Limit (LSL) or Upper Specification Limit (USL)
   - **Two-Sided**: Define both LSL and USL
2. Enter specification limits
3. Enter **Confidence** and **Reliability** levels
4. Input pilot data:
   - **Dataset Method**: Enter comma-separated measurements
   - **Statistics Method**: Enter estimated mean and standard deviation
5. Click **Analyze Pilot Data**
6. Review outlier detection results (Q1, Q3, IQR, flagged outliers)

**Note**: Pilot datasets with fewer than 30 points will trigger a validation warning.

#### Phase 2: Normality Testing and Transformation

1. Review detected outliers
2. Optionally exclude outliers (requires engineering rationale)
3. Choose transformation approach:
   - **Automatic Cascade**: System tries Log → Box-Cox → Yeo-Johnson transformations
   - **Manual Override**: Select specific transformation method
4. Click **Process Normality Testing**
5. Review results:
   - Shapiro-Wilk p-values for each transformation
   - Locked transformation method
   - Analysis method (Parametric or Non-Parametric)

**Transformation Cascade Logic:**
- If original data is normal (p > 0.05): Lock as Parametric
- If not normal: Try Log transformation (requires all positive values)
- If Log fails: Try Box-Cox transformation (requires all positive values)
- If Box-Cox fails: Try Yeo-Johnson transformation (handles zero/negative values)
- If all fail: Lock as Non-Parametric (Wilks method)

#### Phase 3: Sample Size Calculation

1. Review locked method and specification type
2. Click **Calculate Required Sample Size**
3. Review results:
   - Capability margin (k_margin)
   - Tolerance factor (k_factor)
   - Required sample size (N)
   - Formula used (e.g., Howe-Guenther Approximation)

#### Phase 4: Final Validation and Tolerance Limits

1. Collect final validation dataset of size N
2. Enter final data (comma-separated)
3. Click **Calculate Tolerance Limits**
4. Review results:
   - Tolerance limits in transformed and original space
   - Comparison to specification limits
   - **Pass/Fail** determination
   - Process capability index (Ppk) for parametric methods
5. Click **Generate PDF Report** to document results

### Running Validation (IQ/OQ/PQ)

The application includes a built-in validation runner accessible from the UI:

1. Click the **Run Full Validation (IQ/OQ/PQ)** button in the UI header
2. Enter your name as the validation tester
3. Click **Start Validation**
4. Monitor progress as the system runs:
   - **IQ (Installation Qualification)**: Verifies dependencies and installation
   - **OQ (Operational Qualification)**: Tests all calculation formulas against known values
   - **PQ (Performance Qualification)**: Runs end-to-end UI tests (skipped when app is running)
5. Review validation results
6. Download the validation certificate from `./reports/validation/`

**Note**: PQ tests are automatically skipped when running validation from the UI since they require the application to be stopped. For complete validation including PQ tests, use the command-line approach below.

### Command-Line Validation

For complete validation including PQ tests:

```bash
# Stop the application first
# Then run the validation script
uv run python scripts/run_validation.py --tester "Your Name"
```

This generates:
- Validation certificate PDF in `./reports/validation/`
- Verification Traceability Matrix (VTM) CSV
- Updates validated hash in `config/validated_hash.json`

## Docker Deployment

### Quick Start

```bash
# Build and start the container
docker compose up -d

# View logs
docker compose logs -f

# Stop the container
docker compose down
```

The application will be available at **http://localhost:8080** (or custom port via PORT environment variable).

### Configuration

Create a `.env` file in the project root to customize deployment:

```env
PORT=8080
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=90
```

### Volume Mounts

The docker-compose configuration automatically mounts:

- `./logs`: Audit trail logs (read/write)
- `./config`: Configuration files including validated_hash.json (read-only)
- `./reports`: Generated PDF reports (read/write)

All reports and logs persist across container restarts.

### Health Checks

The Docker container includes automatic health checks:
- Endpoint: `http://localhost:8080/`
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3

Check container health:

```bash
docker compose ps
```

### Playwright Support

The Docker image includes Chromium and all dependencies required for automated UI testing (PQ tests). This ensures the validation suite can run completely within the container.

## Reports Directory Structure

All generated reports are organized in the `./reports/` directory:

```
reports/
├── validation/     # IQ/OQ/PQ validation certificates
├── calculations/   # Sample size calculation reports
└── full/          # Comprehensive full reports
```

### Report Types

#### Calculation Reports (`./reports/calculations/`)

Generated when you click "Generate PDF Report" after completing a calculation. Includes:
- Timestamp and session information
- All input parameters
- Calculated results
- Statistical method used
- Engine hash and validation state

**Naming**: `calculation_report_YYYYMMDD_HHMMSS.pdf`

#### Validation Certificates (`./reports/validation/`)

Generated by the IQ/OQ/PQ validation suite. Includes:
- Test execution date and tester name
- System information (OS, Python version)
- Complete test results with URS traceability
- Verification Traceability Matrix (VTM)
- Validated engine hash

**Naming**: `validation_certificate_YYYYMMDD_HHMMSS.pdf`

#### Full Reports (`./reports/full/`)

Comprehensive reports combining:
- Current calculation report
- Latest validation certificates
- Audit trail logs (filtered for session)
- Calculator signature (engine hash and validation state)

**Naming**: `full_report_YYYYMMDD_HHMMSS.pdf`

### Generating Full Reports

Click the **Generate Full Report** button in the UI after completing a calculation to create a comprehensive report with complete traceability.

## Development

### Running Tests

```bash
# Run all tests
uv run pytest -q

# Run specific test suites
uv run pytest tests/validation/test_iq.py -q  # Installation Qualification
uv run pytest tests/validation/test_oq.py -q  # Operational Qualification
uv run pytest tests/validation/test_pq.py -q  # Performance Qualification

# Run property-based tests
uv run pytest tests/property/ -q

# Run with coverage
uv run pytest --cov=src/sample_size_calculator --cov-report=html
```

### Code Quality

```bash
# Run linter
uv run ruff check src/

# Format code
uv run ruff format src/

# Type checking
uv run ty check src/
```

### Adding Dependencies

```bash
# Add a runtime dependency
uv add <package-name>

# Add a development dependency
uv add --group dev <package-name>

# Sync dependencies after changes
uv sync
```

## Architecture Overview

### High-Level Components

```
┌─────────────────────────────────────────────────────────┐
│                    NiceGUI Web Interface                 │
│                  (Module A | Module V)                   │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                    UI Controller                         │
│         (Session Management, Workflow Enforcement)       │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼──────┐  ┌────────▼────────┐
│  Calculation   │  │Transformation│  │    Tolerance    │
│    Engine      │  │    Engine    │  │   Calculator    │
└────────────────┘  └──────────────┘  └─────────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼──────┐  ┌────────▼────────┐
│  Hash Verifier │  │Audit Logger │  │Report Generator │
└────────────────┘  └──────────────┘  └─────────────────┘
```

### Key Design Principles

1. **Single Source of Truth**: Pydantic models define all data structures
2. **Sequential Workflow Enforcement**: UI prevents phase-skipping in Module V
3. **Method Transparency**: Active mathematical paths clearly displayed
4. **Validation-First**: Hash-based verification ensures calculation integrity
5. **Audit Trail**: Comprehensive logging of all interactions
6. **Reproducibility**: Deterministic calculations with locked transformations

### Technology Stack

- **Web Framework**: NiceGUI (Python reactive UI)
- **Calculation Engine**: NumPy, SciPy (statistical computations)
- **Data Validation**: Pydantic (models and validation)
- **PDF Generation**: ReportLab (reports and certificates)
- **Testing**: pytest (unit/OQ), playwright (UI/PQ), hypothesis (property-based)
- **Logging**: Python logging with rotation
- **Deployment**: Docker Compose
- **Package Management**: uv (hash-based lockfile)

## Troubleshooting

### Application Won't Start

**Issue**: Application fails to start or shows import errors

**Solution**:
```bash
# Ensure dependencies are installed
uv sync --all-groups

# Check Python version (requires 3.11+)
uv run python --version

# Check for port conflicts
lsof -i :8080  # On Unix/Linux/Mac
netstat -ano | findstr :8080  # On Windows
```

### Validation Tests Failing

**Issue**: IQ/OQ/PQ tests fail during validation

**Solution**:
```bash
# Check dependency versions
uv run pip list

# Ensure scipy version is 1.x.x
uv run python -c "import scipy; print(scipy.__version__)"

# Run tests individually to identify failures
uv run pytest tests/validation/test_iq.py -v
uv run pytest tests/validation/test_oq.py -v
```

### Docker Container Issues

**Issue**: Container fails health checks or won't start

**Solution**:
```bash
# Check container logs
docker compose logs

# Rebuild container
docker compose down
docker compose build --no-cache
docker compose up -d

# Verify volume permissions
ls -la ./logs ./reports ./config
```

### Validation State Shows "NO"

**Issue**: Reports show "VALIDATED STATE: NO - UNVERIFIED CHANGE"

**Solution**:
This indicates the calculation engine has been modified since the last validation. To restore validated state:

1. Review changes to `src/sample_size_calculator/calculations.py`
2. If changes are intentional, run full validation:
   ```bash
   uv run python scripts/run_validation.py --tester "Your Name"
   ```
3. This will update the validated hash in `config/validated_hash.json`

### Reports Not Generating

**Issue**: PDF reports fail to generate or save

**Solution**:
```bash
# Check reports directory permissions
ls -la ./reports

# Ensure subdirectories exist
mkdir -p ./reports/validation ./reports/calculations ./reports/full

# Check disk space
df -h  # On Unix/Linux/Mac
```

### Transformation Cascade Issues

**Issue**: Module V Phase 2 fails or locks as Non-Parametric unexpectedly

**Solution**:
- Ensure pilot data has at least 3 data points
- Check for non-numeric values in dataset
- For Log/Box-Cox transformations, ensure all values are positive
- Review Shapiro-Wilk p-values in the UI
- Consider using manual override to select specific transformation

### Playwright Tests Failing

**Issue**: PQ tests fail with browser errors

**Solution**:
```bash
# Install Playwright browsers
uv run playwright install --with-deps chromium

# For Docker, rebuild the image
docker compose build --no-cache
```

### Log Files Growing Too Large

**Issue**: Log directory consuming excessive disk space

**Solution**:
- Logs automatically rotate at 10MB per file
- Retention is 90 days by default
- Adjust retention in `.env` file:
  ```env
  LOG_RETENTION_DAYS=30
  ```
- Manually clean old logs:
  ```bash
  find ./logs -name "*.log.*" -mtime +30 -delete
  ```

## Project Structure

```
sample-size-calculator/
├── src/
│   └── sample_size_calculator/
│       ├── __init__.py
│       ├── main.py                    # Application entry point
│       ├── models.py                  # Pydantic data models
│       ├── calculations.py            # Core calculation engine
│       ├── transformations.py         # Data transformation engine
│       ├── outliers.py                # IQR outlier detection
│       ├── normality.py               # Shapiro-Wilk testing
│       ├── tolerance.py               # Tolerance interval calculations
│       ├── hash_verifier.py           # SHA-256 verification
│       ├── audit_logger.py            # Audit trail logging
│       ├── report_generator.py        # PDF report generation
│       ├── full_report_generator.py   # Comprehensive report generation
│       ├── vtm_generator.py           # VTM generation
│       ├── ui_controller.py           # NiceGUI interface
│       ├── validation_runner.py       # IQ/OQ/PQ runner
│       └── report_paths.py            # Report path management
├── tests/
│   ├── property/                      # Property-based tests (Hypothesis)
│   ├── validation/                    # IQ/OQ/PQ validation tests
│   │   ├── test_iq.py                # Installation Qualification
│   │   ├── test_oq.py                # Operational Qualification
│   │   └── test_pq.py                # Performance Qualification
│   └── test_*.py                      # Unit and integration tests
├── config/
│   └── validated_hash.json            # Validated engine hash storage
├── logs/
│   └── audit.log                      # Audit trail logs (rotated)
├── reports/
│   ├── validation/                    # Validation certificates
│   ├── calculations/                  # Calculation reports
│   └── full/                          # Full comprehensive reports
├── scripts/
│   └── run_validation.py              # Validation runner script
├── docker-compose.yml                 # Docker Compose configuration
├── Dockerfile                         # Docker image definition
├── pyproject.toml                     # Project metadata and dependencies
├── uv.lock                            # Locked dependency versions
└── README.md                          # This file
```

## Compliance and Validation

This application is designed for use in regulated medical device environments and follows ISO/TR 80002-2 guidelines for computer software validation.

### Validation Approach

- **IQ (Installation Qualification)**: Verifies correct installation and dependency versions
- **OQ (Operational Qualification)**: Tests all mathematical formulas against known standard values
- **PQ (Performance Qualification)**: End-to-end UI testing with realistic workflows

### Traceability

- All requirements linked to test cases via URS markers
- Verification Traceability Matrix (VTM) generated automatically
- Complete audit trail of all user interactions
- SHA-256 hash verification of calculation engine

### Audit Trail

All events are logged with:
- ISO 8601 timestamps
- Session identifiers
- Event types and context
- Input/output values
- Validation results

Logs are stored in `./logs/` with 90-day retention and automatic rotation.

## License

See LICENSE file for details.

## Support

For issues, questions, or contributions, please refer to the project repository.

---

**Version**: 0.1.0  
**Last Updated**: 2026.02.26  
**Compliance**: ISO/TR 80002-2
