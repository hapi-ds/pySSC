"""Tests for error scenarios and edge cases.

This module tests:
1. Convergence failure paths in iterative calculations (RuntimeError when max_iterations reached)
2. Edge cases with invalid lambda parameters
3. Jupyter error scenarios during startup

**Validates: Requirements 4.5, 10.5, 23.1**
"""

import pytest

from sample_size_calculator.calculations import CalculationEngine


class TestConvergenceFailure:
    """Test convergence failure paths in iterative calculations.

    **Validates: Requirement 4.5**
    """

    def test_cumulative_binomial_convergence_failure(self):
        """Test RuntimeError when cumulative binomial does not converge.

        The method has a max_iterations limit of 150000.
        """
        # Use extreme parameters that will likely cause convergence failure
        # Very high reliability close to 100% with high confidence
        with pytest.raises(RuntimeError, match="did not converge"):
            CalculationEngine.cumulative_binomial(
                confidence=99.999,
                reliability=99.999,
                allowable_failures=1,
            )

    def test_cumulative_binomial_convergence_with_very_high_reliability(self):
        """Test convergence failure with extremely high reliability requirements."""
        with pytest.raises(RuntimeError, match="did not converge"):
            CalculationEngine.cumulative_binomial(
                confidence=99.9,
                reliability=99.9999,
                allowable_failures=2,
            )

    def test_non_parametric_two_sided_convergence_failure(self):
        """Test RuntimeError when non-parametric two-sided does not converge.

        The method has a max_iterations limit of 100000.
        """
        # Use extreme parameters that will likely cause convergence failure
        with pytest.raises(RuntimeError, match="did not converge"):
            CalculationEngine.non_parametric_two_sided_sample_size(
                confidence=99.999,
                reliability=99.999,
            )

    def test_non_parametric_convergence_with_extreme_confidence(self):
        """Test convergence failure with extreme confidence requirements."""
        with pytest.raises(RuntimeError, match="did not converge"):
            CalculationEngine.non_parametric_two_sided_sample_size(
                confidence=99.999,
                reliability=99.999,
            )

    def test_cumulative_binomial_converges_with_reasonable_parameters(self):
        """Verify cumulative binomial still converges with reasonable parameters.

        This ensures the convergence failure tests are actually testing the right thing.
        """
        # These should converge normally
        n = CalculationEngine.cumulative_binomial(
            confidence=95.0,
            reliability=90.0,
            allowable_failures=1,
        )
        assert isinstance(n, int)
        assert n > 0

    def test_non_parametric_converges_with_reasonable_parameters(self):
        """Verify non-parametric still converges with reasonable parameters."""
        n = CalculationEngine.non_parametric_two_sided_sample_size(
            confidence=95.0,
            reliability=90.0,
        )
        assert isinstance(n, int)
        assert n > 0


class TestInvalidLambdaParameters:
    """Test edge cases with invalid lambda parameters.

    **Validates: Requirement 10.5**
    """

    def test_box_cox_with_negative_values_returns_none(self):
        """Box-Cox should return None for data with negative values."""
        from sample_size_calculator.transformations import box_cox_transform

        data = [-1.0, 2.0, 3.0, 4.0, 5.0]

        result = box_cox_transform(data)

        assert result is None

    def test_box_cox_with_zero_value_returns_none(self):
        """Box-Cox should return None for data with zero values."""
        from sample_size_calculator.transformations import box_cox_transform

        data = [0.0, 2.0, 3.0, 4.0, 5.0]

        result = box_cox_transform(data)

        assert result is None

    def test_box_cox_with_constant_data_returns_none(self):
        """Box-Cox should return None for constant data (no variance)."""
        from sample_size_calculator.transformations import box_cox_transform

        data = [5.0] * 10

        result = box_cox_transform(data)

        assert result is None

    def test_box_cox_with_very_small_variance(self):
        """Box-Cox should handle very small variance gracefully."""

        from sample_size_calculator.transformations import box_cox_transform

        base = 100.0
        data = [base + 1e-12 * i for i in range(10)]

        result = box_cox_transform(data)

        assert result is None or (isinstance(result, tuple) and len(result) == 2)

    def test_box_cox_with_valid_data_returns_tuple(self):
        """Box-Cox with valid positive data should return (data, lambda)."""
        from sample_size_calculator.transformations import box_cox_transform

        data = [1.0, 2.0, 3.0, 4.0, 5.0]

        result = box_cox_transform(data)

        assert isinstance(result, tuple)
        transformed_data, lambda_param = result
        assert len(transformed_data) == len(data)
        assert isinstance(lambda_param, float)

    def test_inverse_box_cox_with_extreme_lambda(self):
        """Test inverse Box-Cox with extreme lambda values."""
        from sample_size_calculator.transformations import inverse_box_cox_transform

        transformed_data = [1.0, 2.0, 3.0]
        lambda_param = 100.0

        result = inverse_box_cox_transform(transformed_data, lambda_param)

        assert isinstance(result, list)
        assert len(result) == len(transformed_data)

    def test_inverse_box_cox_with_zero_lambda(self):
        """Test inverse Box-Cox with lambda=0 (logarithmic case)."""
        import numpy as np

        from sample_size_calculator.transformations import inverse_box_cox_transform

        transformed_data = [0.0, 1.0, 2.0]
        lambda_param = 0.0

        result = inverse_box_cox_transform(transformed_data, lambda_param)

        expected = [np.exp(0.0), np.exp(1.0), np.exp(2.0)]
        assert np.allclose(result, expected, rtol=1e-5)

    def test_yeo_johnson_with_negative_values_succeeds(self):
        """Yeo-Johnson should work with negative values (unlike Box-Cox)."""
        from sample_size_calculator.transformations import yeo_johnson_transform

        data = [-5.0, -2.0, 0.0, 3.0, 7.0]

        result = yeo_johnson_transform(data)

        assert isinstance(result, tuple)
        transformed_data, lambda_param = result
        assert len(transformed_data) == len(data)
        assert isinstance(lambda_param, float)

    def test_yeo_johnson_with_zero_values_succeeds(self):
        """Yeo-Johnson should work with zero values."""
        from sample_size_calculator.transformations import yeo_johnson_transform

        data = [0.0, 0.0, 0.0]

        result = yeo_johnson_transform(data)

        transformed_data, lambda_param = result
        assert all(x == 0.0 for x in transformed_data)

    def test_inverse_yeo_johnson_with_extreme_lambda(self):
        """Test inverse Yeo-Johnson with extreme lambda values."""
        from sample_size_calculator.transformations import inverse_yeo_johnson_transform

        transformed_data = [1.0, -1.0, 2.0]
        lambda_param = 50.0

        result = inverse_yeo_johnson_transform(transformed_data, lambda_param)

        assert isinstance(result, list)
        assert len(result) == len(transformed_data)

    def test_inverse_yeo_johnson_with_lambda_two(self):
        """Test inverse Yeo-Johnson with lambda=2 (special case)."""
        import numpy as np

        from sample_size_calculator.transformations import inverse_yeo_johnson_transform

        transformed_data = [-1.0, -2.0]
        lambda_param = 2.0

        result = inverse_yeo_johnson_transform(transformed_data, lambda_param)

        expected = [1 - np.exp(1.0), 1 - np.exp(2.0)]
        assert np.allclose(result, expected, rtol=1e-5)


class TestJupyterStartupErrorScenarios:
    """Test Jupyter error scenarios during startup.

    **Validates: Requirement 23.1**
    """

    def test_start_returns_false_when_already_running(self):
        """Test that start returns False when already running."""
        from unittest.mock import Mock

        from sample_size_calculator.jupyter_manager import JupyterManager

        manager = JupyterManager()
        mock_process = Mock()
        mock_process.poll.return_value = None
        manager.process = mock_process

        result = manager.start()

        assert result is False
        assert manager.is_running() is True

    def test_start_returns_false_on_subprocess_error(self):
        """Test that start returns False on subprocess startup error."""
        from unittest.mock import patch

        from sample_size_calculator.jupyter_manager import JupyterManager

        manager = JupyterManager()

        with patch("subprocess.Popen", side_effect=OSError("Subprocess failed")):
            result = manager.start()

        assert result is False

    def test_start_returns_false_on_exception(self):
        """Test that start returns False on any exception during startup."""
        from unittest.mock import patch

        from sample_size_calculator.jupyter_manager import JupyterManager

        manager = JupyterManager()

        with patch("subprocess.Popen", side_effect=Exception("Memory error")):
            result = manager.start()

        assert result is False

    def test_stop_returns_false_when_not_running(self):
        """Test that stop returns False when not running."""
        from sample_size_calculator.jupyter_manager import JupyterManager

        manager = JupyterManager()

        result = manager.stop()

        assert result is False

    def test_stop_returns_true_on_successful_stop(self):
        """Test that stop returns True on successful process termination."""
        from unittest.mock import Mock

        from sample_size_calculator.jupyter_manager import JupyterManager

        manager = JupyterManager()
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.wait.return_value = None
        manager.process = mock_process

        result = manager.stop()

        assert result is True
        assert manager.process is None

    def test_stop_force_stops_on_timeout(self):
        """Test that stop force-stops process on timeout."""
        import subprocess as sp
        from unittest.mock import Mock

        from sample_size_calculator.jupyter_manager import JupyterManager

        manager = JupyterManager()
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.wait.side_effect = sp.TimeoutExpired(cmd=["test"], timeout=5)
        manager.process = mock_process

        result = manager.stop()

        assert result is True
        mock_process.kill.assert_called_once()

    def test_stop_returns_false_on_exception(self):
        """Test that stop returns False on exception during stopping."""
        from unittest.mock import Mock

        from sample_size_calculator.jupyter_manager import JupyterManager

        manager = JupyterManager()
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.terminate.side_effect = Exception("Terminate failed")
        manager.process = mock_process

        result = manager.stop()

        assert result is False

    def test_get_status_when_running(self):
        """Test get_status returns running status."""
        from unittest.mock import Mock

        from sample_size_calculator.jupyter_manager import JupyterManager

        manager = JupyterManager(port=8000)
        mock_process = Mock()
        mock_process.poll.return_value = None
        manager.process = mock_process

        status = manager.get_status()

        assert "Running" in status
        assert "8000" in status

    def test_get_status_when_not_running(self):
        """Test get_status returns 'Not running' when not running."""
        from sample_size_calculator.jupyter_manager import JupyterManager

        manager = JupyterManager(port=8000)

        status = manager.get_status()

        assert status == "Not running"

    def test_get_url_with_custom_port_and_token(self):
        """Test get_url generates correct URL with custom parameters."""
        from sample_size_calculator.jupyter_manager import JupyterManager

        manager = JupyterManager(port=9000, token="my-secret-token")

        url = manager.get_url()

        assert "localhost" in url
        assert "9000" in url
        assert "my-secret-token" in url
        assert "?token=" in url

    def test_is_running_with_none_process(self):
        """Test is_running returns False when process is None."""
        from sample_size_calculator.jupyter_manager import JupyterManager

        manager = JupyterManager()
        manager.process = None

        assert manager.is_running() is False

    def test_is_running_with_terminated_process(self):
        """Test is_running returns False when process has terminated."""
        from unittest.mock import Mock

        from sample_size_calculator.jupyter_manager import JupyterManager

        manager = JupyterManager()
        mock_process = Mock()
        mock_process.poll.return_value = 0
        manager.process = mock_process

        assert manager.is_running() is False

    def test_is_running_with_active_process(self):
        """Test is_running returns True when process is active."""
        from unittest.mock import Mock

        from sample_size_calculator.jupyter_manager import JupyterManager

        manager = JupyterManager()
        mock_process = Mock()
        mock_process.poll.return_value = None
        manager.process = mock_process

        assert manager.is_running() is True
