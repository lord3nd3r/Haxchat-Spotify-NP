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
3. Add a **Redirect URI** (required!)
	- Try `http://localhost:8888/callback` or `http://127.0.0.1:8888/callback` (Spotify may warn about "Insecure" but allow it in dev mode)
	- If only HTTPS is allowed, use `https://localhost:8888/callback` or `https://127.0.0.1:8888/callback` (see below)
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


Your browser will open for Spotify login on first use (see below if it doesn't work).

## Authentication (Manual Flow)

Spotify may block HTTP redirect URIs or refuse to connect to `localhost`. If so, use the manual authentication flow:

1. Set your Redirect URI in Spotify to `https://localhost:8888/callback` or `https://127.0.0.1:8888/callback` (even if the page won't load)
2. In HexChat, run:
	```
	/np redirect https://localhost:8888/callback
	/np reset
	/np url
	```
3. Open the URL shown in your browser and log in/authorize
4. The browser will try to redirect to `https://localhost:8888/callback?...` and fail to connect (that's OK!)
5. **Copy the entire URL from your browser's address bar**
6. In HexChat, run:
	```
	/np code <paste the URL here>
	```
7. If successful, `/np` will now show your currently playing track

If you get `redirect_uri: Insecure`, try `127.0.0.1` instead of `localhost`.

## Commands

| Command | Description |
|---------|-------------|
| `/np` | Show currently playing track |
| `/np auth` | Re-authenticate with Spotify (automatic, only works if HTTP allowed) |
| `/np url` | Show manual authentication URL |
| `/np code <url>` | Complete manual authentication with callback URL |
| `/np reset` | Clear stored credentials |
| `/np status` | Show auth status |
| `/np redirect <uri>` | Set redirect URI to match Spotify app |
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


### Common Issues

- **Browser page won't load after login**: That's expected! Just copy the URL from the address bar and use `/np code <url>`.
- **redirect_uri: Insecure**: Try `127.0.0.1` instead of `localhost` in both Spotify and `/np redirect`.
- **Port 8888 in use**: Change the port in your redirect URI (e.g., `http://localhost:9999/callback`) and update both Spotify and `/np redirect`.
- **Nothing playing**: Start playback in Spotify on any device.

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
