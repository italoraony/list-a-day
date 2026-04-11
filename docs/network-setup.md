# Network Setup Guide

How to connect your Nucoun VCP-8370 thermal printer and ESP32 on the same LAN.

## Architecture

```
[Router/Switch]
     |
     |--- Ethernet ---> [VCP-8370 Printer] (IP: 192.168.1.100)
     |
     |--- WiFi -------> [ESP32]            (IP: DHCP assigned)
```

## Step 1: Connect the Printer

1. Plug an Ethernet cable from the printer's LAN port to your router or switch
2. Power on the printer (24V adapter)
3. The printer should obtain an IP via DHCP

## Step 2: Find the Printer's IP

Option A — **Print a self-test page**: Hold the FEED button while powering on the printer. The test page should show the network configuration including IP address.

Option B — **Check your router**: Log into your router's admin panel and look for the printer in the connected devices / DHCP leases list.

Option C — **Network scan**: From a computer on the same network:
```bash
# macOS/Linux
nmap -sn 192.168.1.0/24 | grep -B2 "9100"
# or
arp -a
```

## Step 3: Assign a Static IP (Recommended)

To prevent the printer's IP from changing:

1. Log into your router's admin panel
2. Find DHCP reservation / static lease settings
3. Add the printer's MAC address with a fixed IP (e.g., `192.168.1.100`)
4. Reboot the printer

## Step 4: Test Connectivity

From your computer on the same network:

```bash
# Ping the printer
ping 192.168.1.100

# Test the raw print port
nc -zv 192.168.1.100 9100

# Send a test print from your computer
echo -e "\x1b\x40Hello from LAN!\n\n\n\x1d\x56\x00" | nc 192.168.1.100 9100
```

## Step 5: Update ESP32 Config

Edit `client/config.py` and set:
```python
PRINTER_IP = "192.168.1.100"  # Your printer's static IP
PRINTER_PORT = 9100
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Printer not getting IP | Check Ethernet cable, ensure DHCP is enabled on router |
| Can't reach port 9100 | Verify printer is on, check firewall rules on router |
| ESP32 can't reach printer | Ensure both are on the same subnet (e.g., 192.168.1.x) |
| Intermittent connection | Assign static IP to avoid DHCP changes |
