# Sample Size Calculator

Medical device design verification and process validation sample size calculator.

## Overview

The Sample Size Calculator is a Python-based web application for determining statistically valid sample sizes for medical device design verification and process validation. This is critical QMS (Quality Management System) software that must comply with ISO/TR 80002-2 standards.

## Features

- **Module A**: Attribute (binary) data analysis using Success Run Theorem and Cumulative Binomial Distribution
- **Module V**: Variable (continuous) data analysis with 4-phase sequential workflow
- SHA-256 hash verification for calculation engine integrity
- Comprehensive audit trail logging
- Automated validation reporting (IQ/OQ/PQ)

## Installation

```bash
# Install dependencies
uv sync

# Install with dev dependencies
uv sync --all-groups
```

## Usage

```bash
# Run the application
uv run python src/sample_size_calculator/main.py
```

## Development

```bash
# Run tests
uv run pytest -q

# Run linter
uv run ruff check src/

# Format code
uv run ruff format src/
```

## Project Structure

```
.
 src/
    sample_size_calculator/
        __init__.py
        (application modules)
 tests/
    (test modules)
 config/
    (configuration files)
 logs/
    (application logs)
 pyproject.toml
 uv.lock
```

## License

See LICENSE file for details.
