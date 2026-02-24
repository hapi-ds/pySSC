"""Tests for validation runner module."""

import pytest
from pathlib import Path
from sample_size_calculator.validation_runner import ValidationRunner


def test_validation_runner_initialization():
    """Test that ValidationRunner can be initialized."""
    runner = ValidationRunner()
    assert runner is not None
    assert runner.test_results == []
    assert runner.all_passed is True


def test_validation_runner_with_callback():
    """Test that ValidationRunner accepts progress callback."""
    messages = []
    
    def callback(msg: str):
        messages.append(msg)
    
    runner = ValidationRunner(progress_callback=callback)
    runner._report_progress("Test message")
    
    assert len(messages) == 1
    assert messages[0] == "Test message"


def test_validation_runner_extract_test_results():
    """Test extraction of test results from pytest data."""
    runner = ValidationRunner()
    
    pytest_data = {
        "tests": [
            {
                "nodeid": "test_file.py::test_function",
                "outcome": "passed",
                "markers": [
                    {"name": "urs", "args": ["31.2", "31.3"]}
                ]
            }
        ]
    }
    
    results = runner._extract_test_results(pytest_data, "IQ")
    
    assert len(results) == 2  # One for each URS ID
    assert results[0]["urs_id"] == "31.2"
    assert results[0]["result"] == "PASSED"
    assert results[1]["urs_id"] == "31.3"
    assert results[1]["result"] == "PASSED"


def test_validation_runner_extract_failed_test():
    """Test extraction of failed test results."""
    runner = ValidationRunner()
    
    pytest_data = {
        "tests": [
            {
                "nodeid": "test_file.py::test_function",
                "outcome": "failed",
                "markers": [
                    {"name": "urs", "args": ["31.2"]}
                ]
            }
        ]
    }
    
    results = runner._extract_test_results(pytest_data, "OQ")
    
    assert len(results) == 1
    assert results[0]["result"] == "FAILED"
    assert results[0]["status"] == "FAILED"
