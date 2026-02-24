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

### Local Development

```bash
# Run the application
uv run python src/sample_size_calculator/main.py
```

The application will be available at http://localhost:8080

### Docker Deployment

```bash
# Build and start the container
docker compose up -d

# View logs
docker compose logs -f

# Stop the container
docker compose down
```

The application will be available at http://localhost:8080 (or custom port via PORT environment variable).

#### Environment Variables

Configure the application using environment variables or a `.env` file:

- `PORT`: Web interface port (default: 8080)
- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_RETENTION_DAYS`: Log retention period (default: 90)

Example `.env` file:
```
PORT=8080
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=90
```

#### Volume Mounts

The docker-compose configuration mounts the following directories:

- `./logs`: Audit trail logs (read/write)
- `./config`: Configuration files including validated_hash.json (read-only)
- `./reports`: Generated PDF reports (read/write)

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
