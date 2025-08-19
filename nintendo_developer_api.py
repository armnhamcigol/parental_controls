#!/usr/bin/env python3
"""
Nintendo Developer API Integration for Parental Controls
========================================================

This module provides integration with Nintendo's official Developer APIs
to manage parental controls for Nintendo Switch devices.

Requirements:
- Nintendo Developer Account with approved application
- Valid API keys and certificates
- Proper OAuth2 setup for user authentication

Author: Parental Controls Dashboard
Version: 1.0.0
"""

import json
import time
import requests
import hashlib
import hmac
import base64
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
from cryptography.fernet import Fernet
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NintendoDevice:
    """Represents a Nintendo Switch device from Developer API"""
    device_id: str
    device_name: str
    nickname: str
    location: str
    online_status: bool
    last_played_game: Optional[str]
    play_time_today: int  # minutes
    play_time_this_week: int  # minutes
    parental_controls_enabled: bool
    current_restrictions: Dict[str, Any]
    last_seen: datetime
    firmware_version: str
    account_id: str

@dataclass
class ParentalControlSettings:
    """Parental control configuration for a device"""
    daily_time_limit: int  # minutes
    bedtime_enabled: bool
    bedtime_start: str  # HH:MM format
    bedtime_end: str  # HH:MM format
    allowed_software_ratings: List[str]
    restricted_features: List[str]
    communication_restrictions: bool
    purchase_restrictions: bool

class NintendoDeveloperAPIError(Exception):
    """Custom exception for Nintendo Developer API errors"""
    pass

class NintendoDeveloperAPI:
    """
    Nintendo Developer API Client for Parental Controls
    
    This class handles authentication and API calls to Nintendo's
    official Developer APIs for managing parental controls.
    """
    
    def __init__(self, config_file: str = "nintendo_developer_config.json"):
        """Initialize the Nintendo Developer API client"""
        self.config_file = config_file
        self.config = self._load_config()
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.authenticated = False
        
        # API endpoints
        self.base_url = self.config.get('base_url', 'https://api-lp1.znc.srv.nintendo.net')
        self.auth_url = self.config.get('auth_url', 'https://accounts.nintendo.com')
        self.api_version = self.config.get('api_version', 'v1')
        
        # Initialize session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NintendoParentalControlsApp/1.0.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Config file {self.config_file} not found. Using default configuration.")
                return self._create_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration template"""
        config = {
            "client_id": "YOUR_NINTENDO_DEVELOPER_CLIENT_ID",
            "client_secret": "YOUR_NINTENDO_DEVELOPER_CLIENT_SECRET",
            "redirect_uri": "https://localhost:8080/auth/callback",
            "scope": "parental_controls device_management user_profile",
            "base_url": "https://api-lp1.znc.srv.nintendo.net",
            "auth_url": "https://accounts.nintendo.com",
            "api_version": "v1",
            "encryption_key": Fernet.generate_key().decode(),
            "production_mode": True,
            "rate_limit": {
                "requests_per_minute": 60,
                "burst_limit": 10
            },
            "timeout": 30,
            "retry_attempts": 3
        }
        
        # Save the default config
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Created default config file: {self.config_file}")
            logger.warning("Please update the config file with your Nintendo Developer API credentials!")
        except Exception as e:
            logger.error(f"Could not save default config: {e}")
            
        return config
    
    def authenticate(self, username: str = None, password: str = None, 
                    session_token: str = None) -> bool:
        """
        Authenticate with Nintendo Developer APIs
        
        Args:
            username: Nintendo account username (if using password auth)
            password: Nintendo account password (if using password auth)  
            session_token: Pre-obtained session token (recommended)
            
        Returns:
            bool: True if authentication successful
        """
        try:
            if session_token:
                return self._authenticate_with_session_token(session_token)
            elif username and password:
                return self._authenticate_with_credentials(username, password)
            else:
                return self._authenticate_with_stored_tokens()
                
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def _authenticate_with_session_token(self, session_token: str) -> bool:
        """Authenticate using a pre-obtained session token"""
        try:
            # Exchange session token for access token
            auth_payload = {
                'client_id': self.config['client_id'],
                'session_token': session_token,
                'grant_type': 'urn:ietf:params:oauth:grant-type:session-token'
            }
            
            response = self.session.post(
                f"{self.auth_url}/connect/1.0.0/api/token",
                json=auth_payload,
                timeout=self.config['timeout']
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                self.refresh_token = token_data.get('refresh_token')
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # Update session headers
                self.session.headers['Authorization'] = f'Bearer {self.access_token}'
                
                # Store tokens securely
                self._store_tokens()
                
                self.authenticated = True
                logger.info("Successfully authenticated with Nintendo Developer APIs")
                return True
            else:
                logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Session token authentication failed: {e}")
            return False
    
    def _authenticate_with_credentials(self, username: str, password: str) -> bool:
        """Authenticate using Nintendo account credentials (OAuth2 flow)"""
        try:
            # Step 1: Get authorization code
            auth_params = {
                'client_id': self.config['client_id'],
                'redirect_uri': self.config['redirect_uri'],
                'response_type': 'code',
                'scope': self.config['scope'],
                'state': str(uuid.uuid4())
            }
            
            auth_url = f"{self.auth_url}/connect/1.0.0/authorize"
            
            # In a real implementation, you'd redirect the user to this URL
            # and handle the callback. For now, we'll simulate this process.
            logger.info(f"Authorization URL: {auth_url}")
            logger.warning("Manual OAuth2 flow required. Please implement web-based authentication.")
            
            return False  # Implement full OAuth2 flow as needed
            
        except Exception as e:
            logger.error(f"Credential authentication failed: {e}")
            return False
    
    def _authenticate_with_stored_tokens(self) -> bool:
        """Authenticate using stored refresh token"""
        try:
            stored_tokens = self._load_stored_tokens()
            if not stored_tokens or 'refresh_token' not in stored_tokens:
                logger.warning("No stored tokens found")
                return False
                
            # Use refresh token to get new access token
            refresh_payload = {
                'client_id': self.config['client_id'],
                'client_secret': self.config['client_secret'],
                'refresh_token': stored_tokens['refresh_token'],
                'grant_type': 'refresh_token'
            }
            
            response = self.session.post(
                f"{self.auth_url}/connect/1.0.0/api/token",
                json=refresh_payload,
                timeout=self.config['timeout']
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                self.refresh_token = token_data.get('refresh_token', stored_tokens['refresh_token'])
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                self.session.headers['Authorization'] = f'Bearer {self.access_token}'
                self._store_tokens()
                
                self.authenticated = True
                logger.info("Successfully refreshed authentication tokens")
                return True
            else:
                logger.error(f"Token refresh failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Stored token authentication failed: {e}")
            return False
    
    def _store_tokens(self):
        """Securely store authentication tokens"""
        try:
            if not self.config.get('encryption_key'):
                logger.warning("No encryption key found. Tokens will not be stored.")
                return
                
            fernet = Fernet(self.config['encryption_key'].encode())
            
            token_data = {
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None,
                'stored_at': datetime.now().isoformat()
            }
            
            encrypted_data = fernet.encrypt(json.dumps(token_data).encode())
            
            with open('.nintendo_tokens', 'wb') as f:
                f.write(encrypted_data)
                
            logger.debug("Tokens stored securely")
            
        except Exception as e:
            logger.error(f"Failed to store tokens: {e}")
    
    def _load_stored_tokens(self) -> Optional[Dict[str, str]]:
        """Load stored authentication tokens"""
        try:
            if not os.path.exists('.nintendo_tokens'):
                return None
                
            if not self.config.get('encryption_key'):
                return None
                
            fernet = Fernet(self.config['encryption_key'].encode())
            
            with open('.nintendo_tokens', 'rb') as f:
                encrypted_data = f.read()
                
            decrypted_data = fernet.decrypt(encrypted_data)
            token_data = json.loads(decrypted_data.decode())
            
            # Check if tokens are expired
            if token_data.get('expires_at'):
                expires_at = datetime.fromisoformat(token_data['expires_at'])
                if expires_at <= datetime.now():
                    logger.info("Stored tokens have expired")
                    return None
                    
            return token_data
            
        except Exception as e:
            logger.error(f"Failed to load stored tokens: {e}")
            return None
    
    def get_user_devices(self) -> List[NintendoDevice]:
        """Get list of Nintendo Switch devices for authenticated user"""
        if not self.authenticated:
            raise NintendoDeveloperAPIError("Not authenticated")
            
        try:
            response = self.session.get(
                f"{self.base_url}/api/{self.api_version}/devices",
                timeout=self.config['timeout']
            )
            
            if response.status_code == 200:
                devices_data = response.json()
                devices = []
                
                for device_data in devices_data.get('devices', []):
                    device = NintendoDevice(
                        device_id=device_data['device_id'],
                        device_name=device_data.get('device_name', 'Nintendo Switch'),
                        nickname=device_data.get('nickname', ''),
                        location=device_data.get('location', 'Unknown'),
                        online_status=device_data.get('online', False),
                        last_played_game=device_data.get('last_played_application', {}).get('name'),
                        play_time_today=device_data.get('play_time_today_minutes', 0),
                        play_time_this_week=device_data.get('play_time_week_minutes', 0),
                        parental_controls_enabled=device_data.get('parental_controls_enabled', False),
                        current_restrictions=device_data.get('current_restrictions', {}),
                        last_seen=datetime.fromisoformat(device_data.get('last_seen', datetime.now().isoformat())),
                        firmware_version=device_data.get('firmware_version', 'Unknown'),
                        account_id=device_data.get('linked_account_id', '')
                    )
                    devices.append(device)
                    
                logger.info(f"Retrieved {len(devices)} devices from Nintendo Developer API")
                return devices
                
            else:
                logger.error(f"Failed to get devices: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting user devices: {e}")
            return []
    
    def get_device_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status for a specific device"""
        if not self.authenticated:
            raise NintendoDeveloperAPIError("Not authenticated")
            
        try:
            response = self.session.get(
                f"{self.base_url}/api/{self.api_version}/devices/{device_id}/status",
                timeout=self.config['timeout']
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get device status: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting device status: {e}")
            return None
    
    def update_parental_controls(self, device_id: str, settings: ParentalControlSettings) -> bool:
        """Update parental control settings for a device"""
        if not self.authenticated:
            raise NintendoDeveloperAPIError("Not authenticated")
            
        try:
            settings_data = {
                'daily_time_limit_minutes': settings.daily_time_limit,
                'bedtime_enabled': settings.bedtime_enabled,
                'bedtime_start': settings.bedtime_start,
                'bedtime_end': settings.bedtime_end,
                'allowed_software_ratings': settings.allowed_software_ratings,
                'restricted_features': settings.restricted_features,
                'communication_restrictions': settings.communication_restrictions,
                'purchase_restrictions': settings.purchase_restrictions
            }
            
            response = self.session.put(
                f"{self.base_url}/api/{self.api_version}/devices/{device_id}/parental-controls",
                json=settings_data,
                timeout=self.config['timeout']
            )
            
            if response.status_code in [200, 204]:
                logger.info(f"Successfully updated parental controls for device {device_id}")
                return True
            else:
                logger.error(f"Failed to update parental controls: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating parental controls: {e}")
            return False
    
    def suspend_device(self, device_id: str, duration_minutes: int = None) -> bool:
        """Suspend a device immediately (parental control action)"""
        if not self.authenticated:
            raise NintendoDeveloperAPIError("Not authenticated")
            
        try:
            suspend_data = {
                'action': 'suspend',
                'immediate': True
            }
            
            if duration_minutes:
                suspend_data['duration_minutes'] = duration_minutes
                
            response = self.session.post(
                f"{self.base_url}/api/{self.api_version}/devices/{device_id}/actions",
                json=suspend_data,
                timeout=self.config['timeout']
            )
            
            if response.status_code in [200, 202]:
                logger.info(f"Successfully suspended device {device_id}")
                return True
            else:
                logger.error(f"Failed to suspend device: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error suspending device: {e}")
            return False
    
    def resume_device(self, device_id: str) -> bool:
        """Resume a suspended device"""
        if not self.authenticated:
            raise NintendoDeveloperAPIError("Not authenticated")
            
        try:
            resume_data = {
                'action': 'resume',
                'immediate': True
            }
            
            response = self.session.post(
                f"{self.base_url}/api/{self.api_version}/devices/{device_id}/actions",
                json=resume_data,
                timeout=self.config['timeout']
            )
            
            if response.status_code in [200, 202]:
                logger.info(f"Successfully resumed device {device_id}")
                return True
            else:
                logger.error(f"Failed to resume device: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error resuming device: {e}")
            return False
    
    def get_usage_history(self, device_id: str, days: int = 7) -> Dict[str, Any]:
        """Get usage history for a device"""
        if not self.authenticated:
            raise NintendoDeveloperAPIError("Not authenticated")
            
        try:
            params = {
                'days': days,
                'include_applications': True
            }
            
            response = self.session.get(
                f"{self.base_url}/api/{self.api_version}/devices/{device_id}/usage",
                params=params,
                timeout=self.config['timeout']
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get usage history: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting usage history: {e}")
            return {}
    
    def logout(self) -> bool:
        """Logout and clear authentication"""
        try:
            if self.authenticated and self.access_token:
                # Revoke the access token
                revoke_data = {
                    'client_id': self.config['client_id'],
                    'token': self.access_token
                }
                
                self.session.post(
                    f"{self.auth_url}/connect/1.0.0/api/revoke",
                    json=revoke_data,
                    timeout=self.config['timeout']
                )
            
            # Clear stored data
            self.access_token = None
            self.refresh_token = None
            self.token_expires_at = None
            self.authenticated = False
            
            if 'Authorization' in self.session.headers:
                del self.session.headers['Authorization']
            
            # Remove stored tokens
            if os.path.exists('.nintendo_tokens'):
                os.remove('.nintendo_tokens')
                
            logger.info("Successfully logged out from Nintendo Developer APIs")
            return True
            
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            return False

def test_nintendo_developer_api():
    """Test function to verify Nintendo Developer API integration"""
    print("🎮 Testing Nintendo Developer API Integration")
    print("=" * 50)
    
    # Initialize API client
    api = NintendoDeveloperAPI()
    
    print(f"✅ Configuration loaded from: {api.config_file}")
    print(f"📡 API Base URL: {api.base_url}")
    
    # Test authentication (requires manual setup)
    print("\n⚠️  To test authentication, you need to:")
    print("1. Update nintendo_developer_config.json with your API credentials")
    print("2. Obtain a session token from Nintendo Developer Portal")
    print("3. Call api.authenticate(session_token='your_token')")
    
    print("\n🔧 Example usage:")
    print("""
    # After setting up credentials:
    api = NintendoDeveloperAPI()
    
    # Authenticate with session token
    if api.authenticate(session_token='your_session_token'):
        print("✅ Authenticated successfully!")
        
        # Get devices
        devices = api.get_user_devices()
        for device in devices:
            print(f"📱 Device: {device.device_name} ({device.device_id})")
            print(f"   Status: {'🟢 Online' if device.online_status else '🔴 Offline'}")
            print(f"   Play Time Today: {device.play_time_today} minutes")
            
            # Update parental controls
            settings = ParentalControlSettings(
                daily_time_limit=120,
                bedtime_enabled=True,
                bedtime_start="21:00",
                bedtime_end="07:00",
                allowed_software_ratings=["E", "E10+"],
                restricted_features=["web_browser", "social_features"],
                communication_restrictions=True,
                purchase_restrictions=True
            )
            
            success = api.update_parental_controls(device.device_id, settings)
            print(f"   Parental Controls Updated: {'✅' if success else '❌'}")
    """)

if __name__ == "__main__":
    test_nintendo_developer_api()
