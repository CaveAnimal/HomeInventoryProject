# iPhone LAN Access Runbook

Use this when you want to open the Home Inventory site from your iPhone on the home network.

## URL To Open On iPhone

```text
http://192.168.86.83:1800/
http://192.168.86.83:1800/capture
http://192.168.86.83:1800/import
```

The dashboard (`http://127.0.0.1:1800/` on the PC) shows the current phone URL near the top, so check there if the IP ever changes.

## First Check: Is The iPhone On Hogwarts?

The PC is on the **Hogwarts** network (wired Ethernet). The iPhone must be on **Hogwarts** Wi-Fi too.

If the phone has joined **Durmstrang** (or a guest network, or is using cellular data), Firefox/Safari shows "couldn't connect" even though the app is running fine. Switch the phone to Hogwarts and reload.

## How The App Runs

The app normally starts at boot as an elevated (SYSTEM) task that runs `start.ps1`. It binds to `0.0.0.0:1800`, so it's reachable from the LAN, and uses the local Bonsai server (`127.0.0.1:1080`) for photo detection.

To restart it by hand, open **PowerShell as Administrator** in the repo root:

```powershell
Set-Location "E:\MyProjects\MyGitHubCopilot\home-inventory\HIP-001"
.\stop.ps1 -KeepOllama
.\start.ps1
```

A non-admin `stop.ps1` gets "Access is denied" against the boot-started instance. If you stop it and wait, the boot task may relaunch it on its own within a couple of minutes.

## Quick Validation From PC

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:1800/" -UseBasicParsing | Select-Object StatusCode
Invoke-WebRequest -Uri "http://192.168.86.83:1800/" -UseBasicParsing | Select-Object StatusCode
```

Both should return `200`. If they do and the phone still can't connect, the problem is on the phone or network side. Work through the list below.

## If iPhone Still Cannot Reach It

1. **Network:** the phone is on Hogwarts, not Durmstrang, guest Wi-Fi, or cellular. VPN is off.
2. **Address:** the URL is exactly `http://192.168.86.83:1800`, starting with `http://`, with no typos such as `192.168..86.83`.
3. **iOS Local Network permission:** go to Settings → Firefox (or the browser you're using) → turn on **Local Network**. You can also try Safari.
4. **IP changed:** DHCP can hand the PC a new address. Check the dashboard or run:

   ```powershell
   Get-NetIPAddress -AddressFamily IPv4 |
     Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } |
     Select-Object InterfaceAlias, IPAddress
   ```

   Use the **Ethernet** address (the 192.168.86.x one), not Tailscale's 100.x address.
5. **Firewall (last resort):** Windows classes the Ethernet network as **Public**. It has worked without a rule so far, but if it's ever blocked, run this in an Administrator PowerShell:

   ```powershell
   New-NetFirewallRule -DisplayName "Home Inventory 1800" -Direction Inbound -Protocol TCP -LocalPort 1800 -Action Allow -Profile Private,Public
   ```
