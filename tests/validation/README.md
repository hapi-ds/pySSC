# Validation Test Suite (IQ/OQ/PQ)

This directory contains the validation test suite for the Sample Size Calculator application, following ISO/TR 80002-2 standards for medical device software validation.

## Test Suite Structure

### Installation Qualification (IQ) - `test_iq.py`
Verifies correct installation and configuration:
- uv.lock file exists and is valid
- Dependencies install without conflicts
- Required packages are present (scipy, nicegui, pydantic, etc.)
- Python version meets requirements
- Project structure is correct

**Run IQ tests:**
```bash
uv run pytest tests/validation/test_iq.py -v -m iq
```

### Operational Qualification (OQ) - `test_oq.py`
Verifies mathematical formulas and calculations:
- Module A formulas (Success Run Theorem, Cumulative Binomial)
- Module V formulas (tolerance factors, transformations)
- Known standard values (C=95%, R=95%, c=0 → n=59)
- Edge cases (boundary values, empty datasets, zero variance)
- Transformation round-trip accuracy
- Numerical stability

**Run OQ tests:**
```bash
uv run pytest tests/validation/test_oq.py -v -m oq
```

### Performance Qualification (PQ) - `test_pq.py`
Verifies end-to-end workflows using Playwright:
- Complete Module A workflow (input → calculate → report)
- Complete Module V workflow (Phase 1 → 2 → 3 → 4)
- PDF report generation and content verification
- Concurrent user session isolation
- UI validation feedback
- Method transparency display

**Prerequisites for PQ tests:**
1. Install Playwright browsers:
   ```bash
   uv run playwright install
   # or
   uv run playwright install --with-deps chromium
   ```

2. Start the application:
   ```bash
   uv run python src/sample_size_calculator/main.py
   ```

3. Run PQ tests (in a separate terminal):
   ```bash
   uv run pytest tests/validation/test_pq.py -v -m pq
   ```

## Running Complete Validation Suite

### Local Validation

Use the automated validation script to run all tests and generate the validation certificate:

```bash
uv run python scripts/run_validation.py --tester "Your Name"
```

This will:
1. Run IQ, OQ, and PQ tests sequentially
2. Generate Verification Traceability Matrix (VTM)
3. Create validation certificate PDF
4. Store validated hash in `config/validated_hash.json`

**Options:**
- `--tester`: Required. Name of the validation tester
- `--output`: Output PDF filename (default: validation_certificate.pdf)
- `--skip-pq`: Skip PQ tests if application is not running

**Example:**
```bash
# Run full validation
uv run python scripts/run_validation.py --tester "Jane Smith"

# Skip PQ tests
uv run python scripts/run_validation.py --tester "Jane Smith" --skip-pq
```

### Docker Validation

To run the validation suite inside a Docker container:

```bash
# Start the container
docker compose up -d

# Execute validation script inside the container
docker compose exec sample-size-calculator uv run python scripts/run_validation.py --tester "Your Name" --skip-pq

# Or run specific test suites
docker compose exec sample-size-calculator uv run pytest tests/validation/test_iq.py -v -m iq
docker compose exec sample-size-calculator uv run pytest tests/validation/test_oq.py -v -m oq

# View generated validation certificate
ls -la ./reports/validation/

# Stop the container
docker compose down
```

**Note:** PQ tests should be skipped when running validation inside Docker (use `--skip-pq` flag) since the application is already running. PQ tests require starting/stopping the application and are best run locally before containerization.

## Test Markers

All tests use pytest markers for filtering:
- `@pytest.mark.iq` - Installation Qualification tests
- `@pytest.mark.oq` - Operational Qualification tests
- `@pytest.mark.pq` - Performance Qualification tests
- `@pytest.mark.urs("X.Y")` - Links test to specific URS requirement(s)

**Run specific test category:**
```bash
uv run pytest -m iq  # Only IQ tests
uv run pytest -m oq  # Only OQ tests
uv run pytest -m pq  # Only PQ tests
```

**Run tests for specific URS:**
```bash
uv run pytest -m 'urs("31.2")'  # Tests for URS 31.2
```

## Validation Artifacts

After running the validation suite, the following artifacts are generated:

1. **validation_certificate.pdf** - Official validation certificate with:
   - Test execution date and tester name
   - System information (OS, Python version)
   - Complete VTM with all test results
   - Validated engine hash

2. **validation_traceability_matrix.csv** - VTM in CSV format for analysis

3. **config/validated_hash.json** - Stored validated hash for integrity verification

4. **test_results_*.json** - Detailed pytest JSON reports for each suite

## Troubleshooting

**IQ tests fail:**
- Run `uv sync` to ensure dependencies are installed
- Check that uv.lock file exists
- Verify Python version >= 3.11

**OQ tests fail:**
- Check calculation formulas in `src/sample_size_calculator/calculations.py`
- Verify scipy is installed correctly
- Review test output for specific formula failures

**PQ tests fail:**
- Ensure application is running at http://localhost:8080
- Install Playwright browsers: `uv run playwright install`
- Check browser compatibility
- Review Playwright traces for UI interaction issues

**Validation script fails:**
- Ensure pytest-json-report is installed: `uv add --dev pytest-json-report`
- Check that all test files exist
- Verify config directory exists for hash storage
