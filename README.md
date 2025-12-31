# Fleet

Self-hosted media server with VPN-protected downloads.

- [Setup](#setup)
- [Get Your VPN Keys](#get-your-vpn-keys)
- [Commands](#commands)
- [Services](#services)
- [First-Time Service Setup](#first-time-service-setup)
- [Requirements](#requirements)

## Setup

```bash
# 1. Setup
python manage.py setup

# 2. Edit .env with your Mullvad VPN keys (see below)

# 3. Start
python manage.py start
```

## Get Your VPN Keys

1. Go to https://mullvad.net/en/account/wireguard-config
2. Set these settings: ![Mullvad Wireguard Settings](mullvad_wireguard.png)
3. Generate a key → Download the `.conf` file
4. Open it and copy these values to your `.env`:

```
[Interface]
PrivateKey = abc123...   ← WIREGUARD_PRIVATE_KEY
Address = 10.x.x.x/32    ← WIREGUARD_ADDRESSES
```

## Commands

| Command                   | What it does          |
| ------------------------- | --------------------- |
| `python manage.py setup`  | First-time setup      |
| `python manage.py start`  | Start everything      |
| `python manage.py stop`   | Stop everything       |
| `python manage.py status` | Show what's running   |
| `python manage.py vpn`    | Verify VPN is working |
| `python manage.py logs`   | View logs             |
| `python manage.py reset`  | Start fresh           |

## Services

| Service     | URL   | Purpose                   |
| ----------- | ----- | ------------------------- |
| Jellyfin    | :8096 | Watch your media          |
| Jellyseerr  | :5055 | Request movies/shows      |
| Radarr      | :7878 | Movie automation          |
| Sonarr      | :8989 | TV automation             |
| Prowlarr    | :9696 | Indexer management        |
| qBittorrent | :8080 | Downloads (VPN protected) |

**qBittorrent default login:** admin / adminadmin (change this!)

## First-Time Service Setup

After starting, configure each service:

**Prowlarr** → Add indexers, then connect to Radarr/Sonarr

**Radarr/Sonarr** → Add qBittorrent as download client:

- Host: `fleet-gluetun`
- Port: `8080`

**Jellyfin** → Add libraries from `/media/movies` and `/media/tv`

## Requirements

- Docker Desktop
- Python 3.8+
- Mullvad VPN (~€5/month)
