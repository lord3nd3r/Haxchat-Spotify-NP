# HexChat Spotify /np Plugin v2.0 - Ready to Use

## Files

```
spotify_np.py              (~18 KB) - Main plugin
setup_spotify_np.py        (~5 KB)  - Setup wizard with validation
validate_spotify_np.py     (~8 KB)  - Validation/troubleshooting tool
README_SPOTIFY_NP.md       (~4 KB)  - Full documentation
QUICKSTART.md              (~2 KB)  - Quick reference
IMPLEMENTATION_SUMMARY.md  (~6 KB)  - Technical details
```

## Security Features (v2.0)

- **CSRF Protection**: Secure state parameter in OAuth flow
- **File Permissions**: Config saved with 600 (owner-only)
- **Input Validation**: Credential format verified before saving
- **Thread Safety**: Queue-based inter-thread communication
- **Localhost Binding**: OAuth callback on 127.0.0.1 only

## Installation

### Step 1: Run Setup (with validation)

```bash
python3 setup_spotify_np.py
```

This will:
- Validate your Spotify credentials format (32-char hex)
- Save them securely (permissions 600)
- Guide you through Spotify Developer app setup

**Important**: Add `http://localhost:8888/callback` as a Redirect URI in your Spotify app!

### Step 2: Copy Plugin to HexChat

```bash
cp spotify_np.py ~/.config/hexchat/addons/
```

### Step 3: Load and Use

In HexChat:
```
/py load spotify_np
/np
```

## Commands

| Command | Description |
|---------|-------------|
| `/np` | Show currently playing track |
| `/np auth` | Re-authenticate with Spotify |
| `/np reset` | Clear stored credentials |
| `/np status` | Show auth status and token expiry |
| `/np help` | Show help message |

## Output Examples

```
[▶] The Weeknd - Blinding Lights    (green = playing)
[⏸] The Weeknd - Blinding Lights    (red = paused)
[NP] Nothing playing                 (red = no track)
```

## Troubleshooting

**Run the validation script:**
```bash
python3 validate_spotify_np.py
```

This checks:
- Python version (3.6+ required)
- Required libraries (`requests`)
- HexChat configuration
- Spotify credentials format
- API connectivity
- Port 8888 availability
- Plugin syntax

**Common Issues:**

| Problem | Solution |
|---------|----------|
| "requests not found" | `pip install requests` |
| "Port 8888 in use" | Close other apps, wait, retry |
| "Invalid state parameter" | Security feature - retry `/np auth` |
| "Credentials not configured" | Run `setup_spotify_np.py` |
| Plugin won't load | Check `/py console` for errors |

## Configuration

**File location:** `~/.config/hexchat/addons/spotify_np.conf`

**Format:**
```json
{
  "client_id": "your32characterclientid00000000",
  "client_secret": "your32characterclientsecret0000",
  "access_token": "...",
  "refresh_token": "...",
  "token_expiry": 1713456789.0
}
```

**Security:** File permissions automatically set to 600 (owner read/write only).

## What's New in v2.0

- CSRF protection on OAuth flow
- Secure file permissions (600)
- Input validation for credentials
- Thread-safe OAuth communication
- Fixed HexChat plugin API usage
- Added `/np status` and `/np help` commands
- Improved error handling and messages
- Rate limit handling
- Output sanitization for IRC safety
- 5-minute token refresh buffer
- Type hints throughout codebase

## Requirements

- HexChat with Python 3.6+ support
- `requests` library (`pip install requests`)
- Spotify account (free tier works)
- Port 8888 available for OAuth callback

## Documentation

- **Full docs**: [README_SPOTIFY_NP.md](README_SPOTIFY_NP.md)
- **Quick start**: [QUICKSTART.md](QUICKSTART.md)
- **Technical details**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

## License

Public domain. Modify and share freely.
