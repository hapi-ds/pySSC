"""Tests for validation runner module."""

import json

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
                "markers": [{"name": "urs", "args": ["31.2", "31.3"]}],
            }
        ]
    }

    results = runner._extract_test_results(pytest_data, "IQ")

    assert len(results) == 2
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
                "markers": [{"name": "urs", "args": ["31.2"]}],
            }
        ]
    }

    results = runner._extract_test_results(pytest_data, "OQ")

    assert len(results) == 1
    assert results[0]["result"] == "FAILED"
    assert results[0]["status"] == "FAILED"


def test_validation_runner_extract_no_urs_markers():
    """Test extraction when no URS markers are present."""
    runner = ValidationRunner()

    pytest_data = {
        "tests": [{"nodeid": "test_file.py::test_function", "outcome": "passed"}]
    }

    results = runner._extract_test_results(pytest_data, "PQ")

    assert len(results) == 1
    assert results[0]["urs_id"] == "N/A"
    assert results[0]["requirement"].startswith("PQ -")
    assert results[0]["result"] == "PASSED"


def test_validation_runner_extract_marker_as_object():
    """Test extraction when marker is an object with name and args."""
    runner = ValidationRunner()

    class MockMarker:
        def __init__(self, name, args):
            self.name = name
            self.args = args

    pytest_data = {
        "tests": [
            {
                "nodeid": "test_file.py::test_function",
                "outcome": "passed",
                "markers": [MockMarker("urs", ["42.1"])],
            }
        ]
    }

    results = runner._extract_test_results(pytest_data, "IQ")

    assert len(results) == 1
    assert results[0]["urs_id"] == "42.1"


def test_validation_runner_extract_dict_marker():
    """Test extraction when marker is a dict with name and args."""
    runner = ValidationRunner()

    pytest_data = {
        "tests": [
            {
                "nodeid": "test_file.py::test_function",
                "outcome": "passed",
                "markers": [{"name": "urs", "args": ["55.1"]}],
            }
        ]
    }

    results = runner._extract_test_results(pytest_data, "OQ")

    assert len(results) == 1
    assert results[0]["urs_id"] == "55.1"


def test_validation_runner_extract_multiple_markers():
    """Test extraction when multiple URS markers are present."""
    runner = ValidationRunner()

    class MockMarker:
        def __init__(self, name, args):
            self.name = name
            self.args = args

    pytest_data = {
        "tests": [
            {
                "nodeid": "test_file.py::test_function",
                "outcome": "passed",
                "markers": [MockMarker("urs", ["10.1"]), MockMarker("urs", ["10.2"])],
            }
        ]
    }

    results = runner._extract_test_results(pytest_data, "PQ")

    assert len(results) == 2
    assert results[0]["urs_id"] == "10.1"
    assert results[1]["urs_id"] == "10.2"


def test_validation_runner_extract_parametrized_test():
    """Test extraction of parametrized test results."""
    runner = ValidationRunner()

    pytest_data = {
        "tests": [
            {
                "nodeid": "test_file.py::test_function[param]",
                "outcome": "passed",
                "markers": [{"name": "urs", "args": ["20.1"]}],
            }
        ]
    }

    results = runner._extract_test_results(pytest_data, "IQ")

    assert len(results) == 1
    assert results[0]["requirement"].endswith("[param]")
    assert results[0]["test_id"] == "test_file.py::test_function[param]"
    assert results[0]["result"] == "PASSED"


def test_validation_runner_extract_unknown_outcome():
    """Test extraction when test outcome is unknown."""
    runner = ValidationRunner()

    pytest_data = {
        "tests": [{"nodeid": "test_file.py::test_function", "outcome": "unknown"}]
    }

    results = runner._extract_test_results(pytest_data, "OQ")

    assert len(results) == 1
    assert results[0]["result"] == "FAILED"


def test_validation_runner_extract_empty_pytest_data():
    """Test extraction with empty pytest data."""
    runner = ValidationRunner()

    pytest_data = {"tests": []}

    results = runner._extract_test_results(pytest_data, "PQ")

    assert len(results) == 0


def test_validation_runner_extract_multiple_tests():
    """Test extraction of multiple tests from pytest data."""
    runner = ValidationRunner()

    pytest_data = {
        "tests": [
            {
                "nodeid": "test_file.py::test_one",
                "outcome": "passed",
                "markers": [{"name": "urs", "args": ["1.1"]}],
            },
            {
                "nodeid": "test_file.py::test_two",
                "outcome": "failed",
                "markers": [{"name": "urs", "args": ["1.2"]}],
            },
            {"nodeid": "test_file.py::test_three", "outcome": "passed", "markers": []},
        ]
    }

    results = runner._extract_test_results(pytest_data, "IQ")

    assert len(results) == 3
    assert results[0]["urs_id"] == "1.1"
    assert results[0]["result"] == "PASSED"
    assert results[1]["urs_id"] == "1.2"
    assert results[1]["result"] == "FAILED"
    assert results[2]["urs_id"] == "N/A"
    assert results[2]["result"] == "PASSED"


def test_validation_runner_progress_callback_none():
    """Test that _report_progress handles None callback."""
    runner = ValidationRunner()
    runner._report_progress("This should not be recorded")


def test_validation_runner_test_results_accumulate():
    """Test that test results accumulate across multiple runs."""
    runner = ValidationRunner()

    iq_data = {"tests": [{"nodeid": "iq_test.py::test_one", "outcome": "passed"}]}
    oq_data = {"tests": [{"nodeid": "oq_test.py::test_two", "outcome": "failed"}]}

    iq_results = runner._extract_test_results(iq_data, "IQ")
    oq_results = runner._extract_test_results(oq_data, "OQ")

    runner.test_results.extend(iq_results)
    runner.test_results.extend(oq_results)

    assert len(runner.test_results) == 2
    assert runner.test_results[0]["test_id"] == "iq_test.py::test_one"
    assert runner.test_results[1]["test_id"] == "oq_test.py::test_two"




def test_validation_runner_progress_callback_multiple_messages():
    """Test callback receives multiple messages."""
    messages = []

    def callback(msg: str):
        messages.append(msg)

    runner = ValidationRunner(progress_callback=callback)
    runner._report_progress("First")
    runner._report_progress("Second")
    runner._report_progress("Third")

    assert len(messages) == 3
    assert messages[0] == "First"
    assert messages[1] == "Second"
    assert messages[2] == "Third"


def test_validation_runner_with_mocked_subprocess(tmp_path, mocker):
    """Test run_validation with mocked subprocess calls."""
    
    class MockResult:
        def __init__(self):
            self.returncode = 0
            self.stdout = ""
            self.stderr = ""

    json_path = tmp_path / "test_results_iq.json"
    json_path.write_text(
        json.dumps({
            "tests": [{
                "nodeid": "test_iq.py::test_1",
                "outcome": "passed",
                "markers": [{"name": "urs", "args": ["30.1"]}]
            }],
            "summary": {"passed": 1, "failed": 0, "total": 1},
            "exitcode": 0
        })
    )

    mock_result = MockResult()
    mock_result.returncode = 0

    mocker.patch("subprocess.run", return_value=mocker.Mock(return_value=mock_result))

    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch(
        "pathlib.Path.open",
        lambda self, *args, **kwargs: open(json_path, *args, **kwargs)
    )
    mocker.patch(
        "sample_size_calculator.validation_runner.HashVerifier.VALIDATED_HASH_FILE",
        tmp_path / "validated_hash.json"
    )

    pdf_mock_result = MockResult()
    pdf_mock_result.returncode = 0
    pdf_mock_result.stdout = "PASSED test_module_v_pdf_contains_confidence_reliability"
