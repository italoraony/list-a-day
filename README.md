# list-a-day 🖨️

A MicroPython client for ESP32 that prints daily todo lists and calendar items on a thermal receipt printer over LAN.

## Overview

**list-a-day** connects an ESP32 microcontroller to a Nucoun VCP-8370 thermal receipt printer via your local network. The ESP32 fetches todo lists and calendar data from a server API, formats them as styled receipts, and prints them — giving you a tangible daily agenda.

## Architecture

```
[Server]  --WiFi/HTTP-->  [ESP32]  --TCP:9100-->  [VCP-8370 Printer]
                            |                          |
                         (WiFi)                   (Ethernet)
                            └────── Same LAN ─────────┘
```

## Hardware

- **ESP32** (any variant with WiFi)
- **Nucoun VCP-8370** thermal receipt printer (80mm, ESC/POS, USB+LAN)
- Ethernet cable (printer to router/switch)
- 80mm thermal paper rolls

## Quick Start

1. Flash MicroPython firmware to your ESP32 — see [docs/setup.md](docs/setup.md)
2. Configure WiFi and printer IP in `client/config.py`
3. Connect printer to LAN — see [docs/network-setup.md](docs/network-setup.md)
4. Upload code to ESP32: `./tools/upload.sh`
5. Reboot ESP32 and watch it print!

## Project Structure

```
client/
├── boot.py              # WiFi setup on boot
├── main.py              # Main application loop
├── config.py            # All configuration settings
└── lib/
    ├── wifi_manager.py  # WiFi connection management
    ├── escpos.py        # ESC/POS command builder
    ├── printer.py       # TCP socket printer driver
    ├── api_client.py    # HTTP client for server API
    └── formatter.py     # Receipt layout formatter
```

## Tech Stack

- **MicroPython** on ESP32
- **ESC/POS** protocol over TCP (port 9100)
- **HTTP** for server communication

## License

MIT
