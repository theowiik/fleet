# Quick Start - 5 Minute Setup

If you already have Docker and Mullvad credentials, you can be running in 5 minutes.

## Prerequisites Check

```bash
# Docker installed and running?
docker --version
docker ps

# Get your system info
id              # Note your UID and GID
getent group render | cut -d: -f3    # Note render GID
hostname -I     # Note first IP address
```

## 1. Copy Files (30 seconds)

```bash
# Create directory
sudo mkdir -p /opt/media-server
sudo chown $USER:$USER /opt/media-server
cd /opt/media-server

# Copy all these files here:
# - docker-compose.yml
# - manage.py  
# - verify-vpn.sh
# - .env.example
```

## 2. Configure .env (2 minutes)

```bash
cp .env.example .env
nano .env
```

**Required changes:**

```bash
# Your user/group (from 'id' command)
PUID=1000
PGID=1000
RENDER_GID=122

# Your network (change to match your subnet)
LAN_SUBNET=192.168.1.0/24

# Storage paths
DATA_ROOT=/data              # Your external drive or media location
CONFIG_ROOT=/opt/media-server/config

# Mullvad (from MULLVAD_SETUP.md guide)
WIREGUARD_PRIVATE_KEY=your-actual-key-here=
WIREGUARD_ADDRESSES=10.x.x.x/32
VPN_SERVER_CITIES=Stockholm
```

Save and exit (Ctrl+X, Y, Enter)

## 3. Create Directories (10 seconds)

```bash
# Create data structure
sudo mkdir -p /data/torrents/{movies,tv}
sudo mkdir -p /data/media/{movies,tv}
sudo chown -R $USER:$USER /data

# Config directory
mkdir -p config
```

## 4. Validate (30 seconds)

```bash
chmod +x manage.py verify-vpn.sh
./manage.py validate
```

Fix any errors shown.

## 5. Start Stack (2 minutes)

```bash
./manage.py start
```

Wait for containers to start.

## 6. Verify VPN (30 seconds)

```bash
./verify-vpn.sh
```

Should show:
- ✓ Connected via Mullvad VPN
- ✓ All tests passed
- ✓ No leaks detected

## 7. Access Services

Open in browser:
```
http://YOUR_IP:8096   - Jellyfin (setup wizard)
http://YOUR_IP:5055   - Jellyseerr  
http://YOUR_IP:7878   - Radarr
http://YOUR_IP:8989   - Sonarr
http://YOUR_IP:9696   - Prowlarr
http://YOUR_IP:8080   - qBittorrent (admin/adminadmin)
```

Replace `YOUR_IP` with your server's IP (from `hostname -I`).

## 8. Basic Configuration (10 minutes)

See README.md section "Initial Setup" for complete configuration guide.

**Minimum viable setup:**

1. **Prowlarr**: Add 2-3 indexers
2. **Prowlarr**: Add Radarr and Sonarr as apps (syncs indexers)
3. **Radarr**: Add qBittorrent download client (host: `gluetun`)
4. **Sonarr**: Add qBittorrent download client (host: `gluetun`)
5. **qBittorrent**: Change password!
6. **Jellyfin**: Add libraries, enable hardware transcoding
7. **Jellyseerr**: Connect to Jellyfin, Radarr, Sonarr

## Done!

Search for a movie in Jellyseerr → Request → Watch it appear in Jellyfin.

## Ongoing Management

```bash
# Check everything is running
./manage.py status

# View logs
./manage.py logs

# Check VPN protection
./verify-vpn.sh

# Restart if needed
./manage.py restart
```

## If Something Breaks

1. Check logs: `./manage.py logs`
2. Verify VPN: `./verify-vpn.sh`
3. Re-validate: `./manage.py validate`
4. Restart: `./manage.py restart`

For detailed troubleshooting, see README.md "Troubleshooting" section.
