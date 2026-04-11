# list-a-day configuration
# Copy this file and update with your settings

# WiFi Configuration
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASS = "YOUR_WIFI_PASSWORD"

# Printer Configuration (Nucoun VCP-8370)
PRINTER_IP = "192.168.1.100"  # Static IP of your printer on the LAN
PRINTER_PORT = 9100            # Standard RAW print port

# Server Configuration (future)
SERVER_URL = "http://192.168.1.50:8080"
API_POLL_INTERVAL = 3600  # Seconds between server polls (default: 1 hour)

# Print Settings
RECEIPT_WIDTH = 48  # Characters per line (Font A on 80mm paper)
PRINT_HEADER = "✦ LIST-A-DAY ✦"
PRINT_FOOTER = "Have a great day!"
