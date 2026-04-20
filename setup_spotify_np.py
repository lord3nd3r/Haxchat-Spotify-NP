#!/usr/bin/env python3
"""
HexChat Spotify /np Plugin - Setup Helper
Run this to configure the plugin without needing to manually enter commands in HexChat
"""

import json
import os
import stat
import re
from pathlib import Path
import sys
from typing import Optional, Tuple

# Spotify credential format validation
CLIENT_ID_PATTERN = re.compile(r'^[a-f0-9]{32}$')
CLIENT_SECRET_PATTERN = re.compile(r'^[a-f0-9]{32}$')


def validate_client_id(client_id: str) -> Tuple[bool, str]:
    """Validate Spotify Client ID format"""
    if not client_id:
        return False, "Client ID is required"
    if len(client_id) != 32:
        return False, f"Client ID should be 32 characters (got {len(client_id)})"
    if not CLIENT_ID_PATTERN.match(client_id):
        return False, "Client ID should only contain lowercase hex characters (0-9, a-f)"
    return True, ""


def validate_client_secret(client_secret: str) -> Tuple[bool, str]:
    """Validate Spotify Client Secret format"""
    if not client_secret:
        return False, "Client Secret is required"
    if len(client_secret) != 32:
        return False, f"Client Secret should be 32 characters (got {len(client_secret)})"
    if not CLIENT_SECRET_PATTERN.match(client_secret):
        return False, "Client Secret should only contain lowercase hex characters (0-9, a-f)"
    return True, ""


def get_credential_with_validation(prompt: str, validator) -> Optional[str]:
    """Get and validate a credential from user input"""
    max_attempts = 3
    for attempt in range(max_attempts):
        value = input(prompt).strip().lower()  # Spotify credentials are lowercase hex
        is_valid, error_msg = validator(value)
        if is_valid:
            return value
        print(f"✗ {error_msg}")
        if attempt < max_attempts - 1:
            print("  Please try again.")
    return None


def setup_spotify_np():
    """Interactive setup for Spotify /np plugin"""
    
    print("=" * 60)
    print("HexChat Spotify /np Plugin - Setup Helper")
    print("=" * 60)
    print()
    
    # Check if requests library is installed
    try:
        import requests
        print("✓ requests library found")
    except ImportError:
        print("✗ requests library not found")
        print("  Install with: pip install requests")
        sys.exit(1)
    
    # Get config directory
    config_dir = Path.home() / ".config" / "hexchat" / "addons"
    config_file = config_dir / "spotify_np.conf"
    
    # Create directory if needed
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Load existing config if present
    existing_config = {}
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                existing_config = json.load(f)
            print(f"✓ Found existing config at {config_file}")
        except json.JSONDecodeError:
            print(f"Warning: Existing config file is corrupted, will overwrite")
        except Exception as e:
            print(f"Warning: Could not load existing config: {e}")
    
    print()
    print("Step 1: Create Spotify Developer App")
    print("-" * 60)
    print("1. Go to: https://developer.spotify.com/dashboard")
    print("2. Log in with your Spotify account")
    print("3. Click 'Create App'")
    print("4. Fill in the app details:")
    print("   - App name: HexChat NP (or any name you like)")
    print("   - App description: Anything")
    print("   - Redirect URI: http://localhost:8888/callback")
    print("5. Accept the terms and create the app")
    print("6. Click 'Settings' to find your Client ID and Client Secret")
    print()
    print("IMPORTANT: The Redirect URI you enter in Spotify MUST match exactly!")
    print("           Default: http://localhost:8888/callback")
    print()
    
    # Get and validate credentials
    client_id = get_credential_with_validation(
        "Enter your Client ID: ",
        validate_client_id
    )
    if not client_id:
        print("✗ Failed to get valid Client ID after 3 attempts")
        sys.exit(1)
    
    client_secret = get_credential_with_validation(
        "Enter your Client Secret: ",
        validate_client_secret
    )
    if not client_secret:
        print("✗ Failed to get valid Client Secret after 3 attempts")
        sys.exit(1)
    
    print()
    print("Step 2: Save Configuration")
    print("-" * 60)
    
    # Ask about custom redirect URI
    print("If you used a different Redirect URI in Spotify, enter it now.")
    print("Otherwise, press Enter to use the default.")
    print("Default: http://localhost:8888/callback")
    print()
    print("NOTE: Spotify allows http://localhost for development apps.")
    print("      If you used https://, change it to http:// in Spotify settings.")
    print()
    custom_redirect = input("Redirect URI (or Enter for default): ").strip()
    
    # Update config (preserve any existing tokens)
    config_data = existing_config.copy()
    config_data['client_id'] = client_id
    config_data['client_secret'] = client_secret
    if custom_redirect:
        if custom_redirect.startswith('https://localhost'):
            print()
            print("WARNING: https://localhost requires SSL certificates.")
            print("         Please use http://localhost instead in Spotify settings.")
            print()
        config_data['redirect_uri'] = custom_redirect
        print(f"  Using redirect URI: {custom_redirect}")
    elif 'redirect_uri' not in config_data:
        # Only set default if not already configured
        pass  # Will use DEFAULT_REDIRECT_URI in the plugin
    
    # Save config with secure permissions
    try:
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        # Set file permissions to 600 (owner read/write only)
        os.chmod(config_file, stat.S_IRUSR | stat.S_IWUSR)
        print(f"✓ Configuration saved to {config_file}")
        print(f"✓ File permissions set to 600 (owner read/write only)")
    except PermissionError:
        print(f"✗ Permission denied writing to {config_file}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error saving configuration: {e}")
        sys.exit(1)
    
    print()
    print("Step 3: Load Plugin in HexChat")
    print("-" * 60)
    print("In HexChat, run:")
    print("  /py load spotify_np")
    print()
    print("Then run:")
    print("  /np")
    print()
    print("Your browser will open for Spotify login.")
    print()
    print("=" * 60)
    print("Setup complete! ✓")
    print("=" * 60)


if __name__ == "__main__":
    try:
        setup_spotify_np()
    except KeyboardInterrupt:
        print("\nSetup cancelled")
        sys.exit(0)
    except EOFError:
        print("\nNo input received")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
