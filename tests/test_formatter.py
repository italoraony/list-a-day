"""Tests for receipt formatter."""

import pytest
from lib.formatter import ReceiptFormatter
from lib.escpos import ESCPOSBuilder


class TestReceiptFormatterInit:
    def test_default_values(self):
        f = ReceiptFormatter()
        assert f.width == 48
        assert f.header == "LIST-A-DAY"
        assert f.footer == "Have a great day!"

    def test_custom_values(self):
        f = ReceiptFormatter(width=32, header="MY LIST", footer="Bye!")
        assert f.width == 32
        assert f.header == "MY LIST"
        assert f.footer == "Bye!"


class TestReceiptFormatterHeader:
    def test_header_with_date(self):
        f = ReceiptFormatter()
        b = ESCPOSBuilder()
        b.reset()
        result = f.format_header(b, "Mon, Apr 07, 2025")
        assert result is b
        data = b.build()
        assert b"LIST-A-DAY" in data
        assert b"Mon, Apr 07, 2025" in data

    def test_header_without_date(self):
        f = ReceiptFormatter()
        b = ESCPOSBuilder()
        b.reset()
        f.format_header(b, None)
        data = b.build()
        assert b"LIST-A-DAY" in data

    def test_custom_header_text(self):
        f = ReceiptFormatter(header="DAILY TASKS")
        b = ESCPOSBuilder()
        b.reset()
        f.format_header(b, "Today")
        data = b.build()
        assert b"DAILY TASKS" in data


class TestReceiptFormatterFooter:
    def test_footer_content(self):
        f = ReceiptFormatter()
        b = ESCPOSBuilder()
        f.format_footer(b)
        data = b.build()
        assert b"Have a great day!" in data

    def test_custom_footer(self):
        f = ReceiptFormatter(footer="See you tomorrow!")
        b = ESCPOSBuilder()
        f.format_footer(b)
        data = b.build()
        assert b"See you tomorrow!" in data


class TestReceiptFormatterTodoList:
    def test_todo_list_with_items(self):
        f = ReceiptFormatter()
        b = ESCPOSBuilder()
        todos = [
            {"title": "Task 1", "done": False, "priority": "high"},
            {"title": "Task 2", "done": True, "priority": "low"},
            {"title": "Task 3", "done": False, "priority": "medium"},
        ]
        f.format_todo_list(b, todos)
        data = b.build()
        assert b"TO-DO LIST" in data
        assert b"Task 1" in data
        assert b"Task 2" in data
        assert b"Task 3" in data

    def test_todo_checkboxes(self):
        f = ReceiptFormatter()
        b = ESCPOSBuilder()
        todos = [
            {"title": "Done item", "done": True},
            {"title": "Open item", "done": False},
        ]
        f.format_todo_list(b, todos)
        data = b.build()
        assert b"[x]" in data
        assert b"[ ]" in data

    def test_todo_priority_markers(self):
        f = ReceiptFormatter()
        b = ESCPOSBuilder()
        todos = [
            {"title": "Urgent", "done": False, "priority": "high"},
            {"title": "Normal", "done": False, "priority": "medium"},
            {"title": "Low", "done": False, "priority": "low"},
        ]
        f.format_todo_list(b, todos)
        data = b.build()
        assert b"!!" in data  # high priority
        assert b"!  " in data  # medium priority (single ! with spacing)

    def test_todo_truncation(self):
        f = ReceiptFormatter(width=20)
        b = ESCPOSBuilder()
        todos = [
            {"title": "A" * 50, "done": False},
        ]
        f.format_todo_list(b, todos)
        data = b.build()
        assert b"..." in data

    def test_todo_empty_list(self):
        f = ReceiptFormatter()
        b = ESCPOSBuilder()
        f.format_todo_list(b, [])
        data = b.build()
        assert b"TO-DO LIST" in data

    def test_todo_missing_fields_use_defaults(self):
        f = ReceiptFormatter()
        b = ESCPOSBuilder()
        todos = [{"title": "Simple task"}]
        f.format_todo_list(b, todos)
        data = b.build()
        assert b"Simple task" in data
        assert b"[ ]" in data

    def test_todo_untitled(self):
        f = ReceiptFormatter()
        b = ESCPOSBuilder()
        todos = [{}]
        f.format_todo_list(b, todos)
        data = b.build()
        assert b"Untitled" in data


class TestReceiptFormatterCalendar:
    def test_calendar_with_events(self):
        f = ReceiptFormatter()
        b = ESCPOSBuilder()
        events = [
            {"time": "09:00", "title": "Meeting", "location": "Room A"},
            {"time": "14:00", "title": "Lunch", "location": ""},
        ]
        f.format_calendar(b, events)
        data = b.build()
        assert b"CALENDAR" in data
        assert b"09:00" in data
        assert b"Meeting" in data
        assert b"Room A" in data
        assert b"14:00" in data
        assert b"Lunch" in data

    def test_calendar_with_location(self):
        f = ReceiptFormatter()
        b = ESCPOSBuilder()
        events = [{"time": "10:00", "title": "Standup", "location": "Zoom"}]
        f.format_calendar(b, events)
        data = b.build()
        assert b"@ Zoom" in data

    def test_calendar_without_location(self):
        f = ReceiptFormatter()
        b = ESCPOSBuilder()
        events = [{"time": "10:00", "title": "Break", "location": ""}]
        f.format_calendar(b, events)
        data = b.build()
        assert b"@" not in data

    def test_calendar_empty_events(self):
        f = ReceiptFormatter()
        b = ESCPOSBuilder()
        f.format_calendar(b, [])
        data = b.build()
        assert b"CALENDAR" in data

    def test_calendar_missing_fields(self):
        f = ReceiptFormatter()
        b = ESCPOSBuilder()
        events = [{}]
        f.format_calendar(b, events)
        data = b.build()
        assert b"Untitled" in data


class TestReceiptFormatterBuildDailyReceipt:
    def test_full_receipt(self):
        f = ReceiptFormatter()
        todos = [{"title": "Task 1", "done": False}]
        events = [{"time": "09:00", "title": "Meeting"}]
        data = f.build_daily_receipt("Mon, Apr 07, 2025", todos, events)
        assert isinstance(data, bytes)
        assert len(data) > 0
        assert b"LIST-A-DAY" in data
        assert b"Task 1" in data
        assert b"Meeting" in data
        assert b"Have a great day!" in data
        # Should end with cut command
        assert data.endswith(b"\x1d\x56\x00")

    def test_receipt_without_todos(self):
        f = ReceiptFormatter()
        events = [{"time": "09:00", "title": "Meeting"}]
        data = f.build_daily_receipt("Today", None, events)
        assert b"Meeting" in data
        assert b"TO-DO LIST" not in data

    def test_receipt_without_events(self):
        f = ReceiptFormatter()
        todos = [{"title": "Task", "done": False}]
        data = f.build_daily_receipt("Today", todos, None)
        assert b"Task" in data
        assert b"CALENDAR" not in data

    def test_receipt_header_and_footer_only(self):
        f = ReceiptFormatter()
        data = f.build_daily_receipt("Today", None, None)
        assert b"LIST-A-DAY" in data
        assert b"Have a great day!" in data

    def test_receipt_starts_with_init(self):
        f = ReceiptFormatter()
        data = f.build_daily_receipt("Today")
        assert data.startswith(b"\x1b\x40")
