"""Tests for TCP socket printer driver."""

import pytest
from unittest.mock import patch, MagicMock, call
from lib.printer import PrinterConnection


class TestPrinterConnectionInit:
    def test_default_values(self):
        p = PrinterConnection("192.168.1.100")
        assert p.ip == "192.168.1.100"
        assert p.port == 9100
        assert p.timeout == 5
        assert p._sock is None

    def test_custom_values(self):
        p = PrinterConnection("10.0.0.1", port=8080, timeout=10)
        assert p.ip == "10.0.0.1"
        assert p.port == 8080
        assert p.timeout == 10

    def test_not_connected_initially(self):
        p = PrinterConnection("192.168.1.100")
        assert not p.is_connected()


class TestPrinterConnectionConnect:
    @patch("lib.printer.socket.socket")
    def test_connect_success(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock

        p = PrinterConnection("192.168.1.100", port=9100)
        result = p.connect()

        assert result is True
        assert p.is_connected()
        mock_sock.settimeout.assert_called_once_with(5)
        mock_sock.connect.assert_called_once_with(("192.168.1.100", 9100))

    @patch("lib.printer.socket.socket")
    def test_connect_failure(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = OSError("Connection refused")
        mock_socket_cls.return_value = mock_sock

        p = PrinterConnection("192.168.1.100")
        result = p.connect()

        assert result is False
        assert not p.is_connected()

    @patch("lib.printer.socket.socket")
    def test_connect_closes_existing_socket(self, mock_socket_cls):
        mock_sock1 = MagicMock()
        mock_sock2 = MagicMock()
        mock_socket_cls.side_effect = [mock_sock1, mock_sock2]

        p = PrinterConnection("192.168.1.100")
        p.connect()
        p.connect()

        mock_sock1.close.assert_called_once()


class TestPrinterConnectionClose:
    @patch("lib.printer.socket.socket")
    def test_close_connected(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock

        p = PrinterConnection("192.168.1.100")
        p.connect()
        p.close()

        mock_sock.close.assert_called()
        assert not p.is_connected()

    def test_close_not_connected(self):
        p = PrinterConnection("192.168.1.100")
        p.close()  # Should not raise
        assert not p.is_connected()

    @patch("lib.printer.socket.socket")
    def test_close_handles_oserror(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_sock.close.side_effect = OSError("close failed")
        mock_socket_cls.return_value = mock_sock

        p = PrinterConnection("192.168.1.100")
        p.connect()
        p.close()  # Should not raise
        assert not p.is_connected()


class TestPrinterConnectionSend:
    @patch("lib.printer.socket.socket")
    def test_send_bytes(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock

        p = PrinterConnection("192.168.1.100")
        p.connect()
        result = p.send(b"\x1b\x40Hello")

        assert result is True
        mock_sock.sendall.assert_called_once_with(b"\x1b\x40Hello")

    @patch("lib.printer.socket.socket")
    def test_send_string(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock

        p = PrinterConnection("192.168.1.100")
        p.connect()
        result = p.send("Hello")

        assert result is True
        mock_sock.sendall.assert_called_once_with(b"Hello")

    @patch("lib.printer.socket.socket")
    def test_send_bytearray(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock

        p = PrinterConnection("192.168.1.100")
        p.connect()
        result = p.send(bytearray(b"\x1b\x40"))

        assert result is True
        mock_sock.sendall.assert_called_once_with(bytearray(b"\x1b\x40"))

    @patch("lib.printer.socket.socket")
    def test_send_auto_connects_when_not_connected(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock

        p = PrinterConnection("192.168.1.100")
        result = p.send(b"data")

        assert result is True
        mock_sock.connect.assert_called_once()
        mock_sock.sendall.assert_called_once_with(b"data")

    @patch("lib.printer.socket.socket")
    def test_send_failure_closes_socket(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_sock.sendall.side_effect = OSError("Broken pipe")
        mock_socket_cls.return_value = mock_sock

        p = PrinterConnection("192.168.1.100")
        p.connect()
        result = p.send(b"data")

        assert result is False
        assert not p.is_connected()

    @patch("lib.printer.socket.socket")
    def test_send_when_connect_fails(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = OSError("Connection refused")
        mock_socket_cls.return_value = mock_sock

        p = PrinterConnection("192.168.1.100")
        result = p.send(b"data")

        assert result is False


class TestPrinterConnectionPrintReceipt:
    @patch("lib.printer.time.sleep")
    @patch("lib.printer.socket.socket")
    def test_print_receipt_success(self, mock_socket_cls, mock_sleep):
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock

        p = PrinterConnection("192.168.1.100")
        result = p.print_receipt(b"\x1b\x40Hello\x1d\x56\x00")

        assert result is True
        mock_sock.sendall.assert_called_once()
        mock_sleep.assert_called_once_with(0.5)
        assert not p.is_connected()  # Should close after printing

    @patch("lib.printer.time.sleep")
    @patch("lib.printer.socket.socket")
    def test_print_receipt_connect_failure(self, mock_socket_cls, mock_sleep):
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = OSError("No route")
        mock_socket_cls.return_value = mock_sock

        p = PrinterConnection("192.168.1.100")
        result = p.print_receipt(b"data")

        assert result is False


class TestPrinterConnectionTestConnection:
    @patch("lib.printer.socket.socket")
    def test_reachable(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock

        p = PrinterConnection("192.168.1.100", port=9100)
        result = p.test_connection()

        assert result is True
        mock_sock.settimeout.assert_called_once_with(3)
        mock_sock.connect.assert_called_once_with(("192.168.1.100", 9100))
        mock_sock.close.assert_called_once()

    @patch("lib.printer.socket.socket")
    def test_unreachable(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = OSError("Timeout")
        mock_socket_cls.return_value = mock_sock

        p = PrinterConnection("192.168.1.100")
        result = p.test_connection()

        assert result is False


class TestPrinterConnectionContextManager:
    @patch("lib.printer.socket.socket")
    def test_context_manager(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock

        with PrinterConnection("192.168.1.100") as p:
            assert p.is_connected()

        mock_sock.close.assert_called()
