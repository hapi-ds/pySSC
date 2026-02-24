# Multi-stage Dockerfile for Sample Size Calculator
# Requirements: 35.1, 35.5

# ============================================================================
# Builder Stage: Install dependencies and Playwright
# ============================================================================
FROM python:3.11-slim AS builder

# Install system dependencies required for uv and Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files, LICENSE, and README (required by pyproject.toml)
COPY pyproject.toml uv.lock LICENSE README.md ./

# Install Python dependencies using uv (frozen lockfile, including dev dependencies for validation)
# Note: Dev dependencies include pytest, playwright, and pytest-json-report needed for IQ/OQ/PQ tests
RUN uv sync --frozen

# Install Playwright and chromium browser with system dependencies
# This is required for PQ validation tests
RUN uv run playwright install --with-deps chromium

# ============================================================================
# Production Stage: Minimal runtime image
# ============================================================================
FROM python:3.11-slim

# Install runtime dependencies for Playwright chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Chromium dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libxshmfence1 \
    # Additional utilities
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy uv binary from builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy Playwright browsers from builder
COPY --from=builder --chown=appuser:appuser /root/.cache/ms-playwright /home/appuser/.cache/ms-playwright

# Copy project configuration files needed for IQ tests
COPY --chown=appuser:appuser pyproject.toml uv.lock LICENSE README.md /app/

# Copy application source code, scripts, and tests
COPY --chown=appuser:appuser src/ /app/src/
COPY --chown=appuser:appuser scripts/ /app/scripts/
COPY --chown=appuser:appuser tests/ /app/tests/

# Create directories for logs, reports, and pytest cache with correct permissions
RUN mkdir -p /app/logs /app/reports /app/.pytest_cache /app/.hypothesis && \
    chown -R appuser:appuser /app/logs /app/reports /app/.pytest_cache /app/.hypothesis /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src:$PYTHONPATH" \
    PLAYWRIGHT_BROWSERS_PATH="/home/appuser/.cache/ms-playwright"

# Expose port 8080 for web interface
EXPOSE 8080

# Add healthcheck to verify application is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Set CMD to run the application
CMD ["uv", "run", "python", "src/sample_size_calculator/main.py"]
