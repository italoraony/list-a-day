"""Integration tests — full flow from data to receipt."""

import socket
import threading
import time
import pytest
from unittest.mock import patch, MagicMock

from lib.escpos import ESCPOSBuilder
from lib.printer import PrinterConnection
from lib.formatter import ReceiptFormatter
from lib.api_client import MOCK_TODOS, MOCK_EVENTS


class TestFullReceiptFlow:
    """Test complete flow: data → formatter → ESC/POS bytes."""

    def test_mock_data_produces_valid_receipt(self):
        formatter = ReceiptFormatter(width=48, header="LIST-A-DAY", footer="Goodbye!")
        data = formatter.build_daily_receipt("Mon, Apr 13, 2026", MOCK_TODOS, MOCK_EVENTS)

        assert isinstance(data, bytes)
        assert len(data) > 100
        assert data.startswith(b"\x1b\x40")  # ESC @ (init)
        assert data.endswith(b"\x1d\x56\x00")  # Full cut
        assert b"LIST-A-DAY" in data
        assert b"Goodbye!" in data
        assert b"Review pull requests" in data
        assert b"Team standup" in data
        assert b"09:00" in data

    def test_empty_data_produces_minimal_receipt(self):
        formatter = ReceiptFormatter()
        data = formatter.build_daily_receipt("Today", None, None)

        assert isinstance(data, bytes)
        assert data.startswith(b"\x1b\x40")
        assert data.endswith(b"\x1d\x56\x00")
        assert b"LIST-A-DAY" in data
        assert b"Have a great day!" in data

    def test_receipt_with_only_todos(self):
        formatter = ReceiptFormatter()
        todos = [{"title": "Only task", "done": False, "priority": "high"}]
        data = formatter.build_daily_receipt("Today", todos, None)

        assert b"TO-DO LIST" in data
        assert b"Only task" in data
        assert b"CALENDAR" not in data

    def test_receipt_with_only_events(self):
        formatter = ReceiptFormatter()
        events = [{"time": "12:00", "title": "Lunch", "location": "Cafe"}]
        data = formatter.build_daily_receipt("Today", None, events)

        assert b"CALENDAR" in data
        assert b"Lunch" in data
        assert b"TO-DO LIST" not in data


class TestESCPOSComplexReceipt:
    """Test building complex receipts with multiple formatting commands."""

    def test_styled_receipt(self):
        b = ESCPOSBuilder()
        result = (
            b.reset()
            .align("center")
            .size(2, 2)
            .bold(True)
            .text("BIG TITLE")
            .newline()
            .size(1, 1)
            .bold(False)
            .text("Subtitle")
            .newline()
            .separator("=", 48)
            .align("left")
            .font("A")
            .text("Normal text")
            .newline()
            .font("B")
            .text("Small text")
            .newline()
            .font("A")
            .bold(True)
            .underline(True)
            .text("Bold underline")
            .bold(False)
            .underline(False)
            .newline()
            .two_columns("Item", "$9.99", 48)
            .separator("-", 48)
            .align("center")
            .qr_code("https://github.com/italoraony/list-a-day")
            .newline()
            .cut()
        )

        data = result.build()
        assert isinstance(data, bytes)
        assert len(data) > 200
        assert b"BIG TITLE" in data
        assert b"Subtitle" in data
        assert b"Normal text" in data
        assert b"Small text" in data
        assert b"Bold underline" in data
        assert b"Item" in data
        assert b"$9.99" in data
        assert b"https://github.com/italoraony/list-a-day" in data

    def test_barcode_and_qr_in_same_receipt(self):
        b = ESCPOSBuilder()
        b.reset()
        b.text("Barcode:")
        b.newline()
        b.barcode("123456789", barcode_type=73)
        b.newline()
        b.text("QR Code:")
        b.newline()
        b.qr_code("test-data", size=4)
        b.cut()

        data = b.build()
        assert b"Barcode:" in data
        assert b"QR Code:" in data
        assert b"123456789" in data
        assert b"test-data" in data


class TestPrinterWithTCPServer:
    """Test PrinterConnection against a real TCP server (localhost)."""

    @staticmethod
    def _start_tcp_server(port, received_data):
        """Start a TCP server that captures received data."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", port))
        server.listen(1)
        server.settimeout(5)
        try:
            conn, _ = server.accept()
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                received_data.extend(chunk)
            conn.close()
        except socket.timeout:
            pass
        finally:
            server.close()

    def test_print_receipt_to_tcp_server(self):
        """Send a receipt to a real TCP server and verify data."""
        received = bytearray()
        port = 19100  # Use non-privileged port for testing

        server_thread = threading.Thread(
            target=self._start_tcp_server, args=(port, received)
        )
        server_thread.daemon = True
        server_thread.start()
        time.sleep(0.1)  # Let server start

        # Build a receipt
        formatter = ReceiptFormatter(header="TCP TEST")
        receipt = formatter.build_daily_receipt("Today", MOCK_TODOS, MOCK_EVENTS)

        # Send to our test server
        printer = PrinterConnection("127.0.0.1", port)
        result = printer.print_receipt(receipt)

        server_thread.join(timeout=3)

        assert result is True
        assert len(received) > 0
        assert received == receipt

    def test_connection_to_real_tcp_server(self):
        """Test test_connection against a real listening port."""
        port = 19101

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", port))
        server.listen(1)

        try:
            printer = PrinterConnection("127.0.0.1", port)
            assert printer.test_connection() is True
        finally:
            server.close()

    def test_connection_to_closed_port(self):
        """test_connection should return False for a closed port."""
        printer = PrinterConnection("127.0.0.1", 19199)
        assert printer.test_connection() is False

    def test_send_and_close_cycle(self):
        """Test multiple connect/send/close cycles."""
        received = bytearray()
        port = 19102

        # Server that accepts multiple connections
        def multi_server():
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("127.0.0.1", port))
            server.listen(2)
            server.settimeout(5)
            try:
                for _ in range(2):
                    conn, _ = server.accept()
                    while True:
                        chunk = conn.recv(4096)
                        if not chunk:
                            break
                        received.extend(chunk)
                    conn.close()
            except socket.timeout:
                pass
            finally:
                server.close()

        server_thread = threading.Thread(target=multi_server)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(0.1)

        printer = PrinterConnection("127.0.0.1", port)

        # First print
        b1 = ESCPOSBuilder()
        b1.reset().text("First").cut()
        assert printer.print_receipt(b1.build()) is True

        # Second print
        b2 = ESCPOSBuilder()
        b2.reset().text("Second").cut()
        assert printer.print_receipt(b2.build()) is True

        server_thread.join(timeout=3)

        assert b"First" in received
        assert b"Second" in received
