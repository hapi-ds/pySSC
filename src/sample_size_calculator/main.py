"""Main entry point for the Sample Size Calculator application.

This module initializes and runs the NiceGUI web application for medical device
design verification and process validation sample size calculations.

The application provides two analysis modules:
- Module A: Attribute (binary Pass/Fail) data analysis
- Module V: Variable (continuous measurement) data analysis with 4-phase workflow

The application runs on port 8080 by default and can be accessed via web browser.
All user interactions are logged for QMS compliance and audit trail purposes.

Usage:
    Run directly:
        $ uv run python src/sample_size_calculator/main.py

    Or via module:
        $ uv run python -m sample_size_calculator.main

Environment Variables:
    PORT: Web server port (default: 8080)
    LOG_LEVEL: Logging level (default: INFO)
    LOG_RETENTION_DAYS: Log file retention period (default: 90)

Requirements: 35.4, 36.1, 36.2
"""

from sample_size_calculator.ui_controller import create_ui

if __name__ == "__main__":
    create_ui()
