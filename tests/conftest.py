"""Pytest configuration — mocks for MicroPython-specific modules."""

import sys
import types
from unittest.mock import MagicMock

# Mock MicroPython-specific modules before any client code is imported


def _setup_micropython_mocks():
    """Install mock modules that simulate MicroPython's API."""

    # --- network module ---
    network_mod = types.ModuleType("network")
    network_mod.STA_IF = 0
    network_mod.WLAN = MagicMock
    sys.modules["network"] = network_mod

    # --- machine module ---
    machine_mod = types.ModuleType("machine")
    machine_mod.reset = MagicMock()
    machine_mod.UART = MagicMock
    machine_mod.Pin = MagicMock
    sys.modules["machine"] = machine_mod

    # --- ujson → json ---
    import json
    sys.modules["ujson"] = json

    # --- urequests (mock) ---
    urequests_mod = types.ModuleType("urequests")
    urequests_mod.get = MagicMock()
    sys.modules["urequests"] = urequests_mod

    # --- Add client/ to sys.path so `from lib.xxx` and `import config` work ---
    import os
    client_dir = os.path.join(os.path.dirname(__file__), "..", "client")
    client_dir = os.path.abspath(client_dir)
    if client_dir not in sys.path:
        sys.path.insert(0, client_dir)

    # Also add project root
    project_root = os.path.join(os.path.dirname(__file__), "..")
    project_root = os.path.abspath(project_root)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


_setup_micropython_mocks()
