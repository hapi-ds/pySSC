"""JupyterLab manager for on-demand notebook server."""

import os
import subprocess
import time
from pathlib import Path
from typing import Optional

from nicegui import ui


class JupyterManager:
    """Manages JupyterLab process lifecycle."""

    def __init__(
        self,
        port: int = 8888,
        token: Optional[str] = None,
        notebook_dir: Optional[str] = None,
    ):
        """Initialize JupyterLab manager.

        Args:
            port: Port for JupyterLab server (default: 8888)
            token: Authentication token (generates random if None)
            notebook_dir: Directory for notebooks (default: ./notebooks)
        """
        self.port = port
        self.token = token or os.urandom(16).hex()
        self.notebook_dir = Path(notebook_dir or "notebooks").resolve()
        self.process: Optional[subprocess.Popen] = None
        self._ensure_notebook_dir()

    def _ensure_notebook_dir(self) -> None:
        """Create notebooks directory if it doesn't exist."""
        self.notebook_dir.mkdir(parents=True, exist_ok=True)

    def is_running(self) -> bool:
        """Check if JupyterLab process is running.

        Returns:
            True if process is running, False otherwise
        """
        return self.process is not None and self.process.poll() is None

    def start(self) -> bool:
        """Start JupyterLab server.

        Returns:
            True if started successfully, False if already running
        """
        if self.is_running():
            ui.notify("JupyterLab is already running", type="warning")
            return False

        try:
            # Check if running in Docker (more reliable detection)
            in_docker = (
                os.path.exists("/.dockerenv")
                or os.environ.get("DOCKER_CONTAINER", "false").lower() == "true"
            )

            cmd = [
                "jupyter",
                "lab",
                f"--port={self.port}",
                "--port-retries=0",  # Don't retry on port conflict
                f"--ServerApp.token={self.token}",
                "--no-browser",
                f"--notebook-dir={self.notebook_dir}",
                "--ServerApp.allow_origin='*'",
                "--ServerApp.disable_check_xsrf=True",
            ]

            # Add --allow-root only if in Docker
            if in_docker:
                cmd.append("--allow-root")
                # Bind to all interfaces for container port mapping to work
                # Use ServerApp.* instead of NotebookApp.* for JupyterLab 4.x
                cmd.append("--ServerApp.ip=0.0.0.0")

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait a bit for server to start
            time.sleep(2)

            if self.is_running():
                ui.notify("JupyterLab started successfully!", type="positive")
                return True
            else:
                # Get error output for debugging
                stdout, stderr = (
                    self.process.communicate() if self.process else ("", "")
                )
                error_msg = stderr.strip() or stdout.strip() or "Unknown error"
                ui.notify(f"Failed to start JupyterLab: {error_msg}", type="negative")
                return False

        except FileNotFoundError:
            ui.notify(
                "JupyterLab not installed. Run: uv add jupyterlab",
                type="negative",
            )
            return False
        except Exception as e:
            ui.notify(f"Error starting JupyterLab: {e}", type="negative")
            return False

    def stop(self) -> bool:
        """Stop JupyterLab server.

        Returns:
            True if stopped successfully, False if not running
        """
        if not self.is_running():
            ui.notify("JupyterLab is not running", type="warning")
            return False

        try:
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=5)
                self.process = None
                ui.notify("JupyterLab stopped", type="info")
                return True
        except subprocess.TimeoutExpired:
            if self.process:
                self.process.kill()
                self.process = None
            ui.notify("JupyterLab force stopped", type="warning")
            return True
        except Exception as e:
            ui.notify(f"Error stopping JupyterLab: {e}", type="negative")
            return False

        return False

    def get_url(self) -> str:
        """Get JupyterLab URL with token.

        On Windows Docker, use 127.0.0.1 instead of localhost since
        localhost resolves to the Windows host, not the container.

        Returns:
            Full URL to access JupyterLab
        """
        # Detect if running in Docker on Windows
        in_docker = (
            os.path.exists("/.dockerenv")
            or os.environ.get("DOCKER_CONTAINER", "false").lower() == "true"
        )
        is_windows = os.name == "nt"

        host = "127.0.0.1" if (in_docker and is_windows) else "localhost"
        return f"http://{host}:{self.port}/lab?token={self.token}"

    def get_status(self) -> str:
        """Get current status message.

        Returns:
            Status string
        """
        if self.is_running():
            return f"Running on port {self.port}"
        return "Not running"
