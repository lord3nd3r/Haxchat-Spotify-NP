# HexChat Spotify /np Plugin

Display your currently playing Spotify track in IRC via `/np` command.

## Features

- ▶ Shows artist and track name
- 🎨 Color-coded output (green for playing, red for paused)
- 🔐 Secure OAuth2 authentication with CSRF protection
- 🔄 Automatic token refresh
- 🔒 Config file secured with 600 permissions
- ⚡ Fresh data on each call

## Setup

### 1. Create Spotify Developer App

1. Go to https://developer.spotify.com/dashboard
2. Log in with your Spotify account
3. Click "Create App"
4. Fill in the details:
   - **App name**: HexChat NP (or any name)
   - **App description**: Anything
   - **Redirect URI**: `http://localhost:8888/callback` ← **IMPORTANT!**
5. Accept terms and create
6. Click "Settings" to find your **Client ID** and **Client Secret**

> ⚠️ **IMPORTANT**: You must add `http://localhost:8888/callback` as a Redirect URI in your Spotify app settings, or authentication will fail!

### 2. Configure the Plugin

Run the setup script:

```bash
python3 setup_spotify_np.py
```

This will:
- Validate your Client ID and Secret format
- Save credentials securely (file permissions 600)
- Guide you through the process

### 3. Install the Plugin

Copy the plugin to HexChat's addons directory:

```bash
cp spotify_np.py ~/.config/hexchat/addons/
```

### 4. Load and Use

In HexChat:

```
/py load spotify_np
/np
```

On first run, your browser opens for Spotify login. After authorizing, return to HexChat.

## Commands

| Command | Description |
|---------|-------------|
| `/np` | Show currently playing track |
| `/np auth` | Manually trigger Spotify authentication |
| `/np reset` | Clear stored credentials and re-authenticate |
| `/np status` | Show authentication status and token expiry |
| `/np help` | Show help message |

## How It Works

1. **First run**: OAuth2 login opens in browser with CSRF protection
2. **Token stored**: Saved locally with secure file permissions
3. **Subsequent runs**: Fetches live data from Spotify API
4. **Paused**: Shows red pause icon (⏸) instead of green play (▶)
5. **Token refresh**: Automatically refreshes tokens (5-minute buffer)

## Security Features

- **CSRF Protection**: Random state parameter prevents authorization code injection attacks
- **Secure File Permissions**: Config file created with 600 permissions (owner read/write only)
- **Localhost-only Callback**: OAuth callback server binds to 127.0.0.1 only
- **Input Validation**: Credential format validated before saving
- **Thread-safe OAuth**: Uses queue for inter-thread communication

## Configuration Storage

Credentials and tokens stored in: `~/.config/hexchat/addons/spotify_np.conf`

**Security**: File permissions are set to 600 (owner read/write only).

## Troubleshooting

### "Not authenticated"
- Run `/np auth` to login again
- Check that your Client ID and Secret are correct
- Verify redirect URI is set in Spotify dashboard

### "Port 8888 is in use"
- Close other applications using port 8888
- Wait a moment and try again
- Check for zombie processes: `lsof -i :8888`

### "Nothing playing"
- Start playing a track in Spotify (web, desktop, or mobile)
- Make sure Spotify is playing on an active device

### "Invalid state parameter"
- This is a security check - try `/np auth` again
- Ensure you're completing auth within 2 minutes

### Plugin won't load
- Make sure `requests` library is installed: `pip install requests`
- Check HexChat Python plugin is enabled
- See console output: `/py console`

### "Credentials not configured"
- Run the setup script: `python3 setup_spotify_np.py`
- Or manually create `~/.config/hexchat/addons/spotify_np.conf`:
  ```json
  {
    "client_id": "your32characterclientid00000000",
    "client_secret": "your32characterclientsecret0000"
  }
  ```

## Requirements

- HexChat with Python 3 support
- Python 3.6+
- Python `requests` library
- Active Spotify account (free tier works)

## Limitations

- Only shows currently playing track (no album/playlist info)
- Requires active internet connection
- Tokens valid ~1 hour (auto-refresh with 5-minute buffer)
- Only works with Spotify (not other music services)
- OAuth callback requires port 8888 to be available

## Files

| File | Purpose |
|------|---------|
| `spotify_np.py` | Main plugin - copy to `~/.config/hexchat/addons/` |
| `setup_spotify_np.py` | Setup wizard for credentials |
| `validate_spotify_np.py` | Validation/troubleshooting tool |
| `spotify_np.conf` | Auto-generated config (created by plugin) |

## License

Public domain. Feel free to modify and share.
