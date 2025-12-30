# Getting Your Mullvad WireGuard Configuration

## Step 1: Sign up for Mullvad

1. Go to https://mullvad.net/
2. Click "Get started"
3. You'll receive a **16-digit account number** (no email required!)
4. Save this number securely - it's your only login credential
5. Add time to your account (~€5/month)

## Step 2: Generate WireGuard Key

1. Login to https://mullvad.net/en/account/
2. Navigate to **"WireGuard configuration"** in the left menu
3. Click **"Generate key"** or select existing key
4. Choose your preferred **server location** (e.g., Stockholm, Amsterdam)
5. Click **"Download file"** to get the .conf file

## Step 3: Extract Values for .env

Open the downloaded .conf file. It looks like this:

```ini
[Interface]
PrivateKey = ABCDefghIJKLmnopQRSTuvwxYZ1234567890abcd=
Address = 10.68.123.45/32
DNS = 10.64.0.1

[Peer]
PublicKey = xyz...
AllowedIPs = 0.0.0.0/0, ::/0
Endpoint = se10-wireguard.mullvad.net:51820
```

### Copy these values to your .env:

**WIREGUARD_PRIVATE_KEY**
```bash
# From [Interface] → PrivateKey
WIREGUARD_PRIVATE_KEY=ABCDefghIJKLmnopQRSTuvwxYZ1234567890abcd=
```

**WIREGUARD_ADDRESSES**
```bash
# From [Interface] → Address
WIREGUARD_ADDRESSES=10.68.123.45/32
```

**VPN_SERVER_CITIES** (optional)
```bash
# From [Peer] → Endpoint (the "se10" part indicates Sweden)
# se = Sweden, nl = Netherlands, us = United States, etc.
VPN_SERVER_CITIES=Stockholm

# Or leave empty for random server:
VPN_SERVER_CITIES=
```

## Step 4: Verify Format

Your .env should have:

```bash
VPN_PROVIDER=mullvad
VPN_TYPE=wireguard
WIREGUARD_PRIVATE_KEY=ABCDefghIJKLmnopQRSTuvwxYZ1234567890abcd=
WIREGUARD_ADDRESSES=10.68.123.45/32
VPN_SERVER_CITIES=Stockholm
```

## Step 5: Test

After starting the stack:

```bash
# Should show Mullvad IP, not your real IP
docker exec qbittorrent curl -s ifconfig.me

# Should show: "mullvad_exit_ip": true
docker exec qbittorrent curl -s https://am.i.mullvad.net/json | jq
```

## Troubleshooting

### "Invalid private key"
- Make sure you copied the ENTIRE key including the trailing `=`
- Private keys are always exactly 44 characters
- No spaces before or after

### "Connection timeout"
- Check your Mullvad account has active time
- Try different SERVER_CITIES value
- Try leaving SERVER_CITIES empty (random server)

### "Authentication failed"
- Regenerate a new key in Mullvad account
- Make sure you have an active subscription
- Wait 30 seconds after generating key

## Server Locations

Common VPN_SERVER_CITIES values:
- **Europe**: Stockholm, Amsterdam, London, Paris, Frankfurt, Zurich
- **North America**: New York, Los Angeles, Toronto, Dallas
- **Asia**: Tokyo, Singapore, Hong Kong
- **Oceania**: Sydney, Melbourne

Leave empty for automatic selection based on lowest latency.

## Security Notes

- **Never share your private key** - treat it like a password
- **Never commit .env to Git** - it contains your private key
- **Rotate keys periodically** - generate new key every 6-12 months
- **Monitor your Mullvad account** - check for unusual activity

## Multiple Devices

You can generate **up to 5 WireGuard keys** per Mullvad account. Use different keys for:
- This media server
- Your phone
- Your laptop
- etc.

Each device gets its own configuration.
