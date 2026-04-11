#!/bin/bash
# Upload list-a-day client code to ESP32
# Usage: ./tools/upload.sh [PORT]

set -e

PORT="${1:-/dev/tty.usbserial-*}"
CLIENT_DIR="$(dirname "$0")/../client"

echo "=== list-a-day: Upload Code to ESP32 ==="
echo ""

# Check mpremote is installed
if ! command -v mpremote &> /dev/null; then
    echo "Error: mpremote not found. Install with:"
    echo "  pip install mpremote"
    exit 1
fi

echo "Uploading from: $CLIENT_DIR"
echo "To device on: $PORT"
echo ""

# Create lib directory on device
mpremote connect "$PORT" mkdir :lib 2>/dev/null || true

# Upload config
echo "Uploading config.py..."
mpremote connect "$PORT" cp "$CLIENT_DIR/config.py" :config.py

# Upload boot
echo "Uploading boot.py..."
mpremote connect "$PORT" cp "$CLIENT_DIR/boot.py" :boot.py

# Upload main
echo "Uploading main.py..."
mpremote connect "$PORT" cp "$CLIENT_DIR/main.py" :main.py

# Upload libraries
echo "Uploading lib/wifi_manager.py..."
mpremote connect "$PORT" cp "$CLIENT_DIR/lib/wifi_manager.py" :lib/wifi_manager.py

echo "Uploading lib/escpos.py..."
mpremote connect "$PORT" cp "$CLIENT_DIR/lib/escpos.py" :lib/escpos.py

echo "Uploading lib/printer.py..."
mpremote connect "$PORT" cp "$CLIENT_DIR/lib/printer.py" :lib/printer.py

echo "Uploading lib/api_client.py..."
mpremote connect "$PORT" cp "$CLIENT_DIR/lib/api_client.py" :lib/api_client.py

echo "Uploading lib/formatter.py..."
mpremote connect "$PORT" cp "$CLIENT_DIR/lib/formatter.py" :lib/formatter.py

echo ""
echo "Done! Reset your ESP32 to start list-a-day."
echo "  mpremote connect $PORT reset"
