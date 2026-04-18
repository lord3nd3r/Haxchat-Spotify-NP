# Quick Start: HexChat Spotify /np Plugin

## 3-Minute Setup

### 1. Get Spotify Credentials (2 min)
```
Visit: https://developer.spotify.com/dashboard
- Log in / Create account
- Click "Create App"
- Add Redirect URI: http://localhost:8888/callback  ← REQUIRED!
- Copy Client ID & Secret from Settings
```

### 2. Configure Plugin (1 min)
```bash
cd /path/to/spotify-np
python3 setup_spotify_np.py
# Follow prompts to enter Client ID and Secret
```

### 3. Install & Load in HexChat
```bash
cp spotify_np.py ~/.config/hexchat/addons/
```

In HexChat:
```
/py load spotify_np
/np
# Browser opens → Log in → Return to HexChat ✓
```

---

## Commands Reference

| Command | What it does |
|---------|-------------|
| `/np` | Show currently playing track |
| `/np auth` | Re-authenticate with Spotify |
| `/np reset` | Clear stored credentials |
| `/np status` | Show authentication status |
| `/np help` | Show help |

---

## Output Examples

**Playing:**
```
[▶] The Weeknd - Blinding Lights
```
(Green text)

**Paused:**
```
[⏸] The Weeknd - Blinding Lights  
```
(Red text)

**Not playing:**
```
[NP] Nothing playing
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Plugin not initialized" | Check credentials - run `setup_spotify_np.py` |
| "Not authenticated" | Run `/np auth` to login |
| "Port 8888 in use" | Close other apps using the port |
| "Nothing playing" | Start a track in Spotify |
| Plugin won't load | Install `pip install requests` |
| "Invalid state parameter" | Security check - just retry `/np auth` |

---

## Files

```
spotify_np.py          - Main plugin (copy to ~/.config/hexchat/addons/)
setup_spotify_np.py    - Setup wizard
validate_spotify_np.py - Troubleshooting tool
spotify_np.conf        - Auto-generated config (in ~/.config/hexchat/addons/)
```

---

## Security

- CSRF protection on OAuth flow
- Config file secured with 600 permissions
- Credentials validated before saving
- Localhost-only callback server

---

## How It Works

1. **First use**: Opens browser for Spotify OAuth login (with CSRF protection)
2. **Token stored**: Saved locally with secure permissions
3. **Fresh data**: Fetches live playing status each `/np` call
4. **Auto-refresh**: Token refreshes automatically (5-min buffer before expiry)

---

## Need Help?

See `README_SPOTIFY_NP.md` for full documentation.

Run `python3 validate_spotify_np.py` to diagnose issues.
