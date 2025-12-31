#!/usr/bin/env python3
"""Fleet - Media Server Stack"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

ENV_FILE = Path(".env")

ENV_TEMPLATE = """# Fleet - Edit VPN settings, then: python manage.py start

WIREGUARD_PRIVATE_KEY=CHANGE_ME
WIREGUARD_ADDRESSES=CHANGE_ME

# Optional
# VPN_CITY=
# DATA_PATH=./data
# CONFIG_PATH=./config
"""


def load_env():
    if not ENV_FILE.exists():
        return {}
    env = {}
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def docker_ok():
    try:
        return (
            subprocess.run(
                ["docker", "info"], capture_output=True, timeout=10
            ).returncode
            == 0
        )
    except:
        return False


def compose(*args):
    return subprocess.run(["docker", "compose", *args]).returncode


def docker_exec(container, cmd):
    try:
        r = subprocess.run(
            ["docker", "exec", container] + cmd,
            capture_output=True,
            text=True,
            timeout=15,
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except:
        return None


def cmd_setup():
    print("\n⚡ FLEET SETUP\n")

    if not docker_ok():
        print("❌ Docker not running!")
        print("   Install: https://docker.com/products/docker-desktop")
        return 1
    print("✓ Docker ready")

    if not ENV_FILE.exists():
        ENV_FILE.write_text(ENV_TEMPLATE)
        print("✓ Created .env")
    else:
        print("✓ .env exists")

    env = load_env()
    data = Path(env.get("DATA_PATH", "./data"))
    config = Path(env.get("CONFIG_PATH", "./config"))

    for sub in ["torrents/movies", "torrents/tv", "media/movies", "media/tv"]:
        (data / sub).mkdir(parents=True, exist_ok=True)
    config.mkdir(parents=True, exist_ok=True)
    print("✓ Created directories")

    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEXT:

1. Get Mullvad config: https://mullvad.net/en/account/wireguard-config
   → Generate key, download .conf file

2. Edit .env:
   WIREGUARD_PRIVATE_KEY=<from PrivateKey>
   WIREGUARD_ADDRESSES=<from Address>

3. python manage.py start
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
    return 0


def cmd_start():
    print("\n⚡ STARTING FLEET\n")

    if not ENV_FILE.exists():
        print("❌ Run first: python manage.py setup")
        return 1

    env = load_env()
    if env.get("WIREGUARD_PRIVATE_KEY", "CHANGE_ME") == "CHANGE_ME":
        print("❌ VPN not configured! Edit .env with your Mullvad keys")
        return 1

    if not docker_ok():
        print("❌ Docker not running!")
        return 1

    print("Pulling images...")
    compose("pull")

    print("Starting...")
    if compose("up", "-d") == 0:
        print("\n✓ Fleet is running!\n")
        show_urls()
        return 0
    print("\n❌ Failed. Check: python manage.py logs")
    return 1


def cmd_stop():
    print("Stopping...")
    compose("stop")
    print("✓ Stopped")
    return 0


def cmd_restart():
    print("Restarting...")
    compose("restart")
    print("✓ Restarted")
    show_urls()
    return 0


def cmd_status():
    print("\n⚡ FLEET STATUS\n")

    # Get container info
    r = subprocess.run(
        [
            "docker",
            "ps",
            "-a",
            "--filter",
            "name=fleet-",
            "--format",
            "{{.Names}}|{{.Status}}|{{.State}}",
        ],
        capture_output=True,
        text=True,
    )

    if not r.stdout.strip():
        print("❌ No Fleet containers found\n")
        print("Run: python manage.py start")
        return 1

    # Parse container data
    containers = {}
    for line in r.stdout.strip().split("\n"):
        if line:
            parts = line.split("|")
            name = parts[0].replace("fleet-", "")
            status_text = parts[1]  # e.g., "Up 8 minutes (unhealthy)"
            state = parts[2]  # e.g., "running"

            # Parse health status from status text
            health = "unknown"
            if "unhealthy" in status_text.lower():
                health = "unhealthy"
            elif "healthy" in status_text.lower():
                health = "healthy"
            elif "starting" in status_text.lower():
                health = "starting"

            containers[name] = {"status": status_text, "state": state, "health": health}

    # Service definitions with ports
    services = {
        "gluetun": {"name": "VPN", "port": None, "critical": True},
        "qbittorrent": {"name": "qBittorrent", "port": 8080, "critical": False},
        "jellyfin": {"name": "Jellyfin", "port": 8096, "critical": False},
        "jellyseerr": {"name": "Jellyseerr", "port": 5055, "critical": False},
        "radarr": {"name": "Radarr", "port": 7878, "critical": False},
        "sonarr": {"name": "Sonarr", "port": 8989, "critical": False},
        "prowlarr": {"name": "Prowlarr", "port": 9696, "critical": False},
        "bazarr": {"name": "Bazarr", "port": 6767, "critical": False},
    }

    # Get local IP
    ip = "localhost"
    try:
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except:
        pass

    # Display status
    all_running = True
    print("Services:")
    print("─" * 60)

    for svc_id, svc_info in services.items():
        if svc_id in containers:
            state = containers[svc_id]["state"]
            health = containers[svc_id]["health"]
            status_text = containers[svc_id]["status"]

            # Determine icon and status based on state and health
            if state == "running":
                if health == "unhealthy":
                    icon = "⚠"
                    status_display = "running (unhealthy)"
                    all_running = False
                elif health == "starting":
                    icon = "⋯"
                    status_display = "running (starting)"
                elif health == "healthy":
                    icon = "✓"
                    status_display = "running"
                else:
                    icon = "✓"
                    status_display = "running"
            else:
                icon = "✗"
                status_display = f"{state}"
                all_running = False

            # Format service line
            name = f"{svc_info['name']:<12}"
            status = f"{icon} {status_display:<22}"

            if svc_info["port"]:
                url = f"http://{ip}:{svc_info['port']}"
                print(f"{name} {status} {url}")
            else:
                print(f"{name} {status}")
        else:
            print(f"{svc_info['name']:<12} ✗ not found")
            all_running = False

    print("─" * 60)

    # VPN diagnostics
    if "gluetun" in containers and containers["gluetun"]["state"] == "running":
        print()

        # Check if VPN is unhealthy
        if containers["gluetun"]["health"] == "unhealthy":
            print("⚠ VPN is unhealthy - diagnosing...\n")

            # Check gluetun logs for errors
            log_result = subprocess.run(
                ["docker", "logs", "--tail", "30", "fleet-gluetun"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if log_result.returncode == 0:
                logs = log_result.stdout + log_result.stderr

                # Check for common error patterns
                if (
                    "authentication failed" in logs.lower()
                    or "invalid key" in logs.lower()
                ):
                    print("❌ VPN authentication failed")
                    print("   Check your WIREGUARD_PRIVATE_KEY in .env")
                elif "cannot resolve" in logs.lower() or "dns" in logs.lower():
                    print("❌ DNS/Network issue")
                    print("   Check your internet connection")
                elif "wireguard" in logs.lower() and "error" in logs.lower():
                    print("❌ WireGuard configuration error")
                    print(
                        "   Check WIREGUARD_PRIVATE_KEY and WIREGUARD_ADDRESSES in .env"
                    )
                else:
                    print("Healthcheck is failing. Recent logs:")
                    # Show last few relevant lines
                    error_lines = [
                        line
                        for line in logs.split("\n")
                        if "error" in line.lower() or "fail" in line.lower()
                    ]
                    if error_lines:
                        for line in error_lines[-3:]:
                            print(f"   {line}")
                    else:
                        # Show last 3 lines
                        for line in logs.split("\n")[-3:]:
                            if line.strip():
                                print(f"   {line}")

                print(
                    "\nHealthcheck: https://am.i.mullvad.net/connected must return 200"
                )
                print("Run for full logs: python manage.py logs gluetun")

        else:
            # VPN is healthy or starting, do normal checks
            ip_check = docker_exec(
                "fleet-qbittorrent", ["curl", "-s", "--max-time", "3", "ifconfig.me"]
            )
            if ip_check:
                print(f"VPN IP: {ip_check}")

                # Quick Mullvad check
                mullvad_check = docker_exec(
                    "fleet-qbittorrent",
                    ["curl", "-s", "--max-time", "3", "https://am.i.mullvad.net/json"],
                )
                if mullvad_check:
                    try:
                        data = json.loads(mullvad_check)
                        if data.get("mullvad_exit_ip"):
                            city = data.get("city", "Unknown")
                            country = data.get("country", "Unknown")
                            print(f"VPN Location: {city}, {country}")
                            print("✓ VPN is working")
                        else:
                            print("⚠ Not connected to Mullvad VPN")
                    except:
                        pass

    print()

    if all_running:
        print("✓ All services running")
    else:
        print("⚠ Some services not running")
        print("  Try: python manage.py start")

    print()
    return 0 if all_running else 1


def cmd_logs():
    service = sys.argv[2] if len(sys.argv) > 2 else None
    args = ["logs", "-f", "--tail=100"]
    if service:
        args.append(service)
    compose(*args)
    return 0


def cmd_vpn():
    print("\n⚡ VPN CHECK\n")

    r = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True
    )
    containers = r.stdout.strip().split("\n") if r.stdout else []

    if not any("gluetun" in c for c in containers):
        print("❌ VPN container not running")
        return 1

    ip = docker_exec(
        "fleet-qbittorrent", ["curl", "-s", "--max-time", "5", "ifconfig.me"]
    )
    if ip:
        print(f"✓ Torrent IP: {ip}")
    else:
        print("❌ Could not get IP")
        return 1

    result = docker_exec(
        "fleet-qbittorrent",
        ["curl", "-s", "--max-time", "5", "https://am.i.mullvad.net/json"],
    )
    if result:
        try:
            data = json.loads(result)
            if data.get("mullvad_exit_ip"):
                print(f"✓ Mullvad: {data.get('city', '?')}, {data.get('country', '?')}")
                print("\n✓ VPN WORKING")
                return 0
            print("\n❌ NOT ON MULLVAD")
            return 1
        except:
            pass

    print("⚠ Could not verify Mullvad")
    return 0


def cmd_clean():
    print("Removing containers...")
    compose("down")
    print("✓ Done (data preserved)")
    return 0


def cmd_reset():
    print("\n⚠️  This will DELETE all configs (media kept)\n")

    if input("Type 'reset' to confirm: ").lower() != "reset":
        print("Cancelled")
        return 0

    compose("down", "-v")

    config_path = Path(load_env().get("CONFIG_PATH", "./config"))
    if config_path.exists():
        shutil.rmtree(config_path)
        print(f"✓ Removed {config_path}")

    if ENV_FILE.exists():
        ENV_FILE.unlink()
        print("✓ Removed .env")

    print("\n✓ Reset complete. Run: python manage.py setup")
    return 0


def show_urls():
    ip = "localhost"
    try:
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except:
        pass

    print(f"""┌────────────────────────────────────────────┐
│  Jellyfin     http://{ip}:8096        │
│  Jellyseerr   http://{ip}:5055        │
│  Radarr       http://{ip}:7878        │
│  Sonarr       http://{ip}:8989        │
│  Prowlarr     http://{ip}:9696        │
│  qBittorrent  http://{ip}:8080        │
└────────────────────────────────────────────┘
qBittorrent login: admin / adminadmin (change it!)
""")


def show_help():
    print("""
⚡ FLEET - Media Server Stack

Usage: python manage.py <command>

  setup     Create .env and directories
  start     Start all services
  stop      Stop all services
  restart   Restart services
  status    Show containers
  logs      View logs (or: logs <service>)
  vpn       Check VPN is working
  clean     Remove containers (keeps data)
  reset     Full reset
""")


COMMANDS = {
    "setup": cmd_setup,
    "start": cmd_start,
    "stop": cmd_stop,
    "restart": cmd_restart,
    "status": cmd_status,
    "logs": cmd_logs,
    "vpn": cmd_vpn,
    "clean": cmd_clean,
    "reset": cmd_reset,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        show_help()
        sys.exit(0)

    cmd = sys.argv[1].lower().replace("_", "-")
    if cmd in COMMANDS:
        sys.exit(COMMANDS[cmd]() or 0)
    else:
        print(f"❌ Unknown: {cmd}")
        show_help()
        sys.exit(1)
