<p align="center">
  <a href="https://github.com/hapi-ds/pySSC/releases">
    <img src="https://img.shields.io/github/v/release/hapi-ds/pySSC?style=flat-square&color=blue" alt="Latest Release">
  </a>
  <img src="https://img.shields.io/badge/python-3.11%20%7C%203.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python Version">
  <a href="https://github.com/hapi-ds/pySSC/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/hapi-ds/pySSC?style=flat-square" alt="License">
  </a>
</p>

<p align="center">
  <a href="https://github.com/hapi-ds/pySSC/actions">
    <img src="https://github.com/hapi-ds/pySSC/actions/workflows/ci.yml/badge.svg" alt="CI Pipeline Status">
  </a>
  <a href="https://github.com/hapi-ds/pySSC/actions">
    <img src="https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/hapi-ds/aa5bb33df835905782de38749202e3f0/raw/pytest-coverage.json" alt="Coverage">
  </a>
</p>

# Sample Size Calculator

Medical device design verification and process validation sample size calculator compliant with ISO/TR 80002-2 standards.

## Overview

The Sample Size Calculator is a Python/niceGUI-based web application for determining statistically valid sample sizes for medical device design verification and process validation. As this is critical QMS (Quality Management System) software we have to ensures compliance with ISO/TR 80002-2 standards through comprehensive validation - and this is done via one click.
You can find some tutorials/videos on my homepage https://www.koehler.eu.com/en/home/.

### Key Features

- **Module Attribute**: Binary Pass/Fail data analysis using Success Run Theorem and Cumulative Binomial Distribution
- **Module Variable**: Continuous measurement analysis with strict 4-phase sequential workflow
  - Phase 1: Specification definition and (pilot) data input with IQR-based outlier detection
  - Phase 2: Outlier exclusion and automatic transformation cascade (Log → Box-Cox → Yeo-Johnson)
  - Phase 3: Sample size calculation using parametric or non-parametric methods
  - Phase 4: Final validation data analysis with tolerance interval calculation (if enough data are provided in step 1)
- **SHA-256 Hash Verification**: Ensures calculation engine integrity and validated state tracking
- **Comprehensive Audit Trail**: All user interactions and system events logged with timestamps
- **Automated Validation Suite**: IQ/OQ/PQ testing with Verification Traceability Matrix (VTM) generation
- **PDF Report Generation**: User calculation reports, validation certificates, and comprehensive full reports
- **Method Transparency**: Clear display of active mathematical paths and statistical methods

## Installation

### Recommended

Docker Compose

```bash
# build it
docker compose build
# start it
docker compose up -d
# connect to it / use it
http://localhost:8080
# shut down
docker compose down
```

### Local Installation

```bash
# Clone the repository
git clone <repository-url>
cd sample-size-calculator

# Install dependencies using uv
uv sync

# Install with development dependencies (for testing and validation)
uv sync --all-groups

# Configure playwright for e2e tests
uv run playwright install --with-deps chromium

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

Help and examples are accessable also via web interface

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
6. Download the validation certificate if needed - validation is valid as long as button is green (checked via hash of code) (maybe you have to reload page for the green button)


### Configuration

Create a `.env` file in the project root to customize deployment:

```env
PORT=8080
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=90
```

### Data Storage

**Internal Storage (Default)**: All data stays inside the Docker container:
- Audit logs in `/app/logs/`
- Configuration in `/app/config/`  
- Reports in `/app/reports/`

This approach avoids permission issues across all platforms (Linux, macOS, Windows).

To retrieve data from a running container:

```bash
# Copy logs from container to host
docker compose cp sample-size-calculator:/app/logs ./logs

# Copy reports from container to host
docker compose cp sample-size-calculator:/app/reports ./reports

# Copy config from container to host
docker compose cp sample-size-calculator:/app/config ./config
```

**Host Volume Mounts (Alternative)**: If you need data persistence on the host filesystem, uncomment the volume mounts in `docker-compose.yml` and ensure proper permissions are set for your host user.

### Volume Mounts (Alternative)

If you prefer host-mounted volumes for persistence, uncomment the volume mounts in `docker-compose.yml`. When using bind mounts:

- On **Linux**: Ensure your user has write permissions to the mounted directories
- On **macOS/Windows**: Use Docker Desktop's file sharing or ensure directories exist before starting

Example (uncomment in docker-compose.yml):
```yaml
volumes:
  - ./logs:/app/logs
  - ./config:/app/config
  - ./reports:/app/reports
```

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

**Solution (Internal Storage)**:
- Logs automatically rotate at 10MB per file
- Retention is 90 days by default
- Adjust retention in `.env` file:
  ```env
  LOG_RETENTION_DAYS=30
  ```
- Copy logs to host for inspection:
  ```bash
  docker compose cp sample-size-calculator:/app/logs ./logs
  ```

**Solution (Host Volume Mounts)**:
- Manually clean old logs after copying:
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
