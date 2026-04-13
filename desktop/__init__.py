"""list-a-day desktop CLI — print daily lists from your computer.

Reuses the same ESC/POS, printer, and formatter libraries as the ESP32 client.
No MicroPython dependencies — runs on standard Python 3.10+.

Usage:
    uv run python -m desktop                    # Print daily list (mock data)
    uv run python -m desktop --test             # Test printer connection
    uv run python -m desktop --ip 192.168.1.100 # Specify printer IP
    uv run python -m desktop --preview          # Preview receipt as text (no printer)
"""

import argparse
import sys
import os
import time
from datetime import datetime

# Add client/ to path so we can reuse the shared libraries
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "client"))

from lib.escpos import ESCPOSBuilder
from lib.printer import PrinterConnection
from lib.formatter import ReceiptFormatter
from lib.api_client import MOCK_TODOS, MOCK_EVENTS


DEFAULT_PRINTER_IP = "192.168.1.100"
DEFAULT_PRINTER_PORT = 9100
RECEIPT_WIDTH = 48


def get_date_string():
    """Get current date as a formatted string."""
    now = datetime.now()
    return now.strftime("%a, %b %d, %Y")


def fetch_data(server_url=None):
    """Fetch todos and calendar from server, or use mock data."""
    if server_url:
        try:
            import json
            from urllib.request import urlopen, Request

            print(f"[API] Fetching from {server_url}...")

            todos_req = Request(f"{server_url}/todos")
            todos_resp = urlopen(todos_req, timeout=5)
            todos = json.loads(todos_resp.read())

            cal_req = Request(f"{server_url}/calendar")
            cal_resp = urlopen(cal_req, timeout=5)
            events = json.loads(cal_resp.read())

            print(f"[API] Got {len(todos)} todos, {len(events)} events")
            return todos, events
        except Exception as e:
            print(f"[API] Server unavailable ({e}), using mock data")

    print("[API] Using mock data")
    return MOCK_TODOS, MOCK_EVENTS


def preview_receipt(date_str, todos, events, header, footer):
    """Preview receipt content as plain text (no ESC/POS codes)."""
    lines = []
    lines.append("")
    lines.append("=" * RECEIPT_WIDTH)
    lines.append(header.center(RECEIPT_WIDTH))
    lines.append(date_str.center(RECEIPT_WIDTH))
    lines.append("=" * RECEIPT_WIDTH)

    if todos:
        lines.append("")
        lines.append("  TO-DO LIST")
        lines.append("-" * RECEIPT_WIDTH)
        for todo in todos:
            done = todo.get("done", False)
            priority = todo.get("priority", "")
            title = todo.get("title", "Untitled")
            checkbox = "[x]" if done else "[ ]"
            marker = "!! " if priority == "high" else "!  " if priority == "medium" else ""
            lines.append(f"  {checkbox} {marker}{title}")

    if events:
        lines.append("")
        lines.append("  CALENDAR")
        lines.append("-" * RECEIPT_WIDTH)
        for event in events:
            t = event.get("time", "")
            title = event.get("title", "Untitled")
            location = event.get("location", "")
            lines.append(f"  {t}  {title}")
            if location:
                lines.append(f"          @ {location}")

    lines.append("")
    lines.append("=" * RECEIPT_WIDTH)
    lines.append(footer.center(RECEIPT_WIDTH))
    lines.append("=" * RECEIPT_WIDTH)
    lines.append("")

    return "\n".join(lines)


def cmd_print(args):
    """Print a daily receipt."""
    printer = PrinterConnection(args.ip, args.port)
    formatter = ReceiptFormatter(
        width=RECEIPT_WIDTH,
        header=args.header,
        footer=args.footer,
    )

    date_str = get_date_string()
    todos, events = fetch_data(args.server)

    if args.preview:
        print(preview_receipt(date_str, todos, events, args.header, args.footer))
        return

    print(f"[Printer] Connecting to {args.ip}:{args.port}...")
    receipt_data = formatter.build_daily_receipt(date_str, todos, events)
    print(f"[Printer] Sending {len(receipt_data)} bytes...")

    if printer.print_receipt(receipt_data):
        print("✅ Printed successfully!")
    else:
        print("❌ Print failed — is the printer on and connected to the network?")
        sys.exit(1)


def cmd_test(args):
    """Test printer connection."""
    printer = PrinterConnection(args.ip, args.port)
    print(f"Testing connection to {args.ip}:{args.port}...")

    if not printer.test_connection():
        print("❌ Printer unreachable")
        sys.exit(1)

    print("✅ Printer reachable! Sending test page...")

    builder = ESCPOSBuilder()
    builder.reset()
    builder.align("center")
    builder.size(2, 2)
    builder.bold(True)
    builder.text("LIST-A-DAY")
    builder.newline()
    builder.size(1, 1)
    builder.bold(False)
    builder.text("Desktop test print")
    builder.newline()
    builder.separator("=", RECEIPT_WIDTH)
    builder.align("left")
    builder.text(f" Printer: {args.ip}:{args.port}")
    builder.newline()
    builder.text(f" Date: {get_date_string()}")
    builder.newline()
    builder.text(f" Source: Desktop (Python {sys.version.split()[0]})")
    builder.newline()
    builder.separator("=", RECEIPT_WIDTH)
    builder.align("center")
    builder.font("B")
    builder.text("Printer is working!")
    builder.newline()
    builder.font("A")
    builder.cut()

    if printer.print_receipt(builder.build()):
        print("✅ Test page printed!")
    else:
        print("❌ Failed to send test page")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="list-a-day",
        description="Print daily todo lists and calendar on your thermal printer",
    )
    parser.add_argument(
        "--ip",
        default=os.environ.get("PRINTER_IP", DEFAULT_PRINTER_IP),
        help=f"Printer IP address (default: {DEFAULT_PRINTER_IP}, or PRINTER_IP env var)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PRINTER_PORT", DEFAULT_PRINTER_PORT)),
        help=f"Printer port (default: {DEFAULT_PRINTER_PORT})",
    )
    parser.add_argument(
        "--server",
        default=os.environ.get("SERVER_URL"),
        help="Server URL to fetch data from (default: use mock data)",
    )
    parser.add_argument(
        "--header",
        default="✦ LIST-A-DAY ✦",
        help="Receipt header text",
    )
    parser.add_argument(
        "--footer",
        default="Have a great day!",
        help="Receipt footer text",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Print a test page to verify printer connection",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview receipt as text in terminal (don't send to printer)",
    )

    args = parser.parse_args()

    print()
    print("=" * 40)
    print("  list-a-day — Desktop Printer Client")
    print("=" * 40)
    print()

    if args.test:
        cmd_test(args)
    else:
        cmd_print(args)


if __name__ == "__main__":
    main()
