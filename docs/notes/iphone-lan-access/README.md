# iPhone LAN Access Runbook

Use this when you want to open the Home Inventory site from your iPhone on the same Wi-Fi.

## Goal

Run the app so it is reachable on your local network, not only on localhost.

## One-Time Checks

1. PC and iPhone are on the same Wi-Fi SSID.
2. The Wi-Fi network profile in Windows is **Private**.
3. VPN is off on both devices during local testing.
4. iPhone cellular data is off during the test (to force Wi-Fi route).

## Start The App For LAN Access

From repository root:

```powershell
Set-Location "E:\MyProjects\MyGitHubCopilot\home-inventory\HIP-001\outputs\home-inventory-app"

# Create venv once (skip if .venv312 exists)
py -3.12 -m venv .venv312

# Install deps once, then as needed after changes
.\.venv312\Scripts\python.exe -m pip install -r requirements.txt

# Start server on all interfaces (important)
.\.venv312\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Keep that terminal running.

## Find Your PC LAN IP

In another PowerShell window:

```powershell
Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.IPAddress -notlike '127.*' -and $_.InterfaceAlias -notlike 'vEthernet*' } |
  Select-Object InterfaceAlias, IPAddress
```

Use the Ethernet or Wi-Fi address (example: `192.168.86.83`).

## URL To Open On iPhone

```text
http://<LAN-IP>:8000/
http://<LAN-IP>:8000/import
http://<LAN-IP>:8000/capture
```

Example:

```text
http://192.168.86.83:8000/
```

## Quick Validation From PC

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/" -UseBasicParsing | Select-Object StatusCode
Invoke-WebRequest -Uri "http://192.168.86.83:8000/" -UseBasicParsing | Select-Object StatusCode
```

Both should return `200`.

## If iPhone Still Cannot Reach It

1. Confirm app was started with `--host 0.0.0.0` (not `127.0.0.1`).
2. Confirm LAN IP did not change (DHCP can rotate it).
3. Confirm iPhone is not on Guest Wi-Fi.
4. Temporarily allow inbound port 8000 on Windows Defender Firewall.

Optional firewall rule (run as admin PowerShell):

```powershell
netsh advfirewall firewall add rule name="HomeInventory8000" dir=in action=allow protocol=TCP localport=8000
```

## Stop The Server

In the server terminal, press `Ctrl+C`.
