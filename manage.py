#!/usr/bin/env python3
"""
Media Server Stack Manager
Validates configuration and manages Docker Compose stack
"""

import os
import sys
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Tuple

# ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

def print_header(text: str):
    """Print colored header"""
    print(f"\n{BOLD}{BLUE}{'=' * 70}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(70)}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 70}{RESET}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text: str):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠ {text}{RESET}")

def print_info(text: str):
    """Print info message"""
    print(f"{BLUE}ℹ {text}{RESET}")

def load_env() -> Dict[str, str]:
    """Load .env file into dictionary"""
    env_path = Path('.env')
    
    if not env_path.exists():
        print_error(".env file not found!")
        print_info("Copy .env.example to .env and fill in your values:")
        print_info("  cp .env.example .env")
        sys.exit(1)
    
    env_vars = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    return env_vars

def validate_required_vars(env_vars: Dict[str, str]) -> List[str]:
    """Check all required variables are set"""
    required = [
        'PUID', 'PGID', 'RENDER_GID', 'TZ',
        'LAN_SUBNET', 'DATA_ROOT', 'CONFIG_ROOT',
        'WIREGUARD_PRIVATE_KEY', 'WIREGUARD_ADDRESSES',
        'VPN_PROVIDER', 'VPN_TYPE'
    ]
    
    missing = []
    for var in required:
        value = env_vars.get(var, '').strip()
        if not value or value.endswith('-here') or value.startswith('your-'):
            missing.append(var)
    
    return missing

def validate_paths(env_vars: Dict[str, str]) -> List[Tuple[str, str]]:
    """Validate directory paths exist and are writable"""
    issues = []
    
    data_root = Path(env_vars.get('DATA_ROOT', ''))
    config_root = Path(env_vars.get('CONFIG_ROOT', ''))
    
    # Check DATA_ROOT
    if not data_root.exists():
        issues.append(('DATA_ROOT', f'Directory does not exist: {data_root}'))
    elif not os.access(data_root, os.W_OK):
        issues.append(('DATA_ROOT', f'Directory not writable: {data_root}'))
    else:
        # Check subdirectories
        for subdir in ['torrents', 'media']:
            subpath = data_root / subdir
            if not subpath.exists():
                print_warning(f"Creating directory: {subpath}")
                try:
                    subpath.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    issues.append((f'DATA_ROOT/{subdir}', str(e)))
    
    # Check CONFIG_ROOT
    if not config_root.exists():
        print_warning(f"Creating directory: {config_root}")
        try:
            config_root.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            issues.append(('CONFIG_ROOT', str(e)))
    elif not os.access(config_root, os.W_OK):
        issues.append(('CONFIG_ROOT', f'Directory not writable: {config_root}'))
    
    return issues

def validate_mullvad_config(env_vars: Dict[str, str]) -> List[str]:
    """Validate Mullvad WireGuard configuration"""
    issues = []
    
    # Check private key format (base64, 44 characters)
    private_key = env_vars.get('WIREGUARD_PRIVATE_KEY', '')
    if len(private_key) != 44 or not re.match(r'^[A-Za-z0-9+/]{43}=$', private_key):
        issues.append('WIREGUARD_PRIVATE_KEY: Invalid format (should be 44 characters base64)')
    
    # Check addresses format (10.x.x.x/32)
    addresses = env_vars.get('WIREGUARD_ADDRESSES', '')
    if not re.match(r'^10\.\d{1,3}\.\d{1,3}\.\d{1,3}/32$', addresses):
        issues.append('WIREGUARD_ADDRESSES: Invalid format (should be 10.x.x.x/32)')
    
    # Check VPN provider
    if env_vars.get('VPN_PROVIDER', '').lower() != 'mullvad':
        issues.append('VPN_PROVIDER: Should be "mullvad"')
    
    # Check VPN type
    if env_vars.get('VPN_TYPE', '').lower() != 'wireguard':
        issues.append('VPN_TYPE: Should be "wireguard"')
    
    return issues

def validate_network(env_vars: Dict[str, str]) -> List[str]:
    """Validate network configuration"""
    issues = []
    
    # Check LAN subnet format
    lan_subnet = env_vars.get('LAN_SUBNET', '')
    if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$', lan_subnet):
        issues.append('LAN_SUBNET: Invalid format (should be x.x.x.x/xx, e.g., 192.168.1.0/24)')
    
    return issues

def check_docker() -> bool:
    """Check if Docker is installed and running"""
    try:
        result = subprocess.run(['docker', 'info'], 
                              capture_output=True, 
                              timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def check_intel_gpu() -> Tuple[bool, str]:
    """Check if Intel GPU is available"""
    render_device = Path('/dev/dri/renderD128')
    card_device = Path('/dev/dri/card0')
    
    if not render_device.exists() or not card_device.exists():
        return False, "Intel GPU devices not found (/dev/dri/renderD128, /dev/dri/card0)"
    
    # Check render group
    try:
        result = subprocess.run(['getent', 'group', 'render'],
                              capture_output=True,
                              text=True)
        if result.returncode != 0:
            return False, "Render group not found on system"
        
        render_gid = result.stdout.split(':')[2]
        print_info(f"Render group GID: {render_gid}")
        
    except Exception as e:
        return False, f"Error checking render group: {e}"
    
    return True, "Intel GPU detected and accessible"

def run_validation() -> bool:
    """Run all validation checks"""
    print_header("MEDIA SERVER STACK - CONFIGURATION VALIDATION")
    
    all_valid = True
    
    # Load environment
    print_info("Loading .env file...")
    try:
        env_vars = load_env()
        print_success(f"Loaded {len(env_vars)} environment variables")
    except Exception as e:
        print_error(f"Failed to load .env: {e}")
        return False
    
    # Check required variables
    print_info("\nValidating required variables...")
    missing = validate_required_vars(env_vars)
    if missing:
        print_error(f"Missing or invalid variables: {', '.join(missing)}")
        print_info("Edit .env and set these variables properly")
        all_valid = False
    else:
        print_success("All required variables are set")
    
    # Validate Mullvad config
    print_info("\nValidating Mullvad WireGuard configuration...")
    mullvad_issues = validate_mullvad_config(env_vars)
    if mullvad_issues:
        for issue in mullvad_issues:
            print_error(issue)
        print_info("Get correct values from: https://mullvad.net/en/account/wireguard-config")
        all_valid = False
    else:
        print_success("Mullvad configuration looks valid")
    
    # Validate network
    print_info("\nValidating network configuration...")
    network_issues = validate_network(env_vars)
    if network_issues:
        for issue in network_issues:
            print_error(issue)
        all_valid = False
    else:
        print_success(f"LAN subnet: {env_vars['LAN_SUBNET']}")
    
    # Validate paths
    print_info("\nValidating storage paths...")
    path_issues = validate_paths(env_vars)
    if path_issues:
        for var, issue in path_issues:
            print_error(f"{var}: {issue}")
        all_valid = False
    else:
        print_success(f"DATA_ROOT: {env_vars['DATA_ROOT']}")
        print_success(f"CONFIG_ROOT: {env_vars['CONFIG_ROOT']}")
    
    # Check Docker
    print_info("\nChecking Docker...")
    if check_docker():
        print_success("Docker is installed and running")
    else:
        print_error("Docker is not running or not installed")
        print_info("Install: curl -fsSL https://get.docker.com | sh")
        all_valid = False
    
    # Check Intel GPU
    print_info("\nChecking Intel GPU for hardware transcoding...")
    gpu_ok, gpu_msg = check_intel_gpu()
    if gpu_ok:
        print_success(gpu_msg)
    else:
        print_warning(gpu_msg)
        print_info("Hardware transcoding will not be available")
    
    # Summary
    print_header("VALIDATION SUMMARY")
    if all_valid:
        print_success("All critical validations passed!")
        print_info("\nYou can now start the stack with:")
        print_info("  ./manage.py start")
    else:
        print_error("Validation failed - fix the issues above before starting")
        return False
    
    return True

def docker_compose_command(cmd: str) -> int:
    """Run docker compose command"""
    try:
        result = subprocess.run(
            ['docker', 'compose'] + cmd.split(),
            check=False
        )
        return result.returncode
    except Exception as e:
        print_error(f"Failed to run docker compose: {e}")
        return 1

def show_access_info():
    """Show access information for all services"""
    env_vars = load_env()
    
    print_header("SERVICE ACCESS INFORMATION")
    
    # Get local IP
    try:
        result = subprocess.run(
            ['hostname', '-I'],
            capture_output=True,
            text=True
        )
        local_ip = result.stdout.split()[0]
    except:
        local_ip = "YOUR_SERVER_IP"
    
    services = [
        ("Jellyfin (Media Server)", f"http://{local_ip}:{env_vars['JELLYFIN_PORT']}"),
        ("Jellyseerr (Content Requests)", f"http://{local_ip}:{env_vars['JELLYSEERR_PORT']}"),
        ("Radarr (Movies)", f"http://{local_ip}:{env_vars['RADARR_PORT']}"),
        ("Sonarr (TV Shows)", f"http://{local_ip}:{env_vars['SONARR_PORT']}"),
        ("Prowlarr (Indexers)", f"http://{local_ip}:{env_vars['PROWLARR_PORT']}"),
        ("Bazarr (Subtitles)", f"http://{local_ip}:{env_vars['BAZARR_PORT']}"),
        ("qBittorrent (via VPN)", f"http://{local_ip}:{env_vars['QBITTORRENT_PORT']}"),
    ]
    
    for name, url in services:
        print(f"{GREEN}•{RESET} {BOLD}{name:30}{RESET} {url}")
    
    print(f"\n{YELLOW}IMPORTANT:{RESET}")
    print(f"  • qBittorrent traffic is VPN-protected (Mullvad)")
    print(f"  • Default qBittorrent credentials: admin / adminadmin")
    print(f"  • Change qBittorrent password immediately!")

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <command>")
        print(f"\nCommands:")
        print(f"  validate  - Validate .env configuration")
        print(f"  start     - Start all services")
        print(f"  stop      - Stop all services")
        print(f"  restart   - Restart all services")
        print(f"  logs      - Show logs (add container name for specific container)")
        print(f"  status    - Show running containers")
        print(f"  down      - Stop and remove all containers")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'validate':
        success = run_validation()
        sys.exit(0 if success else 1)
    
    elif command == 'start':
        print_header("STARTING MEDIA SERVER STACK")
        
        # Validate first
        if not run_validation():
            sys.exit(1)
        
        print_info("\nPulling latest images...")
        docker_compose_command('pull')
        
        print_info("\nStarting containers...")
        result = docker_compose_command('up -d')
        
        if result == 0:
            print_success("\nAll containers started!")
            show_access_info()
            print_info("\nView logs: ./manage.py logs")
            print_info("Check VPN: docker exec qbittorrent curl -s ifconfig.me")
        else:
            print_error("Failed to start containers")
        
        sys.exit(result)
    
    elif command == 'stop':
        print_info("Stopping all containers...")
        result = docker_compose_command('stop')
        sys.exit(result)
    
    elif command == 'restart':
        print_info("Restarting all containers...")
        docker_compose_command('stop')
        result = docker_compose_command('up -d')
        if result == 0:
            show_access_info()
        sys.exit(result)
    
    elif command == 'logs':
        # Check if specific container specified
        if len(sys.argv) > 2:
            container = sys.argv[2]
            result = docker_compose_command(f'logs -f --tail=100 {container}')
        else:
            result = docker_compose_command('logs -f --tail=100')
        sys.exit(result)
    
    elif command == 'status':
        result = docker_compose_command('ps')
        sys.exit(result)
    
    elif command == 'down':
        print_warning("This will stop and remove all containers")
        print_warning("Config and data will be preserved")
        confirm = input("Continue? (yes/no): ")
        if confirm.lower() == 'yes':
            result = docker_compose_command('down')
            sys.exit(result)
        else:
            print_info("Cancelled")
            sys.exit(0)
    
    else:
        print_error(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()
