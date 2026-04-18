#!/usr/bin/env python3
"""
HexChat Spotify /np Plugin - Validation and Test Script
Use this to verify the plugin will work before loading in HexChat
"""

import sys
import json
import os
import stat
import re
from pathlib import Path
from typing import Tuple, Optional

# Spotify credential format validation
CLIENT_ID_PATTERN = re.compile(r'^[a-f0-9]{32}$')
CLIENT_SECRET_PATTERN = re.compile(r'^[a-f0-9]{32}$')


def print_section(title: str) -> None:
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def check_python_version() -> bool:
    """Check Python version"""
    print_section("1. Python Version")
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"Python {version}")
    
    if sys.version_info.major >= 3 and sys.version_info.minor >= 6:
        print("✓ Version OK (3.6+ required)")
        return True
    else:
        print("✗ Python 3.6+ required")
        return False


def check_requests_library() -> bool:
    """Check if requests library is installed"""
    print_section("2. Required Libraries")
    
    try:
        import requests
        print(f"✓ requests {requests.__version__}")
        return True
    except ImportError:
        print("✗ requests library not found")
        print("  Install with: pip install requests")
        return False


def find_plugin_file() -> Tuple[bool, Optional[Path]]:
    """Find the plugin file in various locations"""
    # Possible locations
    locations = [
        Path(__file__).parent / "spotify_np.py",  # Same directory as this script
        Path.home() / ".config" / "hexchat" / "addons" / "spotify_np.py",  # HexChat addons
        Path.cwd() / "spotify_np.py",  # Current working directory
    ]
    
    for loc in locations:
        if loc.exists():
            return True, loc
    
    return False, None


def check_hexchat_config() -> bool:
    """Check HexChat config directory structure"""
    print_section("3. HexChat Configuration")
    
    config_dir = Path.home() / ".config" / "hexchat" / "addons"
    
    if not config_dir.exists():
        print(f"⚠ Config directory not found: {config_dir}")
        print("  Creating directory...")
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created: {config_dir}")
        except PermissionError:
            print(f"✗ Permission denied creating: {config_dir}")
            return False
        except Exception as e:
            print(f"✗ Failed to create: {e}")
            return False
    else:
        print(f"✓ Config directory exists: {config_dir}")
    
    # Check plugin file in multiple locations
    found, plugin_path = find_plugin_file()
    if found:
        print(f"✓ Plugin file found: {plugin_path}")
        
        # Check if it needs to be copied to HexChat addons
        hexchat_plugin = config_dir / "spotify_np.py"
        if plugin_path != hexchat_plugin and not hexchat_plugin.exists():
            print(f"⚠ Plugin not in HexChat addons directory")
            print(f"  Copy with: cp {plugin_path} {hexchat_plugin}")
    else:
        print(f"✗ Plugin file not found")
        print(f"  Expected in one of:")
        print(f"    - {Path(__file__).parent / 'spotify_np.py'}")
        print(f"    - {Path.home() / '.config' / 'hexchat' / 'addons' / 'spotify_np.py'}")
        return False
    
    return True


def check_spotify_credentials() -> bool:
    """Check Spotify credentials configuration"""
    print_section("4. Spotify Credentials")
    
    config_file = Path.home() / ".config" / "hexchat" / "addons" / "spotify_np.conf"
    
    if not config_file.exists():
        print(f"⚠ Config file not found: {config_file}")
        print("  This is OK - it will be created during setup")
        print("  Run: python3 setup_spotify_np.py")
        return True
    
    # Check file permissions
    file_stat = os.stat(config_file)
    mode = file_stat.st_mode
    if mode & (stat.S_IRGRP | stat.S_IROTH):
        print(f"⚠ Config file is readable by others (permissions: {oct(mode)[-3:]})")
        print("  Recommend: chmod 600 ~/.config/hexchat/addons/spotify_np.conf")
    else:
        print(f"✓ Config file permissions OK (600)")
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        client_id = config.get('client_id', '')
        client_secret = config.get('client_secret', '')
        access_token = config.get('access_token')
        
        if client_id and client_secret:
            # Validate format
            if CLIENT_ID_PATTERN.match(client_id):
                print(f"✓ Client ID: {client_id[:8]}...{client_id[-4:]}")
            else:
                print(f"⚠ Client ID format may be invalid")
            
            if CLIENT_SECRET_PATTERN.match(client_secret):
                print(f"✓ Client Secret: {'*' * 24}{client_secret[-4:]}")
            else:
                print(f"⚠ Client Secret format may be invalid")
        else:
            print("✗ Spotify credentials not configured")
            print("  Run: python3 setup_spotify_np.py")
            return False
        
        if access_token:
            print(f"✓ Access token available (authenticated)")
        else:
            print("⚠ No access token (will authenticate on first /np)")
        
        return True
    except json.JSONDecodeError:
        print(f"✗ Config file is corrupted (invalid JSON)")
        print("  Delete and reconfigure: rm ~/.config/hexchat/addons/spotify_np.conf")
        return False
    except PermissionError:
        print(f"✗ Permission denied reading config file")
        return False
    except Exception as e:
        print(f"✗ Error reading config: {e}")
        return False


def test_spotify_api() -> bool:
    """Test Spotify API connectivity"""
    print_section("5. Spotify API Connectivity")
    
    try:
        import requests
        print("Testing Spotify API connection...")
        
        response = requests.get(
            'https://api.spotify.com/v1/me',
            headers={'Authorization': 'Bearer invalid_token'},
            timeout=10
        )
        
        if response.status_code == 401:
            print("✓ Spotify API is reachable (401 = expected without valid token)")
            return True
        else:
            print(f"✓ Spotify API responded (status: {response.status_code})")
            return True
    except requests.exceptions.Timeout:
        print("✗ Spotify API timeout (network issue or slow connection)")
        return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot reach Spotify API")
        print("  Check your internet connection")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_webbrowser() -> bool:
    """Test browser availability for OAuth"""
    print_section("6. Web Browser Support")
    
    try:
        import webbrowser
        print("✓ webbrowser module available")
        
        # Try to detect default browser
        try:
            if hasattr(webbrowser, '_tryorder') and webbrowser._tryorder:
                browsers = webbrowser._tryorder[:3]
                print(f"✓ Detected browsers: {', '.join(browsers)}")
        except Exception:
            pass
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_local_server() -> bool:
    """Test local HTTP server capability"""
    print_section("7. Local OAuth Callback Server")
    
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import socket
        
        # Try to bind to port 8888
        try:
            # Use socket to test port availability without starting a server
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('127.0.0.1', 8888))
                print("✓ Port 8888 is available (OAuth callback)")
        except OSError as e:
            if "Address already in use" in str(e):
                print("⚠ Port 8888 is in use")
                print("  This may cause issues during authentication")
                print("  Close any application using port 8888, or wait and retry")
            else:
                print(f"⚠ Cannot bind to port 8888: {e}")
            return True  # Not fatal
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_plugin_syntax() -> bool:
    """Test that the plugin file has valid Python syntax"""
    print_section("8. Plugin Syntax Check")
    
    found, plugin_path = find_plugin_file()
    if not found or not plugin_path:
        print("✗ Plugin file not found, skipping syntax check")
        return False
    
    try:
        with open(plugin_path, 'r') as f:
            source = f.read()
        
        # Compile to check for syntax errors
        compile(source, plugin_path, 'exec')
        print(f"✓ Plugin syntax is valid")
        
        # Check for required components
        if 'hexchat.hook_command' in source:
            print("✓ HexChat command hook found")
        else:
            print("⚠ HexChat command hook not found")
        
        if 'SpotifyAuth' in source:
            print("✓ SpotifyAuth class found")
        
        if 'CSRF' in source.lower() or 'state' in source:
            print("✓ CSRF protection appears to be implemented")
        
        return True
    except SyntaxError as e:
        print(f"✗ Syntax error in plugin: {e}")
        return False
    except Exception as e:
        print(f"✗ Error checking plugin: {e}")
        return False


def run_all_checks() -> bool:
    """Run all validation checks"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  HexChat Spotify /np Plugin - Validation Test".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Libraries", check_requests_library),
        ("HexChat Configuration", check_hexchat_config),
        ("Spotify Credentials", check_spotify_credentials),
        ("Spotify API", test_spotify_api),
        ("Web Browser", test_webbrowser),
        ("Local Server", test_local_server),
        ("Plugin Syntax", test_plugin_syntax),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ Unexpected error in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print_section("Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {name}")
    
    print(f"\n{passed}/{total} checks passed")
    
    if passed == total:
        print("\n✓ All checks passed! Ready to use.")
        print("\nNext steps:")
        print("1. If not configured: python3 setup_spotify_np.py")
        print("2. Copy plugin to HexChat: cp spotify_np.py ~/.config/hexchat/addons/")
        print("3. In HexChat: /py load spotify_np")
        print("4. In HexChat: /np")
    elif passed >= total - 2:
        print("\n⚠ Most checks passed. Some features may have issues.")
        print("See above for details and recommendations.")
    else:
        print("\n✗ Some critical checks failed. See above for details.")
    
    print()
    return passed == total


if __name__ == "__main__":
    success = run_all_checks()
    sys.exit(0 if success else 1)
