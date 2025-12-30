# Media Server Stack - Complete Package

## What You're Getting

A **production-ready, .env-based media server stack** with:

- ✅ All configuration in `.env` file
- ✅ Python validation script with safety checks
- ✅ VPN kill switch with zero-leak guarantee (Mullvad)
- ✅ Local network access only (no remote setup yet)
- ✅ Complete automation (search → download → organize → stream)
- ✅ Intel QuickSync hardware transcoding
- ✅ Easy migration (laptop → NUC → NAS)

## Files Included

### Core Configuration

- **`docker-compose.yml`** - Complete stack definition (all values from .env)
- **`.env.example`** - Template with all configurable options
- **`manage.py`** - Python management script with validation

### Documentation

- **`README.md`** - Comprehensive guide (setup, usage, troubleshooting)
- **`QUICKSTART.md`** - 5-minute setup for experienced users
- **`MULLVAD_SETUP.md`** - Step-by-step Mullvad configuration guide

### Tools

- **`verify-vpn.sh`** - VPN leak detection script (run anytime)

## What's Special About This Setup

### 1. Everything in .env

**NO editing docker-compose.yml when migrating!**

```bash
# Moving from laptop to NUC?
# Just change these two lines in .env:
DATA_ROOT=/new/path
CONFIG_ROOT=/new/path
```

### 2. Validation Before Start

The Python script checks EVERYTHING:

- ✅ All required variables set
- ✅ Mullvad config format valid
- ✅ Directories exist and writable
- ✅ Docker running
- ✅ Intel GPU available
- ✅ Network subnet valid

### 3. VPN Protection Guaranteed

```
qBittorrent uses: network_mode: "service:gluetun"
                          ↓
    ALL traffic MUST go through Gluetun VPN
                          ↓
         Cannot bypass even if VPN fails
                          ↓
              Kill switch at kernel level
```

### 4. Simple Management

```bash
./manage.py validate   # Check config
./manage.py start      # Start everything
./manage.py stop       # Stop everything
./manage.py logs       # View logs
./manage.py status     # Check status
./verify-vpn.sh        # Test VPN protection
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR COMPUTER                        │
│                                                         │
│   Browser → http://SERVER_IP:8096 → Jellyfin           │
│   Browser → http://SERVER_IP:5055 → Jellyseerr         │
│                                                         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   DOCKER HOST                           │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Jellyseerr (Family requests content)            │  │
│  └────────────────────┬─────────────────────────────┘  │
│                       ↓                                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Radarr / Sonarr (Automation)                    │  │
│  └────────────────────┬─────────────────────────────┘  │
│                       ↓                                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Prowlarr (Indexer Manager)                      │  │
│  └────────────────────┬─────────────────────────────┘  │
│                       ↓                                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │  Gluetun VPN (Mullvad WireGuard)           │  │  │
│  │  │  - iptables kill switch                    │  │  │
│  │  │  - Blocks ALL traffic without VPN          │  │  │
│  │  └─────────────────┬──────────────────────────┘  │  │
│  │                    ↓                              │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │  qBittorrent (Downloads)                   │  │  │
│  │  │  network_mode: service:gluetun             │  │  │
│  │  │  → CANNOT access internet without VPN      │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
│                       ↓                                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Storage: /data/                                 │  │
│  │  ├── torrents/  (downloads)                      │  │
│  │  └── media/     (organized content)              │  │
│  └──────────────────────────────────────────────────┘  │
│                       ↓                                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Jellyfin (Streams to family)                    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Security Model

### What's Protected

✅ **qBittorrent traffic**: 100% through VPN, kill switch enforced
✅ **Downloads**: Isolated from internet access
✅ **Admin interfaces**: Only accessible on local network

### What's NOT Protected (Yet)

❌ **No remote access** - local network only
❌ **No HTTPS** - plain HTTP on LAN
❌ **No authentication layer** - services unprotected on LAN
❌ **No firewall rules** - Docker manages networking

**These are features for later when you add remote access!**

## Migration Path

### Phase 1: Local Setup (You Are Here)

- Laptop or NUC on local network
- Local storage or external drive
- Family accesses on same WiFi

### Phase 2: Remote Access (Future)

Add to this stack:

- Tailscale for secure remote access
- Caddy for HTTPS reverse proxy
- Let's Encrypt SSL certificates

### Phase 3: Production Hardening (Future)

Add to this stack:

- Authelia for 2FA authentication
- Fail2ban for brute force protection
- UFW firewall rules
- Backup automation

**The beauty: You can add these WITHOUT changing the core stack!**

## Quick Start Path

### For Experienced Users (5 minutes)

1. Copy files to `/opt/media-server`
2. Edit `.env` (see QUICKSTART.md)
3. Run `./manage.py start`
4. Run `./verify-vpn.sh`

### For Everyone Else (30 minutes)

1. Read `README.md` completely
2. Follow `MULLVAD_SETUP.md` for VPN credentials
3. Follow "Initial Setup" section in README
4. Configure each service web interface

## Cost Breakdown

**Required:**

- Mullvad VPN: €5/month (~$5.50 USD)
- Hardware: Use existing laptop/PC/NUC

**Optional:**

- Domain name: $10-15/year (only if adding remote access)
- NAS storage: $200-500 one-time (optional, not required)

**Compare to streaming services:**

- Netflix + Disney+ + HBO Max = $42.47/month
- This setup = $5.50/month

**Savings: $37/month = $444/year**

## What Happens When You Run It

1. **You request content in Jellyseerr**
   - Search: "Dune Part Two"
   - Click: "Request Movie"

2. **Radarr receives request**
   - Searches Prowlarr indexers
   - Finds best quality torrent
   - Sends to qBittorrent

3. **qBittorrent downloads via VPN**
   - ALL traffic through Mullvad
   - Download completes to `/data/torrents/movies/`
   - No data leaks possible

4. **Radarr organizes**
   - Moves file to `/data/media/movies/`
   - Renames: `Movie Name (2024).mkv`
   - Creates hardlink (saves space)
   - Notifies Jellyfin

5. **Jellyfin updates library**
   - Scans new movie
   - Downloads metadata/posters
   - Ready to stream

6. **You get notification**
   - "Dune Part Two is now available"
   - Open Jellyfin
   - Start watching

**Total time: 10-30 minutes depending on torrent speed**

## Important Notes

### VPN Protection

- qBittorrent CANNOT bypass VPN due to Docker networking
- Kill switch is at kernel level (iptables)
- Run `./verify-vpn.sh` anytime to verify
- Even if Gluetun crashes, qBittorrent loses ALL network

### Storage Management

- Use hardlinks to save 50% space
- Single `/data` root enables this
- Monitor disk usage regularly
- Consider NAS when storage fills

### Family Access

- Give them Jellyfin URL only
- Give them Jellyseerr URL to request content
- Do NOT give them admin interface URLs
- Everything else happens automatically

### Performance

- 4GB RAM minimum for Jellyfin
- 8GB+ recommended for large libraries
- Intel QuickSync handles 4-5 simultaneous transcodes
- SSD for CONFIG_ROOT improves responsiveness

## Next Steps After Setup

1. **Test everything locally first**
   - Request test movie
   - Verify download works
   - Confirm Jellyfin streams
   - Run VPN tests

2. **Add content gradually**
   - Start with favorites
   - Build library over time
   - Monitor disk space

3. **When ready for remote access**
   - Keep this issue/conversation
   - Ask about Tailscale + Caddy setup
   - We'll extend the existing stack

4. **Backup your .env file**
   - Contains all your config
   - Keep secure copy
   - Don't commit to Git

## Support Resources

### Included Documentation

- `README.md` - Complete guide
- `QUICKSTART.md` - Fast setup
- `MULLVAD_SETUP.md` - VPN credentials
- Comments in `.env.example` - All options explained
- Comments in `docker-compose.yml` - Architecture explained

### Built-in Tools

- `manage.py validate` - Check configuration
- `manage.py logs` - Debug issues
- `verify-vpn.sh` - Test VPN protection

### External Resources

- Jellyfin docs: https://jellyfin.org/docs/
- Radarr docs: https://wiki.servarr.com/radarr
- Sonarr docs: https://wiki.servarr.com/sonarr
- TRaSH Guides: https://trash-guides.info/
- Mullvad: https://mullvad.net/help/

## File Checksums

For verification, here are the file sizes:

```
13K   media-server-stack.tar.gz
2.2K  .env.example
9.8K  docker-compose.yml
14K   manage.py
3.0K  verify-vpn.sh
11K   README.md
3.2K  MULLVAD_SETUP.md
2.8K  QUICKSTART.md
```

## License & Responsibility

This stack uses:

- Open source software (Jellyfin, \*arr stack)
- Docker (commercially supported)
- Your own Mullvad subscription

**You are responsible for:**

- Legal use of indexers/content
- Keeping software updated
- Securing your network
- Complying with local laws

**This is infrastructure - content sourcing is your responsibility.**

---

**Ready to start?** Extract the archive and see `QUICKSTART.md` or `README.md`!
