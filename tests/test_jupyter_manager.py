"""Tests for Jupyter manager module."""

import os
from unittest.mock import Mock, patch

from sample_size_calculator.jupyter_manager import JupyterManager


class TestJupyterManagerInitialization:
    """Test JupyterManager initialization."""

    def test_initialization_with_defaults(self):
        """Test initialization with default parameters."""
        manager = JupyterManager()
        
        assert manager.port == 8888
        assert manager.token is not None
        assert len(manager.token) == 32
        assert "notebooks" in str(manager.notebook_dir)

    def test_initialization_with_custom_port(self):
        """Test initialization with custom port."""
        manager = JupyterManager(port=9000)
        
        assert manager.port == 9000

    def test_initialization_with_custom_token(self):
        """Test initialization with custom token."""
        manager = JupyterManager(token="custom-token-123")
        
        assert manager.token == "custom-token-123"

    def test_initialization_with_custom_notebook_dir(self):
        """Test initialization with custom notebook directory."""
        manager = JupyterManager(notebook_dir="/tmp/custom_notebooks")
        
        assert "/tmp/custom_notebooks" in str(manager.notebook_dir)

    def test_process_starts_as_none(self):
        """Test that process is None initially."""
        manager = JupyterManager()
        
        assert manager.process is None


class TestJupyterManagerIsRunning:
    """Test is_running method."""

    def test_not_running_when_process_is_none(self):
        """Test not running when process is None."""
        manager = JupyterManager()
        
        assert manager.is_running() is False

    def test_not_running_when_process_terminated(self):
        """Test not running when process has been terminated."""
        manager = JupyterManager()
        mock_process = Mock()
        mock_process.poll.return_value = 0
        manager.process = mock_process
        
        assert manager.is_running() is False


class TestJupyterManagerStart:
    """Test start method."""

    def test_start_returns_false_when_already_running(self):
        """Test start returns False when already running."""
        manager = JupyterManager()
        mock_process = Mock()
        mock_process.poll.return_value = None
        manager.process = mock_process
        
        result = manager.start()
        
        assert result is False

    @patch("subprocess.Popen")
    def test_start_returns_true_when_successfully_started(self, mock_popen):
        """Test start returns True when successfully started."""
        manager = JupyterManager()
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        
        with patch("time.sleep"):
            result = manager.start()
        
        assert result is True

    @patch("subprocess.Popen")
    def test_start_returns_false_when_failed_to_start(self, mock_popen):
        """Test start returns False when failed to start."""
        manager = JupyterManager()
        mock_process = Mock()
        mock_process.poll.return_value = 1
        mock_process.communicate.return_value = ("", "Error message")
        mock_popen.return_value = mock_process
        
        with patch("time.sleep"):
            result = manager.start()
        
        assert result is False

    def test_start_returns_false_when_jupyter_not_found(self):
        """Test start returns False when Jupyter not installed."""
        manager = JupyterManager()
        
        with patch("subprocess.Popen", side_effect=FileNotFoundError):
            result = manager.start()
        
        assert result is False

    def test_start_returns_false_on_exception(self):
        """Test start returns False on exception."""
        manager = JupyterManager()
        
        with patch("subprocess.Popen", side_effect=Exception("Test error")):
            result = manager.start()
        
        assert result is False


class TestJupyterManagerStop:
    """Test stop method."""

    def test_stop_returns_false_when_not_running(self):
        """Test stop returns False when not running."""
        manager = JupyterManager()
        
        result = manager.stop()
        
        assert result is False

    @patch("subprocess.Popen")
    def test_stop_returns_true_when_successfully_stopped(self, mock_popen):
        """Test stop returns True when successfully stopped."""
        manager = JupyterManager()
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.terminate.side_effect = None
        manager.process = mock_process
        
        result = manager.stop()
        
        assert result is True

    @patch("subprocess.Popen")
    def test_stop_force_stops_on_timeout(self, mock_popen):
        """Test stop force stops process on timeout."""
        import subprocess as sp
        
        manager = JupyterManager()
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.wait.side_effect = sp.TimeoutExpired(cmd=["test"], timeout=5)
        manager.process = mock_process
        
        result = manager.stop()
        
        assert result is True

    @patch("subprocess.Popen")
    def test_stop_returns_false_on_exception(self, mock_popen):
        """Test stop returns False on exception."""
        manager = JupyterManager()
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.terminate.side_effect = Exception("Test error")
        manager.process = mock_process
        
        result = manager.stop()
        
        assert result is False

    def test_stop_returns_false_when_process_none(self):
        """Test stop returns False when process is None."""
        manager = JupyterManager()
        manager.process = None
        
        result = manager.stop()
        
        assert result is False


class TestJupyterManagerGetUrl:
    """Test get_url method."""

    @patch.dict(os.environ, {"DOCKER_CONTAINER": "false"}, clear=True)
    def test_get_url_on_linux(self):
        """Test URL generation on Linux."""
        manager = JupyterManager(port=8888, token="test-token")
        
        url = manager.get_url()
        
        assert "localhost" in url
        assert "8888" in url
        assert "test-token" in url

    def test_get_url_on_linux_normal(self):
        """Test URL generation on Linux uses localhost."""
        with patch("os.environ", {}), patch("os.name", "posix"):
            manager = JupyterManager(port=8000, token="abc123")
            
            url = manager.get_url()
            
            assert "localhost" in url
            assert "8000" in url
            assert "abc123" in url


class TestJupyterManagerGetStatus:
    """Test get_status method."""

    def test_get_status_when_running(self):
        """Test status when running."""
        manager = JupyterManager(port=8888)
        mock_process = Mock()
        mock_process.poll.return_value = None
        manager.process = mock_process
        
        status = manager.get_status()
        
        assert "Running" in status
        assert "8888" in status

    def test_get_status_when_not_running(self):
        """Test status when not running."""
        manager = JupyterManager()
        
        status = manager.get_status()
        
        assert status == "Not running"
