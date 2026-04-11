#!/bin/bash
# Flash MicroPython firmware to ESP32
# Usage: ./tools/flash.sh [PORT]

set -e

PORT="${1:-/dev/tty.usbserial-*}"
FIRMWARE_URL="https://micropython.org/resources/firmware/ESP32_GENERIC-20240602-v1.23.0.bin"
FIRMWARE_FILE="/tmp/micropython-esp32.bin"

echo "=== list-a-day: Flash MicroPython to ESP32 ==="
echo ""

# Check esptool is installed
if ! command -v esptool.py &> /dev/null; then
    echo "Error: esptool.py not found. Install with:"
    echo "  pip install esptool"
    exit 1
fi

# Download firmware if not cached
if [ ! -f "$FIRMWARE_FILE" ]; then
    echo "Downloading MicroPython firmware..."
    curl -L -o "$FIRMWARE_FILE" "$FIRMWARE_URL"
fi

echo "Using port: $PORT"
echo ""

# Erase flash
echo "Step 1/2: Erasing flash..."
esptool.py --chip esp32 --port "$PORT" erase_flash

# Flash firmware
echo "Step 2/2: Flashing MicroPython..."
esptool.py --chip esp32 --port "$PORT" --baud 460800 write_flash -z 0x1000 "$FIRMWARE_FILE"

echo ""
echo "Done! MicroPython is now installed on your ESP32."
echo "Connect with: screen $PORT 115200"
