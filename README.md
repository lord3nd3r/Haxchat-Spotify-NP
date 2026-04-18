# HexChat Spotify /np Plugin

Display your currently playing Spotify track in IRC with the `/np` command.

```
[▶] The Weeknd - Blinding Lights
```

## Features

- 🎵 Shows artist and track name from Spotify
- 🎨 Color-coded output (green = playing, red = paused)
- 🔐 Secure OAuth2 with CSRF protection
- 🔄 Automatic token refresh
- 🔒 Config stored with secure file permissions

## Quick Start

### 1. Create Spotify App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create an app
3. Add `http://localhost:8888/callback` as a **Redirect URI** (required!)
4. Copy your **Client ID** and **Client Secret**

### 2. Install

```bash
# Clone the repo
git clone https://github.com/lord3nd3r/Haxchat-Spotify-NP.git
cd Haxchat-Spotify-NP

# Run setup
python3 setup_spotify_np.py

# Copy plugin to HexChat
cp spotify_np.py ~/.config/hexchat/addons/
```

### 3. Use

In HexChat:
```
/py load spotify_np
/np
```

Your browser will open for Spotify login on first use.

## Commands

| Command | Description |
|---------|-------------|
| `/np` | Show currently playing track |
| `/np auth` | Re-authenticate with Spotify |
| `/np reset` | Clear stored credentials |
| `/np status` | Show auth status |
| `/np help` | Show help |

## Requirements

- HexChat with Python 3.6+ support
- `requests` library (`pip install requests`)
- Spotify account (free tier works)

## Files

| File | Description |
|------|-------------|
| `spotify_np.py` | Main HexChat plugin |
| `setup_spotify_np.py` | Interactive setup wizard |
| `validate_spotify_np.py` | Troubleshooting tool |

## Troubleshooting

Run the validation script to diagnose issues:

```bash
python3 validate_spotify_np.py
```

See [README_SPOTIFY_NP.md](README_SPOTIFY_NP.md) for detailed troubleshooting.

## Security

- OAuth flow uses CSRF protection (state parameter)
- Config file saved with 600 permissions (owner-only)
- Credentials validated before saving
- Callback server binds to localhost only

## License

Public domain. Modify and share freely.
