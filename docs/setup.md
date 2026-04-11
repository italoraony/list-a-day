# Setup Guide

Complete setup guide for the list-a-day thermal printer client.

## Prerequisites

- ESP32 development board (any variant with WiFi)
- Nucoun VCP-8370 thermal receipt printer
- 80mm thermal paper rolls
- Ethernet cable
- USB cable (for programming ESP32)
- WiFi network

## 1. Install MicroPython on ESP32

### Install tools on your computer

```bash
pip install esptool mpremote
```

### Flash MicroPython firmware

```bash
# Make the flash script executable
chmod +x tools/flash.sh

# Flash (replace PORT with your ESP32's serial port)
./tools/flash.sh /dev/tty.usbserial-0001
```

### Verify MicroPython is running

```bash
mpremote connect /dev/tty.usbserial-0001 repl
# You should see the MicroPython REPL prompt: >>>
# Press Ctrl+] to exit
```

## 2. Set Up the Printer

Follow the [Network Setup Guide](network-setup.md) to:
1. Connect the printer to your LAN via Ethernet
2. Find and assign a static IP to the printer
3. Verify connectivity on port 9100

## 3. Configure the Client

```bash
# Copy the example config
cp client/config.example.py client/config.py
```

Edit `client/config.py` with your settings:
```python
WIFI_SSID = "YourWiFiName"
WIFI_PASS = "YourWiFiPassword"
PRINTER_IP = "192.168.1.100"  # Your printer's IP
```

## 4. Upload Code to ESP32

```bash
chmod +x tools/upload.sh
./tools/upload.sh /dev/tty.usbserial-0001
```

## 5. First Print!

Reset the ESP32:
```bash
mpremote connect /dev/tty.usbserial-0001 reset
```

The ESP32 will:
1. Connect to WiFi
2. Test the printer connection
3. Fetch data (mock data until server is built)
4. Print your first daily receipt!

## Testing from Your Computer

You can test the printer directly from your computer:

```bash
# Quick test print via netcat
echo -e "\x1b\x40Hello World!\n\n\n\x1d\x56\x00" | nc 192.168.1.100 9100
```

## File Structure on ESP32

After upload, the ESP32 filesystem looks like:
```
/
├── boot.py
├── main.py
├── config.py
└── lib/
    ├── wifi_manager.py
    ├── escpos.py
    ├── printer.py
    ├── api_client.py
    └── formatter.py
```
