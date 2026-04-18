# HexChat Spotify /np Plugin - Implementation Summary

## Version 2.0 - Security & Quality Update

This document describes the implementation details and security features of the plugin.

---

## Files

| File | Size | Purpose |
|------|------|---------|
| `spotify_np.py` | ~18 KB | Main HexChat plugin |
| `setup_spotify_np.py` | ~5 KB | Interactive setup wizard |
| `validate_spotify_np.py` | ~8 KB | Validation and troubleshooting |
| `README_SPOTIFY_NP.md` | ~4 KB | Full documentation |
| `QUICKSTART.md` | ~2 KB | Quick reference guide |

---

## Security Features

### 1. CSRF Protection
The OAuth flow includes a cryptographically secure state parameter:
```python
self._oauth_state = secrets.token_urlsafe(32)
```
This prevents authorization code injection attacks where an attacker could trick users into authorizing malicious requests.

### 2. Secure File Permissions
Config files containing credentials are created with owner-only permissions:
```python
os.chmod(self.config_file, stat.S_IRUSR | stat.S_IWUSR)  # 600
```

### 3. Input Validation
Spotify credentials are validated before saving:
- Must be exactly 32 characters
- Must be lowercase hexadecimal (0-9, a-f)

### 4. Localhost-Only Binding
The OAuth callback server binds to `127.0.0.1` only, not all interfaces.

### 5. Thread-Safe Communication
Uses `queue.Queue` for inter-thread communication instead of shared mutable state.

---

## Architecture

### Phase 1: OAuth Authentication
```
User runs /np
  ↓
Plugin checks if authenticated
  ↓
If not: Generate CSRF state token
  ↓
Start callback server on 127.0.0.1:8888
  ↓
Open browser → Spotify login page
  ↓
User logs in → Authorization granted
  ↓
Spotify redirects to localhost:8888 with code + state
  ↓
Plugin verifies state matches (CSRF check)
  ↓
Exchange code for tokens via thread-safe queue
  ↓
Tokens stored in config file (permissions 600)
```

### Phase 2: Track Fetching
```
User runs /np
  ↓
Check token validity (refresh if <5 min to expiry)
  ↓
Make API request to /v1/me/player/currently-playing
  ↓
Handle response:
  - 200: Parse and display track
  - 204: Nothing playing
  - 401: Refresh token and retry (once)
  - 429: Rate limited, show retry time
  ↓
Sanitize output (remove control characters)
  ↓
Format with IRC colors
  ↓
Output to channel via /say
```

---

## Classes

### SpotifyConfig
Handles persistent storage with secure file permissions.
- Stores credentials and tokens as JSON
- Creates config directory if needed
- Sets file permissions to 600 on save

### OAuthCallbackHandler
HTTP request handler for OAuth callback.
- Validates CSRF state parameter
- Uses thread-safe queue for results
- Sends formatted HTML responses

### SpotifyAuth
Manages OAuth2 authentication flow.
- Generates secure state tokens
- Handles token exchange and refresh
- 5-minute buffer before token expiry

### SpotifyNP
Fetches and formats currently playing track.
- Handles all API response codes
- Sanitizes output for IRC safety
- Rate limit handling

### PluginState
Container for plugin state (replaces scattered globals).

---

## Commands

| Command | Function |
|---------|----------|
| `/np` | Show currently playing or start auth |
| `/np auth` | Force re-authentication |
| `/np reset` | Clear all stored credentials |
| `/np status` | Show auth status and token expiry |
| `/np help` | Display help message |

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Not authenticated | Initiates OAuth flow automatically |
| Token expired | Auto-refreshes with 5-min buffer |
| Token refresh fails | Prompts to re-authenticate |
| API timeout | Shows timeout message |
| Connection error | Shows network error message |
| Rate limited | Shows retry-after time |
| Invalid JSON | Shows parse error |
| Port 8888 in use | Shows helpful error message |
| CSRF state mismatch | Rejects request, shows security error |
| No active playback | Shows "Nothing playing" |

---

## Output Format

**Playing:**
```
[▶] Artist Name - Track Title
```
(IRC color 03 = green)

**Paused:**
```
[⏸] Artist Name - Track Title
```
(IRC color 04 = red)

**Errors:**
```
[NP] Error message
```
(IRC color 04 = red)

---

## Dependencies

- Python 3.6+
- `requests` library (HTTP client)
- Standard library: `json`, `os`, `stat`, `threading`, `time`, `secrets`, `queue`, `typing`, `urllib.parse`, `http.server`, `pathlib`

---

## Configuration File Format

`~/.config/hexchat/addons/spotify_np.conf`:
```json
{
  "client_id": "32characterhexstring00000000000",
  "client_secret": "32characterhexstring00000000000",
  "access_token": "BQD...",
  "refresh_token": "AQD...",
  "token_expiry": 1713456789.123
}
```

---

## Known Limitations

- Single Spotify account only
- Port 8888 must be available for OAuth
- OAuth blocks HexChat briefly during auth (up to 2 min timeout)
- Only displays track info (no album/playlist)
- Requires internet connection

---

## Customization

To modify the plugin, edit `spotify_np.py`:

| Change | Location |
|--------|----------|
| Output format | `SpotifyNP.format_output()` method |
| IRC colors | `COLOR_GREEN`, `COLOR_RED` constants |
| Callback port | `CALLBACK_PORT` constant |
| OAuth timeout | `OAUTH_TIMEOUT` constant |
| Token refresh buffer | In `exchange_code_for_token()` and `refresh_access_token()` |

After editing, reload in HexChat:
```
/py reload spotify_np
```

---

## Changelog

### Version 2.0
- Added CSRF protection with state parameter
- Added secure file permissions (600)
- Added input validation for credentials
- Fixed thread-safety using queue.Queue
- Fixed plugin initialization (proper HexChat API)
- Added `/np status` and `/np help` commands
- Improved error messages
- Added rate limit handling
- Added output sanitization
- Increased timeout to 120 seconds
- Changed token refresh buffer to 5 minutes
- Added type hints throughout

### Version 1.0
- Initial implementation

### Debug Commands

In HexChat:
```
/py console              # Open Python console
/py exec import spotify_np; print(spotify_np.config.data)  # View config
/set -list spotify      # Show Spotify settings (if any)
```

---

## Conclusion

The HexChat Spotify `/np` plugin is fully implemented, validated, and ready to use. All planned features from the initial design have been completed:

✅ OAuth2 browser-based authentication  
✅ Automatic token management  
✅ Color-coded IRC output  
✅ Comprehensive error handling  
✅ Easy setup via interactive wizard  
✅ Full documentation  
✅ Validation and testing tools  

The implementation is production-ready and can be used immediately by following the Quick Start guide above.
