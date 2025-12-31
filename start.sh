#!/bin/bash
set -e

echo "============================================"
echo "  Media Server Startup"
echo "============================================"
echo ""

# Check .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found"
    echo "   Run ./setup.sh first"
    exit 1
fi

# Check if VPN credentials are set
if grep -q "WIREGUARD_PRIVATE_KEY=CHANGE_ME" .env; then
    echo "❌ Mullvad VPN not configured!"
    echo ""
    echo "Edit .env and add your Mullvad credentials:"
    echo "  nano .env"
    echo ""
    echo "Get credentials from:"
    echo "  https://mullvad.net/en/account/wireguard-config"
    exit 1
fi

if grep -q "WIREGUARD_ADDRESSES=CHANGE_ME" .env; then
    echo "❌ Mullvad VPN address not configured!"
    echo ""
    echo "Edit .env and add your WIREGUARD_ADDRESSES:"
    echo "  nano .env"
    exit 1
fi

echo "Validating configuration..."
./manage.py validate || exit 1
echo ""

echo "Starting services..."
docker compose pull
docker compose up -d
echo ""

echo "Waiting for services to start..."
sleep 5
echo ""

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

echo "============================================"
echo "  Services Started!"
echo "============================================"
echo ""
echo "Access your services at:"
echo ""
echo "  Jellyfin:    http://$SERVER_IP:8096"
echo "  Jellyseerr:  http://$SERVER_IP:5055"
echo "  Radarr:      http://$SERVER_IP:7878"
echo "  Sonarr:      http://$SERVER_IP:8989"
echo "  Prowlarr:    http://$SERVER_IP:9696"
echo "  qBittorrent: http://$SERVER_IP:8080 (admin/adminadmin)"
echo ""
echo "IMPORTANT: Verify VPN protection:"
echo "  docker exec qbittorrent curl -s ifconfig.me"
echo ""
echo "This should show a Mullvad IP, NOT your real IP!"
echo ""
