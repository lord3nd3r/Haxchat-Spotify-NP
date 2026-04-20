"""
HexChat Spotify /np Plugin
Displays currently playing Spotify track via /np command
"""

import hexchat
import requests
import json
import os
import queue
import secrets
import stat
import threading
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

__module_name__ = "Spotify /np"
__module_version__ = "1.0"
__module_description__ = "Display currently playing Spotify track"

# Configuration
PLUGIN_NAME = "spotify_np"
CONFIG_DIR = Path(hexchat.get_info("configdir")) / "addons"
CONFIG_FILE = CONFIG_DIR / f"{PLUGIN_NAME}.conf"
CALLBACK_PORT = 8888
OAUTH_TIMEOUT = 120
DEFAULT_REDIRECT_URI = f"http://localhost:{CALLBACK_PORT}/callback"

# Spotify API endpoints
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_URL = "https://api.spotify.com/v1"

# IRC color codes
COLOR_GREEN = "\00303"
COLOR_RED = "\00304"
COLOR_RESET = "\003"


class SpotifyConfig:
    """Handle plugin configuration storage with secure file permissions"""
    
    def __init__(self) -> None:
        self.config_file: Path = CONFIG_FILE
        self.data: Dict[str, Any] = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """Load config from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                hexchat.prnt(f"[NP] Config file corrupted: {e}")
            except PermissionError:
                hexchat.prnt("[NP] Cannot read config file - permission denied")
            except Exception as e:
                hexchat.prnt(f"[NP] Error loading config: {e}")
        return {}
    
    def _save(self) -> None:
        """Save config to file with secure permissions (owner read/write only)"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.data, f, indent=2)
            # Set file permissions to 600 (owner read/write only) for security
            os.chmod(self.config_file, stat.S_IRUSR | stat.S_IWUSR)
        except PermissionError:
            hexchat.prnt("[NP] Cannot write config file - permission denied")
        except Exception as e:
            hexchat.prnt(f"[NP] Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value"""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set config value and save"""
        self.data[key] = value
        self._save()
    
    def remove(self, key: str) -> None:
        """Remove config value and save"""
        if key in self.data:
            del self.data[key]
            self._save()


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback from Spotify with CSRF protection"""
    
    # Thread-safe queue for passing auth results
    result_queue: queue.Queue = queue.Queue()
    expected_state: Optional[str] = None
    
    def do_GET(self) -> None:
        """Handle GET request from OAuth redirect"""
        # Parse query parameters
        try:
            query = parse_qs(self.path.split('?')[1] if '?' in self.path else '')
        except Exception:
            self._send_error("Invalid request")
            return
        
        # Verify CSRF state parameter
        received_state = query.get('state', [None])[0]
        if received_state != OAuthCallbackHandler.expected_state:
            self._send_error("Invalid state parameter - possible CSRF attack")
            OAuthCallbackHandler.result_queue.put(('error', 'state_mismatch'))
            return
        
        if 'code' in query:
            auth_code = query['code'][0]
            self._send_success()
            OAuthCallbackHandler.result_queue.put(('success', auth_code))
        elif 'error' in query:
            error = query['error'][0]
            self._send_error(f"Spotify error: {error}")
            OAuthCallbackHandler.result_queue.put(('error', error))
        else:
            self._send_error("Missing authorization code")
            OAuthCallbackHandler.result_queue.put(('error', 'missing_code'))
    
    def _send_success(self) -> None:
        """Send success response"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        html = b"""<!DOCTYPE html><html><head><title>Success</title>
        <style>body{font-family:sans-serif;text-align:center;padding:50px;}</style></head>
        <body><h1>Success!</h1><p>You can close this window and return to HexChat.</p></body></html>"""
        self.wfile.write(html)
    
    def _send_error(self, message: str) -> None:
        """Send error response"""
        self.send_response(400)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        html = f"""<!DOCTYPE html><html><head><title>Error</title>
        <style>body{{font-family:sans-serif;text-align:center;padding:50px;color:red;}}</style></head>
        <body><h1>Error</h1><p>{message}</p></body></html>""".encode()
        self.wfile.write(html)
    
    def log_message(self, format: str, *args) -> None:
        """Suppress HTTP server log messages"""
        pass


class SpotifyAuth:
    """Handle Spotify OAuth authentication with CSRF protection"""
    
    def __init__(self, client_id: str, client_secret: str, config: SpotifyConfig) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.config = config
        self.redirect_uri: str = self.config.get('redirect_uri', DEFAULT_REDIRECT_URI)
        self.access_token: Optional[str] = self.config.get('access_token')
        self.refresh_token: Optional[str] = self.config.get('refresh_token')
        self.token_expiry: float = self.config.get('token_expiry', 0)
        self._oauth_state: Optional[str] = None
        self._oauth_server: Optional[HTTPServer] = None
    
    def is_authenticated(self) -> bool:
        """Check if we have a valid access token"""
        return bool(self.access_token and time.time() < self.token_expiry)
    
    def get_auth_url(self) -> str:
        """Generate Spotify authorization URL with CSRF state parameter"""
        # Generate cryptographically secure state for CSRF protection
        self._oauth_state = secrets.token_urlsafe(32)
        OAuthCallbackHandler.expected_state = self._oauth_state
        
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': 'user-read-currently-playing',
            'state': self._oauth_state,
            'show_dialog': 'false'
        }
        return f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"
    
    def start_oauth_flow(self) -> bool:
        """Start OAuth flow in browser with proper threading"""
        import webbrowser
        
        hexchat.prnt("[NP] Opening Spotify login in your browser...")
        
        # Clear any previous results from the queue
        while not OAuthCallbackHandler.result_queue.empty():
            try:
                OAuthCallbackHandler.result_queue.get_nowait()
            except queue.Empty:
                break
        
        # Try to start callback server
        try:
            self._oauth_server = HTTPServer(('127.0.0.1', CALLBACK_PORT), OAuthCallbackHandler)
            self._oauth_server.timeout = 1  # 1 second timeout for handle_request
        except OSError as e:
            if "Address already in use" in str(e):
                hexchat.prnt(f"[NP] Port {CALLBACK_PORT} is in use. Close other applications using it.")
            else:
                hexchat.prnt(f"[NP] Cannot start callback server: {e}")
            return False
        
        # Start server in background thread
        server_thread = threading.Thread(
            target=self._run_server,
            daemon=True,
            name="SpotifyOAuthServer"
        )
        server_thread.start()
        
        # Open browser
        auth_url = self.get_auth_url()
        try:
            webbrowser.open(auth_url)
        except Exception as e:
            hexchat.prnt(f"[NP] Cannot open browser: {e}")
            hexchat.prnt(f"[NP] Please manually visit: {auth_url}")
        
        # Wait for callback using thread-safe queue
        try:
            result = OAuthCallbackHandler.result_queue.get(timeout=OAUTH_TIMEOUT)
            status, data = result
            
            if status == 'success':
                return self.exchange_code_for_token(data)
            else:
                hexchat.prnt(f"[NP] Authentication failed: {data}")
                return False
        except queue.Empty:
            hexchat.prnt("[NP] Authentication timed out (no response within 2 minutes)")
            return False
        finally:
            self._cleanup_server()
    
    def _run_server(self) -> None:
        """Run callback server until request received or shutdown"""
        if self._oauth_server:
            try:
                # Handle requests until we get one or timeout
                self._oauth_server.handle_request()
            except Exception as e:
                hexchat.prnt(f"[NP] Server error: {e}")
    
    def _cleanup_server(self) -> None:
        """Clean up the OAuth server"""
        if self._oauth_server:
            try:
                self._oauth_server.server_close()
            except Exception:
                pass
            self._oauth_server = None
        self._oauth_state = None
        OAuthCallbackHandler.expected_state = None
    
    def exchange_code_for_token(self, code: str) -> bool:
        """Exchange auth code for access token"""
        try:
            response = requests.post(
                SPOTIFY_TOKEN_URL,
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': self.redirect_uri,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data['access_token']
                self.refresh_token = data.get('refresh_token', self.refresh_token)
                # Use 5-minute buffer instead of 1-minute for safer token refresh
                self.token_expiry = time.time() + data.get('expires_in', 3600) - 300
                
                self.config.set('access_token', self.access_token)
                self.config.set('refresh_token', self.refresh_token)
                self.config.set('token_expiry', self.token_expiry)
                
                hexchat.prnt("[NP] Successfully authenticated with Spotify!")
                return True
            else:
                error_msg = "Unknown error"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error_description', error_data.get('error', error_msg))
                except Exception:
                    pass
                hexchat.prnt(f"[NP] Token exchange failed ({response.status_code}): {error_msg}")
                return False
        except requests.exceptions.Timeout:
            hexchat.prnt("[NP] Authentication timeout - Spotify took too long to respond")
            return False
        except requests.exceptions.ConnectionError:
            hexchat.prnt("[NP] Cannot connect to Spotify - check your internet connection")
            return False
        except Exception as e:
            hexchat.prnt(f"[NP] Authentication error: {e}")
            return False
    
    def refresh_access_token(self) -> bool:
        """Refresh access token using refresh token"""
        if not self.refresh_token:
            hexchat.prnt("[NP] No refresh token available - please re-authenticate with /np auth")
            return False
        
        try:
            response = requests.post(
                SPOTIFY_TOKEN_URL,
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': self.refresh_token,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data['access_token']
                # Spotify may issue a new refresh token
                if 'refresh_token' in data:
                    self.refresh_token = data['refresh_token']
                    self.config.set('refresh_token', self.refresh_token)
                # Use 5-minute buffer for safer token refresh
                self.token_expiry = time.time() + data.get('expires_in', 3600) - 300
                
                self.config.set('access_token', self.access_token)
                self.config.set('token_expiry', self.token_expiry)
                return True
            elif response.status_code == 400:
                # Refresh token may be revoked
                hexchat.prnt("[NP] Session expired - please re-authenticate with /np auth")
                return False
            else:
                hexchat.prnt(f"[NP] Token refresh failed ({response.status_code})")
                return False
        except requests.exceptions.Timeout:
            hexchat.prnt("[NP] Token refresh timeout")
            return False
        except requests.exceptions.ConnectionError:
            hexchat.prnt("[NP] Cannot connect to Spotify - check your internet connection")
            return False
        except Exception as e:
            hexchat.prnt(f"[NP] Token refresh error: {e}")
            return False


class SpotifyNP:
    """Fetch currently playing track from Spotify"""
    
    def __init__(self, auth: SpotifyAuth) -> None:
        self.auth = auth
        self._retry_count = 0
        self._max_retries = 1
    
    def get_currently_playing(self) -> Optional[Dict[str, Any]]:
        """Fetch currently playing track"""
        if not self.auth.is_authenticated():
            if not self.auth.refresh_access_token():
                return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.auth.access_token}'
            }
            
            response = requests.get(
                f'{SPOTIFY_API_URL}/me/player/currently-playing',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                # Check if response has content (204 = no content = nothing playing)
                if not response.content:
                    return None
                data = response.json()
                if data and data.get('item'):
                    self._retry_count = 0
                    return data
                return None
            elif response.status_code == 204:
                # No content - nothing currently playing
                return None
            elif response.status_code == 401:
                # Token invalid, try refresh (with retry limit)
                if self._retry_count < self._max_retries:
                    self._retry_count += 1
                    if self.auth.refresh_access_token():
                        return self.get_currently_playing()
                self._retry_count = 0
                return None
            elif response.status_code == 429:
                # Rate limited
                retry_after = response.headers.get('Retry-After', '60')
                hexchat.prnt(f"[NP] Rate limited by Spotify. Try again in {retry_after} seconds.")
                return None
            else:
                hexchat.prnt(f"[NP] Spotify API error ({response.status_code})")
                return None
        except requests.exceptions.Timeout:
            hexchat.prnt("[NP] Spotify API timeout")
            return None
        except requests.exceptions.ConnectionError:
            hexchat.prnt("[NP] Cannot connect to Spotify - check your internet connection")
            return None
        except json.JSONDecodeError:
            hexchat.prnt("[NP] Invalid response from Spotify")
            return None
        except Exception as e:
            hexchat.prnt(f"[NP] API error: {e}")
            return None
    
    def format_output(self, data: Optional[Dict[str, Any]]) -> str:
        """Format currently playing info for IRC"""
        if not data:
            return f"{COLOR_RED}[NP] Nothing playing{COLOR_RESET}"
        
        item = data.get('item')
        is_playing = data.get('is_playing', False)
        
        if not item:
            return f"{COLOR_RED}[NP] Nothing playing{COLOR_RESET}"
        
        # Extract track info with safe defaults
        track_name = item.get('name') or 'Unknown'
        artists = item.get('artists', [])
        artist_name = ', '.join([a.get('name', 'Unknown') for a in artists if a]) if artists else 'Unknown'
        
        # Sanitize output (remove control characters that could mess up IRC)
        track_name = ''.join(c for c in track_name if c.isprintable())
        artist_name = ''.join(c for c in artist_name if c.isprintable())
        
        # Format with color based on play status
        status_icon = "▶" if is_playing else "⏸"
        color = COLOR_GREEN if is_playing else COLOR_RED
        
        output = f"{color}[{status_icon}] {artist_name} - {track_name}{COLOR_RESET}"
        return output


# Plugin state container (avoids scattered globals)
class PluginState:
    """Container for plugin state"""
    def __init__(self) -> None:
        self.config: Optional[SpotifyConfig] = None
        self.auth: Optional[SpotifyAuth] = None
        self.np: Optional[SpotifyNP] = None
        self.initialized: bool = False

state = PluginState()


def cmd_np(word, word_eol, userdata) -> int:
    """Handle /np command"""
    if not state.initialized or not state.auth or not state.np:
        hexchat.prnt("[NP] Plugin not initialized. Check configuration.")
        return hexchat.EAT_ALL
    
    # Check for subcommands
    if len(word) > 1:
        subcommand = word[1].lower()
        
        if subcommand == "auth":
            hexchat.prnt("[NP] Starting authentication...")
            state.auth.start_oauth_flow()
            return hexchat.EAT_ALL
        
        elif subcommand == "reset":
            state.config.remove('access_token')
            state.config.remove('refresh_token')
            state.config.remove('token_expiry')
            state.auth.access_token = None
            state.auth.refresh_token = None
            state.auth.token_expiry = 0
            hexchat.prnt("[NP] Credentials cleared. Run /np to re-authenticate.")
            return hexchat.EAT_ALL
        
        elif subcommand == "status":
            if state.auth.is_authenticated():
                hexchat.prnt("[NP] Status: Authenticated")
                expiry = state.auth.token_expiry - time.time()
                if expiry > 0:
                    hexchat.prnt(f"[NP] Token expires in {int(expiry // 60)} minutes")
            else:
                hexchat.prnt("[NP] Status: Not authenticated")
            hexchat.prnt(f"[NP] Redirect URI: {state.auth.redirect_uri}")
            return hexchat.EAT_ALL
        
        elif subcommand == "redirect":
            if len(word) > 2:
                new_uri = word_eol[2].strip()
                state.config.set('redirect_uri', new_uri)
                state.auth.redirect_uri = new_uri
                hexchat.prnt(f"[NP] Redirect URI set to: {new_uri}")
                hexchat.prnt("[NP] Run /np reset then /np auth to re-authenticate")
            else:
                hexchat.prnt(f"[NP] Current redirect URI: {state.auth.redirect_uri}")
                hexchat.prnt("[NP] Usage: /np redirect <uri>")
                hexchat.prnt("[NP] Example: /np redirect https://localhost:8888/callback")
            return hexchat.EAT_ALL
        
        elif subcommand == "help":
            hexchat.prnt("[NP] Spotify Now Playing Commands:")
            hexchat.prnt("  /np           - Show currently playing track")
            hexchat.prnt("  /np auth      - Authenticate with Spotify")
            hexchat.prnt("  /np reset     - Clear stored credentials")
            hexchat.prnt("  /np status    - Show authentication status")
            hexchat.prnt("  /np redirect  - Show/set redirect URI")
            hexchat.prnt("  /np help      - Show this help")
            return hexchat.EAT_ALL
    
    # Check authentication
    if not state.auth.is_authenticated():
        hexchat.prnt("[NP] Not authenticated. Starting login...")
        if not state.auth.start_oauth_flow():
            return hexchat.EAT_ALL
    
    # Fetch and display currently playing
    track_data = state.np.get_currently_playing()
    output = state.np.format_output(track_data)
    
    hexchat.command(f"say {output}")
    return hexchat.EAT_ALL


def init_plugin() -> bool:
    """Initialize the plugin"""
    # Initialize config
    state.config = SpotifyConfig()
    
    # Get Spotify credentials from config
    client_id = state.config.get('client_id')
    client_secret = state.config.get('client_secret')
    
    if not client_id or not client_secret:
        hexchat.prnt("[NP] Spotify credentials not configured")
        hexchat.prnt("[NP] Run the setup script: python3 ~/.config/hexchat/addons/setup_spotify_np.py")
        hexchat.prnt("[NP] Or manually add client_id and client_secret to:")
        hexchat.prnt(f"[NP]   {CONFIG_FILE}")
        return False
    
    # Validate credentials format (basic check)
    if len(client_id) < 20 or len(client_secret) < 20:
        hexchat.prnt("[NP] Invalid Spotify credentials format")
        return False
    
    # Initialize auth and NP
    state.auth = SpotifyAuth(client_id, client_secret, state.config)
    state.np = SpotifyNP(state.auth)
    state.initialized = True
    
    return True


# Register command
hexchat.hook_command(
    "np",
    cmd_np,
    help="Usage: /np - Show currently playing Spotify track\n"
         "       /np auth - Authenticate with Spotify\n"
         "       /np reset - Clear stored credentials\n"
         "       /np status - Show authentication status\n"
         "       /np redirect <uri> - Set redirect URI to match Spotify app\n"
         "       /np help - Show help"
)

# Initialize on load
if init_plugin():
    hexchat.prnt(f"[NP] Spotify /np plugin v{__module_version__} loaded!")
    if state.auth and not state.auth.is_authenticated():
        hexchat.prnt("[NP] Run /np to authenticate")
else:
    hexchat.prnt("[NP] Plugin loaded but not configured - see messages above")
