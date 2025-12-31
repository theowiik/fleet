# Media Server Stack

Self-hosted media automation with VPN-protected downloads.

- [What This Does](#what-this-does)
- [Requirements](#requirements)
- [Setup](#setup)
- [Access](#access)
- [Initial Configuration](#initial-configuration)
- [Verify VPN](#verify-vpn)
- [Management](#management)
- [Storage](#storage)
- [Security](#security)

## What This Does

- **Jellyfin**: Stream media
- **Jellyseerr**: Request content
- **Radarr/Sonarr**: Auto-download movies/TV
- **qBittorrent**: Torrents via VPN (leak-proof)
- **Prowlarr**: Indexer management
- **Bazarr**: Subtitles

## Requirements

- Ubuntu/Debian server
- Docker + Docker Compose
- Mullvad VPN account (~€5/month)

## Setup

```bash
# 1. Auto-detect and create config
make setup

# 2. Edit .env and add Mullvad credentials
nano .env

# 3. Start everything
make start
```

Get Mullvad credentials from: https://mullvad.net/en/account/wireguard-config

You need `PrivateKey` and `Address` from the [Interface] section.

## Access

- Jellyfin: `http://YOUR_IP:8096`
- Jellyseerr: `http://YOUR_IP:5055`
- Radarr: `http://YOUR_IP:7878`
- Sonarr: `http://YOUR_IP:8989`
- Prowlarr: `http://YOUR_IP:9696`
- qBittorrent: `http://YOUR_IP:8080` (admin/adminadmin)

## Initial Configuration

### 1. Prowlarr

- Add indexers
- Settings → Apps → Add Radarr and Sonarr

### 2. Radarr

- Settings → Download Clients → Add qBittorrent (host: `gluetun`, port: 8080)
- Settings → Media Management → Root: `/data/media/movies`, enable hardlinks

### 3. Sonarr

- Same as Radarr but root: `/data/media/tv`

### 4. qBittorrent

- Change password
- Default save path: `/data/torrents`

### 5. Jellyfin

- Add libraries: `/media/movies` and `/media/tv`
- Enable hardware transcoding (Intel QuickSync)

### 6. Jellyseerr

- Connect to Jellyfin, Radarr, Sonarr

## Verify VPN

```bash
docker exec qbittorrent curl -s ifconfig.me
```

Should show Mullvad IP, not your real IP.

## Management

```bash
make status      # Check status
make logs        # View logs
make restart     # Restart all
make stop        # Stop all
make start       # Start all
make validate    # Check config
make clean       # Remove containers
```

## Storage

Your `.env` has `DATA_ROOT` which can be:

- `./data` - relative to project (default)
- `/data` - absolute path
- `/mnt/external` - external drive

Structure:

```
DATA_ROOT/
├── torrents/    # Downloads
└── media/       # Organized (movies, tv)
```

## Security

- All torrent traffic through VPN (network isolation + kill switch)
- Local network only
- qBittorrent cannot bypass VPN
