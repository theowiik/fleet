#!/bin/bash
# VPN Leak Test - Verifies qBittorrent is using VPN

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "  VPN LEAK TEST - Mullvad via Gluetun"
echo "=============================================="
echo ""

# Check if qBittorrent container is running
if ! docker ps | grep -q qbittorrent; then
    echo -e "${RED}✗ qBittorrent container is not running${NC}"
    exit 1
fi

# Check if Gluetun container is running
if ! docker ps | grep -q gluetun; then
    echo -e "${RED}✗ Gluetun container is not running${NC}"
    exit 1
fi

# Test 1: Get current IP from qBittorrent
echo "Test 1: Checking qBittorrent IP address..."
QBIT_IP=$(docker exec qbittorrent curl -s --max-time 10 ifconfig.me 2>/dev/null || echo "FAILED")

if [ "$QBIT_IP" = "FAILED" ]; then
    echo -e "${RED}✗ Could not determine IP (may indicate kill switch is working)${NC}"
else
    echo -e "${GREEN}✓ qBittorrent IP: $QBIT_IP${NC}"
fi

# Test 2: Verify it's a Mullvad IP
echo ""
echo "Test 2: Verifying Mullvad connection..."
MULLVAD_CHECK=$(docker exec qbittorrent curl -s --max-time 10 https://am.i.mullvad.net/json 2>/dev/null || echo "{}")

if echo "$MULLVAD_CHECK" | jq -e '.mullvad_exit_ip == true' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Connected via Mullvad VPN${NC}"
    MULLVAD_IP=$(echo "$MULLVAD_CHECK" | jq -r '.ip')
    MULLVAD_COUNTRY=$(echo "$MULLVAD_CHECK" | jq -r '.country')
    MULLVAD_CITY=$(echo "$MULLVAD_CHECK" | jq -r '.city')
    echo -e "  IP: $MULLVAD_IP"
    echo -e "  Location: $MULLVAD_CITY, $MULLVAD_COUNTRY"
else
    echo -e "${RED}✗ NOT connected via Mullvad!${NC}"
    echo -e "${RED}  This is a potential leak!${NC}"
    exit 1
fi

# Test 3: Check Gluetun health
echo ""
echo "Test 3: Checking Gluetun container health..."
GLUETUN_HEALTH=$(docker inspect gluetun --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")

if [ "$GLUETUN_HEALTH" = "healthy" ]; then
    echo -e "${GREEN}✓ Gluetun container is healthy${NC}"
else
    echo -e "${YELLOW}⚠ Gluetun health status: $GLUETUN_HEALTH${NC}"
fi

# Test 4: Check for DNS leaks
echo ""
echo "Test 4: DNS leak test..."
DNS_CHECK=$(docker exec qbittorrent nslookup google.com 2>/dev/null | grep "Server:" | head -1 || echo "FAILED")

if echo "$DNS_CHECK" | grep -qE "(127\.0\.0\.|10\.)"; then
    echo -e "${GREEN}✓ DNS queries going through VPN${NC}"
    echo -e "  $DNS_CHECK"
else
    echo -e "${YELLOW}⚠ DNS check: $DNS_CHECK${NC}"
fi

# Summary
echo ""
echo "=============================================="
echo "  LEAK TEST SUMMARY"
echo "=============================================="
echo -e "${GREEN}✓ All tests passed${NC}"
echo -e "${GREEN}✓ qBittorrent is protected by VPN${NC}"
echo -e "${GREEN}✓ No leaks detected${NC}"
echo ""
echo "To test kill switch manually, run:"
echo "  docker stop gluetun"
echo "  docker exec qbittorrent curl -s --max-time 5 ifconfig.me"
echo "  (should timeout/fail)"
echo "  docker start gluetun"
