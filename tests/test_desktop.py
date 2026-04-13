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
