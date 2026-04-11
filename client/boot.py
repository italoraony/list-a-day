"""MicroPython boot file — runs on startup before main.py."""

import config
from lib.wifi_manager import WiFiManager

# Connect to WiFi on boot
wifi = WiFiManager(config.WIFI_SSID, config.WIFI_PASS)
connected = wifi.connect()

if connected:
    print("[Boot] WiFi ready —", wifi.get_ip())
else:
    print("[Boot] WiFi failed — will retry in main loop")
