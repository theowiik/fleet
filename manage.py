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
    compose("ps")
    return 0


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
