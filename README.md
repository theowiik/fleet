# Fleet

Self-hosted media server with VPN-protected downloads.

- [Setup](#setup)
- [Get Your VPN Keys](#get-your-vpn-keys)
- [Services](#services)
- [First-Time Service Setup](#first-time-service-setup)
  - [1. qBittorrent (:8080)](#1-qbittorrent-8080)
  - [2. Prowlarr (:9696)](#2-prowlarr-9696)
  - [3. Radarr (:7878) \& Sonarr (:8989)](#3-radarr-7878--sonarr-8989)
  - [4. Jellyfin (:8096)](#4-jellyfin-8096)
  - [5. Jellyseerr (:5055)](#5-jellyseerr-5055)
  - [6. Bazarr (:6767) — Optional](#6-bazarr-6767--optional)
  - [7. Recyclarr](#7-recyclarr)
  - [8. Decluttarr](#8-decluttarr)
- [Disclaimer](#disclaimer)

## Setup

Requirements:

- Docker Desktop
- Python 3.8+
- Mullvad VPN

```bash
# 1. Setup
python manage.py setup

# 2. Edit .env with your Mullvad VPN keys (see below)

# 3. See commands
python manage.py help

# 4. Start
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

## Services

| Service      | Port  | Purpose                              |
| ------------ | ----- | ------------------------------------ |
| Jellyfin     | :8096 | Watch your media                     |
| Jellyseerr   | :5055 | Request movies/shows                 |
| Radarr       | :7878 | Movie automation                     |
| Sonarr       | :8989 | TV automation                        |
| Prowlarr     | :9696 | Indexer management                   |
| FlareSolverr | :8191 | Cloudflare bypass (VPN protected)    |
| Bazarr       | :6767 | Subtitle automation                  |
| qBittorrent  | :8080 | Downloads (VPN protected)            |
| Recyclarr    | —     | Applies recommended quality settings |
| Decluttarr   | —     | Auto-removes stuck downloads         |

## First-Time Service Setup

Configure in this order (takes ~10 minutes):

### 1. qBittorrent (:8080)

Get your temporary password from the logs:

```bash
python manage.py logs qbittorrent
# Look for: "A temporary password is provided for this session: xxxxxxxx"
```

Login with `admin` + that password, then:

- **Settings → Web UI → Authentication:** Set a permanent password
- **Settings → Downloads → Default Save Path:** `/data/torrents`

### 2. Prowlarr (:9696)

- **Settings → General:** Note your API Key (needed for next steps)
- **Settings → Indexers → Add FlareSolverr:** For Cloudflare-protected indexers:
  - Tags: `flaresolverr`
  - Host: `http://fleet-gluetun:8191`
- **Indexers → Add:** Add your torrent indexers (1337x, RARBG, etc.)
  - For Cloudflare-protected sites, add tag: `flaresolverr`
- **Settings → Apps → Add:** Connect to Radarr and Sonarr:
  - Prowlarr Server: `http://fleet-prowlarr:9696`
  - Radarr/Sonarr Server: `http://fleet-radarr:7878` or `http://fleet-sonarr:8989`
  - API Key: Get from each app's Settings → General

### 3. Radarr (:7878) & Sonarr (:8989)

Both need the same setup:

- **Settings → Media Management → Root Folder:**
  - Radarr: `/data/media/movies`
  - Sonarr: `/data/media/tv`
- **Settings → Download Clients → Add qBittorrent:**
  - Host: `fleet-gluetun`
  - Port: `8080`
  - Username: `admin`
  - Password: (your qBittorrent password)

### 4. Jellyfin (:8096)

- Run through initial wizard
- **Add Media Library:**
  - Movies → `/media/movies`
  - Shows → `/media/tv`

### 5. Jellyseerr (:5055)

- Sign in with Jellyfin
- Connect to Radarr/Sonarr using their API keys
- Use internal URLs: `http://fleet-radarr:7878`, `http://fleet-sonarr:8989`

### 6. Bazarr (:6767) — Optional

Automatic subtitles. Connect to Radarr/Sonarr the same way.

### 7. Recyclarr

Applies recommended quality profiles from TRaSH Guides.

1. Copy API keys from Radarr/Sonarr (Settings → General) into `.env`
2. Run `python manage.py sync`
3. In Radarr/Sonarr: Settings → Indexers → set **Minimum Seeders** to `5`

### 8. Decluttarr

Automatically removes stuck/failed downloads. Runs continuously in the background.

1. Check it sees your queues: `python manage.py logs decluttarr`
2. Once verified, edit `decluttarr/config.yaml` and set `test_run: false`

## Disclaimer

For educational purposes only. Use responsibly.
