# Media Server Stack - Local Setup

Complete self-hosted media automation with **mandatory VPN protection** for all torrent traffic. Zero tolerance for leaks.

## What This Does

- **Jellyfin**: Stream your media (Netflix-like interface)
- **Jellyseerr**: Family members search and request content
- **Radarr**: Automatically downloads movies
- **Sonarr**: Automatically downloads TV shows
- **Prowlarr**: Manages torrent indexers
- **Bazarr**: Downloads subtitles
- **qBittorrent**: Downloads torrents **via VPN only**
- **Gluetun**: VPN container with kill switch (Mullvad)

## Security Architecture

```
Family searches in Jellyseerr
         ↓
Request sent to Radarr/Sonarr
         ↓
Prowlarr finds torrent
         ↓
qBittorrent downloads ──→ ALL TRAFFIC THROUGH VPN
         ↓                 (Gluetun + Mullvad)
Radarr/Sonarr organize
         ↓
Jellyfin streams to family
```

**Critical**: qBittorrent uses `network_mode: service:gluetun` - it is physically impossible for it to bypass the VPN.

## Prerequisites

### 1. Ubuntu Server installed

Any recent Ubuntu Server (20.04+, 22.04, 24.04)

### 2. Docker installed

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in
```

### 3. Mullvad account

- Sign up: https://mullvad.net/
- Cost: ~€5/month
- Generate WireGuard config: https://mullvad.net/en/account/wireguard-config

### 4. Storage setup

You need two directories:

- **DATA_ROOT**: Your media files (movies, TV, torrents) - can be external drive
- **CONFIG_ROOT**: Application configs and databases - should be fast (SSD)

## Quick Start

### Step 1: Download this stack

```bash
# Clone or download these files to your server
cd /opt
sudo mkdir media-server
sudo chown $USER:$USER media-server
cd media-server

# Copy these files here:
# - docker-compose.yml
# - manage.py
# - .env.example
```

### Step 2: Create your .env file

```bash
cp .env.example .env
nano .env
```

Fill in these **required** values:

```bash
# System (run 'id' to get these)
PUID=1000                    # Your user ID
PGID=1000                    # Your group ID
RENDER_GID=122               # Run: getent group render | cut -d: -f3

# Network (your local subnet)
LAN_SUBNET=192.168.1.0/24    # Change to match your network

# Storage
DATA_ROOT=/mnt/external      # Where media files go
CONFIG_ROOT=/opt/media-server/config  # Where configs go

# Mullvad (from wireguard config)
WIREGUARD_PRIVATE_KEY=abc123...  # From [Interface] section
WIREGUARD_ADDRESSES=10.x.x.x/32  # From [Interface] section
VPN_SERVER_CITIES=Stockholm       # Or your preferred location
```

### Step 3: Validate configuration

```bash
./manage.py validate
```

This checks:

- All required variables are set
- Mullvad config is valid format
- Directories exist and are writable
- Docker is running
- Intel GPU is available (for transcoding)

Fix any errors before proceeding.

### Step 4: Start the stack

```bash
./manage.py start
```

This will:

1. Re-run validation
2. Pull all Docker images
3. Start all containers
4. Show access URLs

## Verifying VPN Protection

**CRITICAL**: Always verify torrents go through VPN!

### Test 1: Check qBittorrent IP

```bash
docker exec qbittorrent curl -s ifconfig.me
```

**Expected**: Shows Mullvad IP (NOT your home IP)

### Test 2: Mullvad connection check

```bash
docker exec qbittorrent curl -s https://am.i.mullvad.net/json | jq
```

**Expected**: `"mullvad_exit_ip": true`

### Test 3: Kill switch test

```bash
# Stop VPN
docker stop gluetun

# Try to reach internet from qBittorrent
docker exec qbittorrent curl -s --max-time 5 ifconfig.me
```

**Expected**: TIMEOUT (no connection = kill switch works)

```bash
# Restart VPN
docker start gluetun
```

### Test 4: Torrent IP check

1. Visit: https://torguard.net/checkmytorrentipaddress.php
2. Copy the magnet link
3. Add to qBittorrent
4. Check IP shown on TorGuard site
5. **Expected**: Mullvad IP, not your home IP

## Initial Setup

After starting, configure each service:

### 1. Jellyfin (http://YOUR_IP:8096)

- Complete setup wizard
- Create admin account
- Add libraries:
  - Movies: `/media/movies`
  - TV Shows: `/media/tv`
- Enable hardware transcoding:
  - Dashboard → Playback → Transcoding
  - Hardware acceleration: Intel QuickSync (QSV)
  - Enable: H.264, HEVC, VP9
  - Enable VPP tone mapping

### 2. Prowlarr (http://YOUR_IP:9696)

- Add indexers (torrent sites)
- Common ones: 1337x, RARBG alternatives, YTS
- Settings → Apps → Add Radarr and Sonarr
- This syncs indexers automatically

### 3. Radarr (http://YOUR_IP:7878)

- Settings → Media Management:
  - Root Folder: `/data/media/movies`
  - Enable "Use Hardlinks"
- Settings → Download Clients:
  - Add qBittorrent
  - Host: `gluetun` (not localhost!)
  - Port: `8080`
  - Category: `radarr`
- Settings → Connect:
  - Add Jellyfin notification
  - URL: `http://jellyfin:8096`
  - API Key: (from Jellyfin Dashboard → API Keys)

### 4. Sonarr (http://YOUR_IP:8989)

- Same setup as Radarr but:
  - Root Folder: `/data/media/tv`
  - qBittorrent Category: `sonarr`

### 5. qBittorrent (http://YOUR_IP:8080)

- Default login: `admin` / `adminadmin`
- **Change password immediately!**
- Settings → Downloads:
  - Default Save Path: `/data/torrents`
- Settings → Categories:
  - Add `radarr`: `/data/torrents/movies`
  - Add `sonarr`: `/data/torrents/tv`

### 6. Jellyseerr (http://YOUR_IP:5055)

- Use Jellyfin account to login
- Connect to Jellyfin: `http://jellyfin:8096`
- Add Radarr: `http://radarr:7878`
- Add Sonarr: `http://sonarr:8989`
- Enable notifications (email/Discord/etc)

### 7. Bazarr (http://YOUR_IP:6767)

- Languages → Add your languages
- Providers → Add subtitle providers
- Sonarr → Add Sonarr instance
- Radarr → Add Radarr instance

## Directory Structure

Your storage should look like:

```
DATA_ROOT/
├── torrents/           # qBittorrent downloads here
│   ├── movies/
│   └── tv/
└── media/              # Radarr/Sonarr organize here
    ├── movies/
    │   └── Movie Name (2024)/
    │       └── Movie Name (2024).mkv
    └── tv/
        └── Show Name/
            └── Season 01/
                └── Show S01E01.mkv

CONFIG_ROOT/
├── jellyfin/
├── radarr/
├── sonarr/
├── prowlarr/
├── qbittorrent/
├── jellyseerr/
├── bazarr/
└── gluetun/
```

**Why this structure?**

- Single root (`/data`) enables **hardlinks**
- Hardlinks save 50% disk space (file appears in two places, stored once)
- Radarr/Sonarr do instant moves instead of slow copies

## Management Commands

```bash
# Validate configuration
./manage.py validate

# Start all services
./manage.py start

# Stop all services
./manage.py stop

# Restart everything
./manage.py restart

# View logs (all services)
./manage.py logs

# View logs (specific service)
./manage.py logs jellyfin
./manage.py logs gluetun
./manage.py logs qbittorrent

# Check status
./manage.py status

# Stop and remove containers (keeps data)
./manage.py down
```

## Migrating to NUC

When moving from laptop to NUC:

### Option A: Move external drive

```bash
# On laptop
./manage.py stop
# Unplug drive, plug into NUC

# On NUC
# 1. Install Docker
# 2. Copy these files (docker-compose.yml, manage.py, .env)
# 3. Update .env if drive mount point changed
# 4. Copy CONFIG_ROOT backup if you want settings
./manage.py start
```

### Option B: Network transfer

```bash
# On laptop
./manage.py stop
rsync -avhP /data/ user@nuc:/data/
rsync -avhP /docker/appdata/ user@nuc:/docker/appdata/

# On NUC
./manage.py start
```

Your .env file makes this easy - just change paths if needed.

## Troubleshooting

### qBittorrent not accessible

```bash
# Check if Gluetun is healthy
docker ps
# Look for "healthy" status on gluetun

# Check Gluetun logs
./manage.py logs gluetun
```

### VPN not connecting

```bash
# Check Mullvad credentials
./manage.py logs gluetun | grep -i error

# Common issues:
# - Wrong WIREGUARD_PRIVATE_KEY
# - Wrong WIREGUARD_ADDRESSES format
# - Expired Mullvad account
```

### Jellyfin won't transcode

```bash
# Check GPU devices exist
ls -la /dev/dri/

# Check render group
getent group render

# Verify RENDER_GID in .env matches
```

### Downloads not appearing in Jellyfin

```bash
# Check Radarr/Sonarr logs
./manage.py logs radarr
./manage.py logs sonarr

# Verify Jellyfin notification is working
# Settings → Connect → Test button
```

### Containers keep restarting

```bash
# Check for permission issues
ls -la /data
ls -la /docker/appdata

# Should be owned by your user (PUID:PGID)
```

## Family Usage

1. **To stream existing content:**
   - Open Jellyfin in browser or TV app
   - Browse and play

2. **To request new content:**
   - Open Jellyseerr in browser
   - Search for movie/show
   - Click "Request"
   - Get notification when ready (~10-30 min)
   - Content appears in Jellyfin

## Access URLs (Local Network Only)

After starting, access services at:

- Jellyfin: http://YOUR_IP:8096
- Jellyseerr: http://YOUR_IP:5055
- Radarr: http://YOUR_IP:7878
- Sonarr: http://YOUR_IP:8989
- Prowlarr: http://YOUR_IP:9696
- Bazarr: http://YOUR_IP:6767
- qBittorrent: http://YOUR_IP:8080

Replace `YOUR_IP` with your server's local IP (run `hostname -I`).

## What's NOT Included (Yet)

This setup is **local network only**. Not included:

- Remote access (Tailscale/VPN)
- Reverse proxy (Caddy/Nginx)
- HTTPS/SSL certificates
- Authentication layer
- External domain access

Add these later when needed for family remote access.

## Cost Breakdown

- **Mullvad VPN**: €5/month (~$5.50)
- **Everything else**: FREE

Compare to:

- Netflix: $15.49/month
- Disney+: $10.99/month
- HBO Max: $15.99/month
- **Total**: $42.47/month vs $5.50/month

## Important Notes

1. **VPN is mandatory** - qBittorrent CANNOT bypass it due to network configuration
2. **Change qBittorrent password** immediately after first login
3. **Backup your .env file** - it contains all your config
4. **Monitor disk space** - media fills up fast
5. **Use legal indexers** - this stack is tool-agnostic about content sources

## Support

Run into issues?

```bash
# Full system check
./manage.py validate

# Check all container logs
./manage.py logs

# Verify VPN
docker exec qbittorrent curl -s ifconfig.me
```
