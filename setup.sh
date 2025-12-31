#!/bin/bash
set -e

echo "============================================"
echo "  Media Server Setup"
echo "============================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Don't run this as root (no sudo)"
    echo "   Run: ./setup.sh"
    exit 1
fi

# Check Docker
echo "Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Install it first:"
    echo "   curl -fsSL https://get.docker.com | sh"
    echo "   sudo usermod -aG docker \$USER"
    echo "   Then log out and back in"
    exit 1
fi

if ! docker ps &> /dev/null; then
    echo "❌ Docker not running or permission denied"
    echo "   Make sure Docker is running and you're in the docker group"
    echo "   Run: sudo usermod -aG docker \$USER"
    echo "   Then log out and back in"
    exit 1
fi
echo "✓ Docker is ready"
echo ""

# Auto-detect system values
echo "Detecting system configuration..."
PUID=$(id -u)
PGID=$(id -g)
RENDER_GID=$(getent group render 2>/dev/null | cut -d: -f3 || echo "")
TZ=$(timedatectl 2>/dev/null | grep "Time zone" | awk '{print $3}' || echo "UTC")
LAN_SUBNET=$(ip route | grep default | awk '{print $3}' | sed 's/\.[0-9]*$/\.0\/24/' || echo "192.168.1.0/24")
SERVER_IP=$(hostname -I | awk '{print $1}')

echo "✓ User ID (PUID): $PUID"
echo "✓ Group ID (PGID): $PGID"
if [ -n "$RENDER_GID" ]; then
    echo "✓ Render Group (for GPU): $RENDER_GID"
else
    echo "⚠ Render group not found (GPU transcoding disabled)"
    RENDER_GID="0"
fi
echo "✓ Timezone: $TZ"
echo "✓ Network: $LAN_SUBNET"
echo "✓ Server IP: $SERVER_IP"
echo ""

# Create .env from template
if [ -f .env ]; then
    echo "⚠ .env already exists, skipping..."
else
    echo "Creating .env file..."
    cat > .env << EOF
# Auto-generated configuration - only edit the sections marked below

# ============ AUTO-DETECTED (don't change) ============
PUID=$PUID
PGID=$PGID
RENDER_GID=$RENDER_GID
TZ=$TZ
LAN_SUBNET=$LAN_SUBNET
VPN_PROVIDER=mullvad
VPN_TYPE=wireguard

# ============ STORAGE (change if needed) ============
# Where your media files will be stored
# Examples: ./data (relative), /data (absolute), /mnt/external (external drive)
DATA_ROOT=./data

# Where app configs are stored (leave default)
CONFIG_ROOT=./config

# ============ REQUIRED: MULLVAD VPN ============
# Get these from https://mullvad.net/en/account/wireguard-config
# 1. Login to Mullvad account
# 2. Go to "WireGuard configuration"
# 3. Click "Generate key"
# 4. Download the .conf file
# 5. Open it and copy these values from [Interface] section:

WIREGUARD_PRIVATE_KEY=CHANGE_ME
WIREGUARD_ADDRESSES=CHANGE_ME

# Optional: specific location (Stockholm, Amsterdam, etc.) or leave empty
VPN_SERVER_CITIES=
EOF
    echo "✓ Created .env file"
fi
echo ""

# Create directory structure
echo "Creating directories..."
DATA_ROOT=$(grep ^DATA_ROOT .env | cut -d= -f2)
if [ "$DATA_ROOT" = "/data" ]; then
    sudo mkdir -p /data/torrents/{movies,tv} 2>/dev/null || true
    sudo mkdir -p /data/media/{movies,tv} 2>/dev/null || true
    sudo chown -R $USER:$USER /data 2>/dev/null || true
    echo "✓ Created /data directories"
else
    mkdir -p $DATA_ROOT/torrents/{movies,tv}
    mkdir -p $DATA_ROOT/media/{movies,tv}
    echo "✓ Created $DATA_ROOT directories"
fi

mkdir -p config
echo "✓ Created config directory"
echo ""

# Make scripts executable
chmod +x manage.py 2>/dev/null || true
chmod +x start.sh 2>/dev/null || true
echo "✓ Made scripts executable"
echo ""

echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "NEXT STEPS:"
echo ""
echo "1. Edit .env file and add your Mullvad VPN credentials:"
echo "   nano .env"
echo ""
echo "   Change these lines:"
echo "   WIREGUARD_PRIVATE_KEY=CHANGE_ME"
echo "   WIREGUARD_ADDRESSES=CHANGE_ME"
echo ""
echo "2. Start the server:"
echo "   ./start.sh"
echo ""
echo "3. Access at http://$SERVER_IP:8096 (Jellyfin)"
echo ""
