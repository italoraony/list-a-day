import network
import time


class WiFiManager:
    """Manages WiFi connection for ESP32."""

    def __init__(self, ssid, password, max_retries=10, retry_delay=2):
        self.ssid = ssid
        self.password = password
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.wlan = network.WLAN(network.STA_IF)

    def connect(self):
        """Connect to WiFi network. Returns True on success."""
        if self.is_connected():
            print("[WiFi] Already connected:", self.get_ip())
            return True

        self.wlan.active(True)
        self.wlan.connect(self.ssid, self.password)
        print(f"[WiFi] Connecting to {self.ssid}...")

        for attempt in range(self.max_retries):
            if self.wlan.isconnected():
                ip = self.get_ip()
                print(f"[WiFi] Connected! IP: {ip}")
                return True
            print(f"[WiFi] Attempt {attempt + 1}/{self.max_retries}...")
            time.sleep(self.retry_delay)

        print("[WiFi] Failed to connect after all retries")
        return False

    def disconnect(self):
        """Disconnect from WiFi."""
        if self.wlan.active():
            self.wlan.disconnect()
            self.wlan.active(False)
            print("[WiFi] Disconnected")

    def is_connected(self):
        """Check if currently connected to WiFi."""
        return self.wlan.active() and self.wlan.isconnected()

    def get_ip(self):
        """Get current IP address, or None if not connected."""
        if self.is_connected():
            return self.wlan.ifconfig()[0]
        return None

    def get_info(self):
        """Get full network info (ip, subnet, gateway, dns)."""
        if self.is_connected():
            ifconfig = self.wlan.ifconfig()
            return {
                "ip": ifconfig[0],
                "subnet": ifconfig[1],
                "gateway": ifconfig[2],
                "dns": ifconfig[3],
            }
        return None

    def ensure_connected(self):
        """Ensure WiFi is connected, reconnecting if necessary."""
        if not self.is_connected():
            print("[WiFi] Connection lost, reconnecting...")
            return self.connect()
        return True
