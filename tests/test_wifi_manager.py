"""Tests for WiFi connection manager."""

import pytest
from unittest.mock import patch, MagicMock


class TestWiFiManagerInit:
    def test_stores_credentials(self):
        from lib.wifi_manager import WiFiManager
        wm = WiFiManager("TestSSID", "TestPass")
        assert wm.ssid == "TestSSID"
        assert wm.password == "TestPass"
        assert wm.max_retries == 10
        assert wm.retry_delay == 2

    def test_custom_retries(self):
        from lib.wifi_manager import WiFiManager
        wm = WiFiManager("TestSSID", "TestPass", max_retries=5, retry_delay=1)
        assert wm.max_retries == 5
        assert wm.retry_delay == 1


class TestWiFiManagerConnect:
    @patch("lib.wifi_manager.time.sleep")
    def test_connect_success_immediate(self, mock_sleep):
        from lib.wifi_manager import WiFiManager
        wm = WiFiManager("TestSSID", "TestPass")
        wm.wlan = MagicMock()
        wm.wlan.active.return_value = False
        wm.wlan.isconnected.side_effect = [False, True]
        wm.wlan.ifconfig.return_value = ("192.168.1.50", "255.255.255.0", "192.168.1.1", "8.8.8.8")

        result = wm.connect()

        assert result is True
        # active(True) is called to activate WiFi, then active() is called later in is_connected()
        wm.wlan.active.assert_any_call(True)
        wm.wlan.connect.assert_called_once_with("TestSSID", "TestPass")

    @patch("lib.wifi_manager.time.sleep")
    def test_connect_already_connected(self, mock_sleep):
        from lib.wifi_manager import WiFiManager
        wm = WiFiManager("TestSSID", "TestPass")
        wm.wlan = MagicMock()
        wm.wlan.active.return_value = True
        wm.wlan.isconnected.return_value = True
        wm.wlan.ifconfig.return_value = ("192.168.1.50", "255.255.255.0", "192.168.1.1", "8.8.8.8")

        result = wm.connect()

        assert result is True
        wm.wlan.connect.assert_not_called()

    @patch("lib.wifi_manager.time.sleep")
    def test_connect_failure_all_retries(self, mock_sleep):
        from lib.wifi_manager import WiFiManager
        wm = WiFiManager("TestSSID", "TestPass", max_retries=3, retry_delay=0)
        wm.wlan = MagicMock()
        wm.wlan.active.return_value = False
        wm.wlan.isconnected.return_value = False

        result = wm.connect()

        assert result is False
        assert mock_sleep.call_count == 3

    @patch("lib.wifi_manager.time.sleep")
    def test_connect_succeeds_on_third_retry(self, mock_sleep):
        from lib.wifi_manager import WiFiManager
        wm = WiFiManager("TestSSID", "TestPass", max_retries=5)
        wm.wlan = MagicMock()
        # First call to is_connected returns False (not already connected)
        # Then isconnected() returns False, False, True during polling
        wm.wlan.active.return_value = False
        wm.wlan.isconnected.side_effect = [False, False, True]
        wm.wlan.ifconfig.return_value = ("192.168.1.50", "255.255.255.0", "192.168.1.1", "8.8.8.8")

        result = wm.connect()

        assert result is True
        assert mock_sleep.call_count == 2


class TestWiFiManagerDisconnect:
    def test_disconnect_when_active(self):
        from lib.wifi_manager import WiFiManager
        wm = WiFiManager("TestSSID", "TestPass")
        wm.wlan = MagicMock()
        wm.wlan.active.return_value = True

        wm.disconnect()

        wm.wlan.disconnect.assert_called_once()
        wm.wlan.active.assert_called_with(False)

    def test_disconnect_when_not_active(self):
        from lib.wifi_manager import WiFiManager
        wm = WiFiManager("TestSSID", "TestPass")
        wm.wlan = MagicMock()
        wm.wlan.active.return_value = False

        wm.disconnect()

        wm.wlan.disconnect.assert_not_called()


class TestWiFiManagerStatus:
    def test_is_connected_true(self):
        from lib.wifi_manager import WiFiManager
        wm = WiFiManager("TestSSID", "TestPass")
        wm.wlan = MagicMock()
        wm.wlan.active.return_value = True
        wm.wlan.isconnected.return_value = True

        assert wm.is_connected() is True

    def test_is_connected_false_not_active(self):
        from lib.wifi_manager import WiFiManager
        wm = WiFiManager("TestSSID", "TestPass")
        wm.wlan = MagicMock()
        wm.wlan.active.return_value = False
        wm.wlan.isconnected.return_value = True

        assert wm.is_connected() is False

    def test_is_connected_false_not_connected(self):
        from lib.wifi_manager import WiFiManager
        wm = WiFiManager("TestSSID", "TestPass")
        wm.wlan = MagicMock()
        wm.wlan.active.return_value = True
        wm.wlan.isconnected.return_value = False

        assert wm.is_connected() is False

    def test_get_ip_when_connected(self):
        from lib.wifi_manager import WiFiManager
        wm = WiFiManager("TestSSID", "TestPass")
        wm.wlan = MagicMock()
        wm.wlan.active.return_value = True
        wm.wlan.isconnected.return_value = True
        wm.wlan.ifconfig.return_value = ("192.168.1.50", "255.255.255.0", "192.168.1.1", "8.8.8.8")

        assert wm.get_ip() == "192.168.1.50"

    def test_get_ip_when_not_connected(self):
        from lib.wifi_manager import WiFiManager
        wm = WiFiManager("TestSSID", "TestPass")
        wm.wlan = MagicMock()
        wm.wlan.active.return_value = False
        wm.wlan.isconnected.return_value = False

        assert wm.get_ip() is None

    def test_get_info_when_connected(self):
        from lib.wifi_manager import WiFiManager
        wm = WiFiManager("TestSSID", "TestPass")
        wm.wlan = MagicMock()
        wm.wlan.active.return_value = True
        wm.wlan.isconnected.return_value = True
        wm.wlan.ifconfig.return_value = ("192.168.1.50", "255.255.255.0", "192.168.1.1", "8.8.8.8")

        info = wm.get_info()

        assert info == {
            "ip": "192.168.1.50",
            "subnet": "255.255.255.0",
            "gateway": "192.168.1.1",
            "dns": "8.8.8.8",
        }

    def test_get_info_when_not_connected(self):
        from lib.wifi_manager import WiFiManager
        wm = WiFiManager("TestSSID", "TestPass")
        wm.wlan = MagicMock()
        wm.wlan.active.return_value = False
        wm.wlan.isconnected.return_value = False

        assert wm.get_info() is None


class TestWiFiManagerEnsureConnected:
    @patch("lib.wifi_manager.time.sleep")
    def test_ensure_connected_already_connected(self, mock_sleep):
        from lib.wifi_manager import WiFiManager
        wm = WiFiManager("TestSSID", "TestPass")
        wm.wlan = MagicMock()
        wm.wlan.active.return_value = True
        wm.wlan.isconnected.return_value = True

        result = wm.ensure_connected()

        assert result is True
        wm.wlan.connect.assert_not_called()

    @patch("lib.wifi_manager.time.sleep")
    def test_ensure_connected_reconnects(self, mock_sleep):
        from lib.wifi_manager import WiFiManager
        wm = WiFiManager("TestSSID", "TestPass", max_retries=3)
        wm.wlan = MagicMock()
        # active() returns False so is_connected() short-circuits without calling isconnected()
        # This means isconnected() is only called in the connect() loop
        wm.wlan.active.return_value = False
        wm.wlan.isconnected.side_effect = [False, True]
        wm.wlan.ifconfig.return_value = ("192.168.1.50", "255.255.255.0", "192.168.1.1", "8.8.8.8")

        result = wm.ensure_connected()

        assert result is True
        wm.wlan.connect.assert_called_once()
