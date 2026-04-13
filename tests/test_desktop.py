"""Tests for the desktop CLI module."""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add desktop/ to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from desktop import (
    get_date_string,
    fetch_data,
    preview_receipt,
    RECEIPT_WIDTH,
)
from lib.api_client import MOCK_TODOS, MOCK_EVENTS


class TestGetDateString:
    def test_returns_formatted_date(self):
        with patch("desktop.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 13, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result = get_date_string()
            assert result == "Mon, Apr 13, 2026"

    def test_different_date(self):
        with patch("desktop.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 12, 25, 8, 0, 0)
            result = get_date_string()
            assert result == "Thu, Dec 25, 2025"


class TestFetchData:
    def test_returns_mock_data_when_no_server(self):
        todos, events = fetch_data(server_url=None)
        assert todos == MOCK_TODOS
        assert events == MOCK_EVENTS

    def test_returns_mock_data_on_server_failure(self):
        todos, events = fetch_data(server_url="http://localhost:99999")
        assert todos == MOCK_TODOS
        assert events == MOCK_EVENTS


class TestPreviewReceipt:
    def test_contains_header(self):
        result = preview_receipt("Today", [], [], "MY HEADER", "MY FOOTER")
        assert "MY HEADER" in result

    def test_contains_footer(self):
        result = preview_receipt("Today", [], [], "HEADER", "MY FOOTER")
        assert "MY FOOTER" in result

    def test_contains_date(self):
        result = preview_receipt("Mon, Apr 13, 2026", [], [], "H", "F")
        assert "Mon, Apr 13, 2026" in result

    def test_contains_todos(self):
        todos = [
            {"title": "Buy milk", "done": False, "priority": "high"},
            {"title": "Walk dog", "done": True, "priority": "low"},
        ]
        result = preview_receipt("Today", todos, [], "H", "F")
        assert "TO-DO LIST" in result
        assert "Buy milk" in result
        assert "Walk dog" in result
        assert "[ ]" in result
        assert "[x]" in result
        assert "!!" in result

    def test_contains_calendar(self):
        events = [
            {"time": "09:00", "title": "Meeting", "location": "Zoom"},
            {"time": "14:00", "title": "Lunch", "location": ""},
        ]
        result = preview_receipt("Today", [], events, "H", "F")
        assert "CALENDAR" in result
        assert "09:00" in result
        assert "Meeting" in result
        assert "@ Zoom" in result
        assert "Lunch" in result

    def test_empty_data(self):
        result = preview_receipt("Today", [], [], "H", "F")
        assert "H" in result
        assert "F" in result
        assert "TO-DO LIST" not in result
        assert "CALENDAR" not in result

    def test_full_receipt(self):
        todos = [{"title": "Task", "done": False}]
        events = [{"time": "10:00", "title": "Event"}]
        result = preview_receipt("Today", todos, events, "HEADER", "FOOTER")
        assert "HEADER" in result
        assert "FOOTER" in result
        assert "TO-DO LIST" in result
        assert "CALENDAR" in result
        assert "Task" in result
        assert "Event" in result


class TestDesktopCLI:
    def test_preview_flag_no_printer_needed(self):
        """--preview should work without a printer connection."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "desktop", "--preview"],
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
        )
        assert result.returncode == 0
        assert "LIST-A-DAY" in result.stdout
        assert "TO-DO LIST" in result.stdout
        assert "CALENDAR" in result.stdout

    def test_help_flag(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "desktop", "--help"],
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
        )
        assert result.returncode == 0
        assert "--ip" in result.stdout
        assert "--preview" in result.stdout
        assert "--test" in result.stdout


class TestFetchDataServer:
    """Test fetch_data with mocked server responses."""

    def test_fetch_from_server_success(self):
        from unittest.mock import patch, MagicMock
        import json

        mock_todos = [{"title": "Server Todo", "done": False}]
        mock_events = [{"time": "10:00", "title": "Server Event"}]

        def mock_urlopen(req, timeout=None):
            url = req.full_url if hasattr(req, 'full_url') else str(req)
            resp = MagicMock()
            if "/todos" in url:
                resp.read.return_value = json.dumps(mock_todos).encode()
            elif "/calendar" in url:
                resp.read.return_value = json.dumps(mock_events).encode()
            return resp

        with patch("urllib.request.urlopen", mock_urlopen):
            todos, events = fetch_data(server_url="http://localhost:8080")

        assert todos == mock_todos
        assert events == mock_events

    def test_fetch_from_server_partial_failure(self):
        """If server call raises, should fall back to mock data."""
        from unittest.mock import patch

        with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
            todos, events = fetch_data(server_url="http://localhost:8080")

        assert todos == MOCK_TODOS
        assert events == MOCK_EVENTS


class TestCmdPrint:
    """Test cmd_print with mocked printer."""

    def test_cmd_print_preview_mode(self, capsys):
        args = MagicMock()
        args.ip = "192.168.1.100"
        args.port = 9100
        args.server = None
        args.header = "TEST HEADER"
        args.footer = "TEST FOOTER"
        args.preview = True

        from desktop import cmd_print
        cmd_print(args)

        captured = capsys.readouterr()
        assert "TEST HEADER" in captured.out
        assert "TEST FOOTER" in captured.out
        assert "TO-DO LIST" in captured.out

    @patch("desktop.PrinterConnection")
    def test_cmd_print_sends_to_printer(self, mock_printer_cls):
        mock_printer = MagicMock()
        mock_printer.print_receipt.return_value = True
        mock_printer_cls.return_value = mock_printer

        args = MagicMock()
        args.ip = "192.168.1.100"
        args.port = 9100
        args.server = None
        args.header = "H"
        args.footer = "F"
        args.preview = False

        from desktop import cmd_print
        cmd_print(args)

        mock_printer.print_receipt.assert_called_once()
        sent_data = mock_printer.print_receipt.call_args[0][0]
        assert isinstance(sent_data, bytes)
        assert len(sent_data) > 0

    @patch("desktop.PrinterConnection")
    def test_cmd_print_failure_exits(self, mock_printer_cls):
        mock_printer = MagicMock()
        mock_printer.print_receipt.return_value = False
        mock_printer_cls.return_value = mock_printer

        args = MagicMock()
        args.ip = "192.168.1.100"
        args.port = 9100
        args.server = None
        args.header = "H"
        args.footer = "F"
        args.preview = False

        from desktop import cmd_print
        with pytest.raises(SystemExit) as exc_info:
            cmd_print(args)
        assert exc_info.value.code == 1


class TestCmdTest:
    """Test cmd_test with mocked printer."""

    @patch("desktop.PrinterConnection")
    def test_cmd_test_success(self, mock_printer_cls):
        mock_printer = MagicMock()
        mock_printer.test_connection.return_value = True
        mock_printer.print_receipt.return_value = True
        mock_printer_cls.return_value = mock_printer

        args = MagicMock()
        args.ip = "192.168.1.100"
        args.port = 9100

        from desktop import cmd_test
        cmd_test(args)

        mock_printer.test_connection.assert_called_once()
        mock_printer.print_receipt.assert_called_once()
        sent_data = mock_printer.print_receipt.call_args[0][0]
        assert b"LIST-A-DAY" in sent_data
        assert b"Desktop test print" in sent_data

    @patch("desktop.PrinterConnection")
    def test_cmd_test_unreachable_exits(self, mock_printer_cls):
        mock_printer = MagicMock()
        mock_printer.test_connection.return_value = False
        mock_printer_cls.return_value = mock_printer

        args = MagicMock()
        args.ip = "192.168.1.100"
        args.port = 9100

        from desktop import cmd_test
        with pytest.raises(SystemExit) as exc_info:
            cmd_test(args)
        assert exc_info.value.code == 1

    @patch("desktop.PrinterConnection")
    def test_cmd_test_send_failure_exits(self, mock_printer_cls):
        mock_printer = MagicMock()
        mock_printer.test_connection.return_value = True
        mock_printer.print_receipt.return_value = False
        mock_printer_cls.return_value = mock_printer

        args = MagicMock()
        args.ip = "192.168.1.100"
        args.port = 9100

        from desktop import cmd_test
        with pytest.raises(SystemExit) as exc_info:
            cmd_test(args)
        assert exc_info.value.code == 1


class TestDesktopCLIArgs:
    """Test CLI argument parsing via subprocess."""

    def test_custom_header_footer(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "desktop", "--preview",
             "--header", "CUSTOM HEADER", "--footer", "CUSTOM FOOTER"],
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
        )
        assert result.returncode == 0
        assert "CUSTOM HEADER" in result.stdout
        assert "CUSTOM FOOTER" in result.stdout

    def test_default_ip_env_var(self):
        import subprocess
        env = os.environ.copy()
        env["PRINTER_IP"] = "10.0.0.99"
        result = subprocess.run(
            [sys.executable, "-m", "desktop", "--preview"],
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
            env=env,
        )
        assert result.returncode == 0


class TestPreviewReceiptEdgeCases:
    def test_medium_priority_marker(self):
        todos = [{"title": "Medium task", "done": False, "priority": "medium"}]
        result = preview_receipt("Today", todos, [], "H", "F")
        assert "!  " in result

    def test_no_priority_no_marker(self):
        todos = [{"title": "Simple", "done": False, "priority": "low"}]
        result = preview_receipt("Today", todos, [], "H", "F")
        assert "[ ]" in result
        assert "Simple" in result

    def test_missing_event_fields(self):
        events = [{}]
        result = preview_receipt("Today", [], events, "H", "F")
        assert "Untitled" in result

    def test_missing_todo_fields(self):
        todos = [{}]
        result = preview_receipt("Today", todos, [], "H", "F")
        assert "Untitled" in result
