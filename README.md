# list-a-day 🖨️

A thermal receipt printer client that prints daily todo lists and calendar items — runs on **ESP32 (MicroPython)** or **your desktop (Python 3.10+)**.

## Overview

**list-a-day** connects to a Nucoun VCP-8370 thermal receipt printer via your local network. It fetches todo lists and calendar data, formats them as styled receipts, and prints them — giving you a tangible daily agenda.

## Architecture

```
[Server]  --HTTP-->  [ESP32 or Desktop]  --TCP:9100-->  [VCP-8370 Printer]
                            |                                |
                      (WiFi or LAN)                     (Ethernet)
                            └──────── Same LAN ─────────────┘
```

## Quick Start (Desktop)

No hardware needed beyond the printer on your network:

```bash
# Preview receipt in terminal (no printer needed)
uv run python -m desktop --preview

# Print to your printer
uv run python -m desktop --ip 192.168.1.100

# Test printer connection
uv run python -m desktop --test --ip 192.168.1.100

# Set printer IP via environment variable
export PRINTER_IP=192.168.1.100
uv run python -m desktop
```

## Quick Start (ESP32)

1. Flash MicroPython firmware to your ESP32 — see [docs/setup.md](docs/setup.md)
2. Configure WiFi and printer IP in `client/config.py`
3. Connect printer to LAN — see [docs/network-setup.md](docs/network-setup.md)
4. Upload code to ESP32: `./tools/upload.sh`
5. Reboot ESP32 and watch it print!

## Hardware

- **Nucoun VCP-8370** thermal receipt printer (80mm, ESC/POS, USB+LAN)
- Ethernet cable (printer to router/switch)
- 80mm thermal paper rolls
- **ESP32** (any variant with WiFi) — only needed for standalone mode

## Project Structure

```
desktop/                 # Desktop CLI (Python 3.10+)
├── __init__.py          # CLI entry point with argparse
└── __main__.py          # python -m desktop support

client/                  # ESP32 MicroPython client
├── boot.py              # WiFi setup on boot
├── main.py              # Main application loop
├── config.py            # All configuration settings
└── lib/                 # Shared libraries (used by both desktop & ESP32)
    ├── escpos.py        # ESC/POS command builder
    ├── printer.py       # TCP socket printer driver
    ├── formatter.py     # Receipt layout formatter
    ├── api_client.py    # HTTP client for server API
    └── wifi_manager.py  # WiFi connection management (ESP32 only)

tests/                   # Test suite (151 tests)
```

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest tests/ -v
```

## License

MIT
