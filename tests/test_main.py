"""Tests for main module functions."""

import sys
import types
import pytest
from unittest.mock import MagicMock, patch


def _import_main_module():
    """Import main.py while preventing the main() call at module level."""
    import importlib
    
    # Ensure config module is available
    if "config" not in sys.modules:
        import config  # noqa: This will load from client/ via sys.path in conftest
    
    # Read the source, remove the main() call at the bottom
    import os
    main_path = os.path.join(os.path.dirname(__file__), "..", "client", "main.py")
    main_path = os.path.abspath(main_path)
    
    with open(main_path, "r") as f:
        source = f.read()
    
    # Remove the bare main() call at module level
    source = source.replace("\nmain()\n", "\n# main() call removed for testing\n")
    source = source.replace("\nmain()", "\n# main() call removed for testing")
    
    # Create module
    mod = types.ModuleType("client_main")
    mod.__file__ = main_path
    exec(compile(source, main_path, "exec"), mod.__dict__)
    return mod


class TestGetDateString:
    def test_returns_formatted_date(self):
        mod = _import_main_module()
        with patch.object(mod.time, "localtime") as mock_lt:
            # time.localtime returns (year, month, day, hour, min, sec, weekday, yearday)
            # weekday: 0=Mon, 6=Sun
            mock_lt.return_value = (2025, 4, 7, 10, 30, 0, 0, 97)
            result = mod.get_date_string()
            assert result == "Mon, Apr 07, 2025"

    def test_different_date(self):
        mod = _import_main_module()
        with patch.object(mod.time, "localtime") as mock_lt:
            # Friday, December 25, 2025
            mock_lt.return_value = (2025, 12, 25, 8, 0, 0, 4, 359)
            result = mod.get_date_string()
            assert result == "Fri, Dec 25, 2025"

    def test_saturday(self):
        mod = _import_main_module()
        with patch.object(mod.time, "localtime") as mock_lt:
            # Saturday, January 1, 2026
            mock_lt.return_value = (2026, 1, 1, 0, 0, 0, 5, 1)
            result = mod.get_date_string()
            assert result == "Sat, Jan 01, 2026"

    def test_fallback_on_exception(self):
        mod = _import_main_module()
        with patch.object(mod.time, "localtime", side_effect=Exception("RTC not set")):
            result = mod.get_date_string()
            assert result == "Today"


class TestPrintDailyList:
    def test_success(self):
        mod = _import_main_module()
        
        mock_printer = MagicMock()
        mock_printer.print_receipt.return_value = True
        
        mock_api = MagicMock()
        mock_api.get_todos.return_value = [{"title": "Test", "done": False}]
        mock_api.get_calendar.return_value = [{"time": "09:00", "title": "Meeting"}]
        
        mock_formatter = MagicMock()
        mock_formatter.build_daily_receipt.return_value = b"\x1b\x40test"
        
        result = mod.print_daily_list(mock_printer, mock_api, mock_formatter)
        
        assert result is True
        mock_api.get_todos.assert_called_once()
        mock_api.get_calendar.assert_called_once()
        mock_formatter.build_daily_receipt.assert_called_once()
        mock_printer.print_receipt.assert_called_once_with(b"\x1b\x40test")

    def test_print_failure(self):
        mod = _import_main_module()
        
        mock_printer = MagicMock()
        mock_printer.print_receipt.return_value = False
        
        mock_api = MagicMock()
        mock_api.get_todos.return_value = []
        mock_api.get_calendar.return_value = []
        
        mock_formatter = MagicMock()
        mock_formatter.build_daily_receipt.return_value = b"data"
        
        result = mod.print_daily_list(mock_printer, mock_api, mock_formatter)
        
        assert result is False

    def test_with_none_data(self):
        mod = _import_main_module()
        
        mock_printer = MagicMock()
        mock_printer.print_receipt.return_value = True
        
        mock_api = MagicMock()
        mock_api.get_todos.return_value = None
        mock_api.get_calendar.return_value = None
        
        mock_formatter = MagicMock()
        mock_formatter.build_daily_receipt.return_value = b"data"
        
        result = mod.print_daily_list(mock_printer, mock_api, mock_formatter)
        
        assert result is True


class TestTestPrint:
    def test_test_print_success(self):
        mod = _import_main_module()
        
        mock_printer = MagicMock()
        mock_printer.print_receipt.return_value = True
        
        result = mod.test_print(mock_printer)
        
        assert result is True
        mock_printer.print_receipt.assert_called_once()
        # Verify it sent bytes
        sent_data = mock_printer.print_receipt.call_args[0][0]
        assert isinstance(sent_data, bytes)
        assert len(sent_data) > 0

    def test_test_print_failure(self):
        mod = _import_main_module()
        
        mock_printer = MagicMock()
        mock_printer.print_receipt.return_value = False
        
        result = mod.test_print(mock_printer)
        
        assert result is False

    def test_test_print_contains_list_a_day(self):
        mod = _import_main_module()
        
        mock_printer = MagicMock()
        mock_printer.print_receipt.return_value = True
        
        mod.test_print(mock_printer)
        
        sent_data = mock_printer.print_receipt.call_args[0][0]
        assert b"LIST-A-DAY" in sent_data

    def test_test_print_contains_test_message(self):
        mod = _import_main_module()
        
        mock_printer = MagicMock()
        mock_printer.print_receipt.return_value = True
        
        mod.test_print(mock_printer)
        
        sent_data = mock_printer.print_receipt.call_args[0][0]
        assert b"Test print successful!" in sent_data
