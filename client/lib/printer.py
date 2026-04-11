"""TCP socket printer driver for ESC/POS thermal printers over LAN."""

import socket
import time


class PrinterConnection:
    """Manages TCP socket connection to a thermal printer on the network."""

    def __init__(self, ip, port=9100, timeout=5):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self._sock = None

    def connect(self):
        """Open TCP connection to the printer."""
        if self._sock is not None:
            self.close()
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(self.timeout)
            self._sock.connect((self.ip, self.port))
            print(f"[Printer] Connected to {self.ip}:{self.port}")
            return True
        except OSError as e:
            print(f"[Printer] Connection failed: {e}")
            self._sock = None
            return False

    def close(self):
        """Close the TCP connection."""
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
            print("[Printer] Connection closed")

    def is_connected(self):
        """Check if socket is open."""
        return self._sock is not None

    def send(self, data):
        """Send raw bytes to the printer.
        
        Args:
            data: bytes or bytearray of ESC/POS commands
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_connected():
            print("[Printer] Not connected, attempting to connect...")
            if not self.connect():
                return False

        try:
            if isinstance(data, (bytes, bytearray)):
                self._sock.sendall(data)
            else:
                self._sock.sendall(data.encode('utf-8'))
            return True
        except OSError as e:
            print(f"[Printer] Send failed: {e}")
            self.close()
            return False

    def print_receipt(self, escpos_data):
        """Send a complete receipt (ESC/POS bytes) to the printer.
        
        Opens a connection, sends the data, and closes.
        This is the recommended approach for receipt printing —
        one connection per receipt avoids stale socket issues.
        """
        if not self.connect():
            return False

        success = self.send(escpos_data)
        time.sleep(0.5)  # Allow printer to process before closing
        self.close()
        return success

    def test_connection(self):
        """Test if the printer is reachable on the network."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((self.ip, self.port))
            sock.close()
            print(f"[Printer] Reachable at {self.ip}:{self.port}")
            return True
        except OSError as e:
            print(f"[Printer] Unreachable: {e}")
            return False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()
