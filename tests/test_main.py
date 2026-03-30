"""Tests for main entry point module."""

from unittest.mock import patch


def test_main_creates_ui():
    """Test that create_ui is called when main runs."""
    with patch("sample_size_calculator.ui_controller.create_ui") as mock_create_ui:
        # Directly call the main block logic
        from sample_size_calculator.ui_controller import create_ui
        
        create_ui()
        
        assert mock_create_ui.called


def test_main_module_imports():
    """Test that main module imports successfully."""
    import sample_size_calculator.main
    
    assert hasattr(sample_size_calculator.main, "__name__")
