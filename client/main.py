"""list-a-day — Main application for ESP32 thermal printer client."""

import time
import config
from lib.wifi_manager import WiFiManager
from lib.printer import PrinterConnection
from lib.api_client import APIClient
from lib.formatter import ReceiptFormatter


def get_date_string():
    """Get current date as a formatted string."""
    try:
        t = time.localtime()
        months = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ]
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return f"{days[t[6]]}, {months[t[1]-1]} {t[2]:02d}, {t[0]}"
    except Exception:
        return "Today"


def print_daily_list(printer, api, formatter):
    """Fetch data from server and print a daily receipt."""
    print("\n[Main] Preparing daily print...")

    date_str = get_date_string()
    todos = api.get_todos()
    events = api.get_calendar()

    print(f"[Main] {len(todos or [])} todos, {len(events or [])} events")

    receipt_data = formatter.build_daily_receipt(date_str, todos, events)
    print(f"[Main] Receipt: {len(receipt_data)} bytes")

    success = printer.print_receipt(receipt_data)
    if success:
        print("[Main] Printed successfully!")
    else:
        print("[Main] Print failed!")
    return success


def test_print(printer):
    """Print a test receipt to verify printer connection."""
    from lib.escpos import ESCPOSBuilder

    builder = ESCPOSBuilder()
    builder.reset()
    builder.align('center')
    builder.size(2, 2)
    builder.bold(True)
    builder.text("LIST-A-DAY")
    builder.newline()
    builder.size(1, 1)
    builder.bold(False)
    builder.text("Test print successful!")
    builder.newline()
    builder.separator('=', config.RECEIPT_WIDTH)
    builder.align('left')
    builder.text(f" Printer: {config.PRINTER_IP}:{config.PRINTER_PORT}")
    builder.newline()
    builder.text(f" Date: {get_date_string()}")
    builder.newline()
    builder.separator('=', config.RECEIPT_WIDTH)
    builder.align('center')
    builder.font('B')
    builder.text("Printer is working!")
    builder.newline()
    builder.font('A')
    builder.cut()

    return printer.print_receipt(builder.build())


def main():
    """Main application loop."""
    print("\n" + "=" * 40)
    print("  list-a-day - Thermal Printer Client")
    print("=" * 40)

    # Initialize components
    wifi = WiFiManager(config.WIFI_SSID, config.WIFI_PASS)
    printer = PrinterConnection(config.PRINTER_IP, config.PRINTER_PORT)
    api = APIClient(config.SERVER_URL)
    formatter = ReceiptFormatter(
        width=config.RECEIPT_WIDTH,
        header=config.PRINT_HEADER,
        footer=config.PRINT_FOOTER,
    )

    # Ensure WiFi is connected
    if not wifi.ensure_connected():
        print("[Main] Cannot start without WiFi. Rebooting in 30s...")
        time.sleep(30)
        import machine
        machine.reset()

    # Test printer connectivity
    print("[Main] Testing printer connection...")
    if not printer.test_connection():
        print("[Main] WARNING: Printer not reachable. Will retry on print.")

    # Print on first boot
    print_daily_list(printer, api, formatter)

    # Main polling loop
    print(f"[Main] Polling every {config.API_POLL_INTERVAL}s...")
    while True:
        time.sleep(config.API_POLL_INTERVAL)

        wifi.ensure_connected()
        print_daily_list(printer, api, formatter)


# Entry point
main()
