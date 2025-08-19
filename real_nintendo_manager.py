#!/usr/bin/env python3
"""
Real Nintendo Switch Parental Controls Manager
Uses the pynintendoparental library to actually control Nintendo Switch devices
"""

import asyncio
import json
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time

# Real Nintendo Switch parental control imports
try:
    from pynintendoparental import NintendoParental, Authenticator, Device
    from pynintendoparental.authenticator import Authenticator
    from pynintendoparental.enum import RestrictionMode
    from pynintendoparental.exceptions import NoDevicesFoundException, InvalidOAuthConfigurationException
    NINTENDO_AVAILABLE = True
    print("✅ Nintendo Parental Control library available")
except ImportError as e:
    print(f"❌ Nintendo Parental Control library not available: {e}")
    NINTENDO_AVAILABLE = False

class RealNintendoSwitchManager:
    """Real Nintendo Switch Parental Controls Manager"""
    
    def __init__(self, config_file='nintendo_config.json'):
        self.config_file = config_file
        self.api: Optional[NintendoParental] = None
        self.authenticator: Optional[Authenticator] = None
        self.devices: Dict[str, Device] = {}
        self.session_token: Optional[str] = None
        self.last_update = None
        self.enhanced_discovery_available = True
        
        # Load configuration
        self.load_config()
        
        if NINTENDO_AVAILABLE and self.session_token:
            self.initialize_api()
    
    def load_config(self):
        """Load Nintendo Switch configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.session_token = config.get('session_token')
                    print(f"✅ Loaded Nintendo config from {self.config_file}")
            except Exception as e:
                print(f"❌ Error loading Nintendo config: {e}")
        else:
            print(f"⚠️  Nintendo config file {self.config_file} not found")
    
    def save_config(self):
        """Save Nintendo Switch configuration"""
        try:
            config = {
                'session_token': self.session_token,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"✅ Saved Nintendo config to {self.config_file}")
        except Exception as e:
            print(f"❌ Error saving Nintendo config: {e}")
    
    def initialize_api(self):
        """Initialize Nintendo Parental Control API"""
        if not NINTENDO_AVAILABLE:
            print("❌ Cannot initialize: Nintendo library not available")
            return False
            
        if not self.session_token:
            print("❌ Cannot initialize: No session token available")
            return False
        
        try:
            # Create authenticator with session token (this is sync)
            self.authenticator = Authenticator(session_token=self.session_token)
            
            # Create Nintendo Parental API instance (this is also sync)
            self.api = NintendoParental(
                authenticator=self.authenticator,
                timezone="America/New_York",  # Adjust as needed
                language="en-US"
            )
            
            print("✅ Nintendo Parental Control API initialized (async operations deferred)")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing Nintendo API: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if authenticated with Nintendo"""
        return self.api is not None and self.session_token is not None
    
    async def update_devices(self):
        """Update device information from Nintendo API"""
        if not self.is_authenticated():
            return False
        
        try:
            await self.api.update()
            
            if self.api.devices:
                self.devices = self.api.devices
                self.last_update = datetime.now()
                print(f"✅ Updated {len(self.devices)} Nintendo Switch devices")
                return True
            else:
                print("⚠️  No Nintendo Switch devices found")
                return False
                
        except NoDevicesFoundException:
            print("❌ No Nintendo Switch devices found on account")
            return False
        except InvalidOAuthConfigurationException:
            print("❌ Invalid Nintendo authentication configuration")
            return False
        except Exception as e:
            print(f"❌ Error updating Nintendo devices: {e}")
            return False
    
    def get_devices(self) -> List[Dict[str, Any]]:
        """Get all Nintendo Switch devices in dashboard format"""
        if not self.is_authenticated():
            return []
        
        # Run async update in sync context
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Update devices
        loop.run_until_complete(self.update_devices())
        
        dashboard_devices = []
        
        for device_id, device in self.devices.items():
            dashboard_device = {
                'device_id': device.device_id,
                'device_name': device.name,
                'device_type': 'nintendo_switch',
                'ip_address': 'unknown',  # Nintendo API doesn't provide IP
                'mac_address': None,
                'location': 'Nintendo Account',
                'online': True,  # Assume online if in Nintendo account
                'response_time_ms': None,
                'last_seen': datetime.now().isoformat(),
                
                # Nintendo-specific data
                'current_game': getattr(device, 'current_application', {}).get('name', 'Unknown') if hasattr(device, 'current_application') else 'Unknown',
                'network_activity_level': 'unknown',
                'estimated_game_active': getattr(device, 'playing_time', 0) > 0,
                'activity_score': min(getattr(device, 'playing_time', 0), 100),
                
                # Session tracking
                'current_session_minutes': getattr(device, 'playing_time', 0),
                'today_play_time_minutes': getattr(device, 'playing_time', 0),
                'session_active': getattr(device, 'playing_time', 0) > 0,
                
                # Control states (Real Nintendo parental controls!)
                'controls_enabled': device.parental_control_settings.get('restriction_mode') == RestrictionMode.FORCED_TERMINATION if hasattr(device, 'parental_control_settings') else True,
                'parental_controls_enabled': True,
                'daily_limit_minutes': getattr(device, 'limit_time', 180),
                
                # Discovery metadata
                'network_discovered': False,
                'enhanced_discovery': True,
                'production_mode': True  # This IS real Nintendo API!
            }
            dashboard_devices.append(dashboard_device)
        
        return dashboard_devices
    
    async def toggle_device_controls_async(self, device_id: str, enabled: bool) -> bool:
        """Toggle parental controls for a specific device (async)"""
        if not self.is_authenticated():
            print("❌ Not authenticated with Nintendo")
            return False
        
        if device_id not in self.devices:
            await self.update_devices()
            
        if device_id not in self.devices:
            print(f"❌ Device {device_id} not found")
            return False
        
        device = self.devices[device_id]
        
        try:
            if enabled:
                # Enable restrictions (forced termination mode)
                await device.set_restriction_mode(RestrictionMode.FORCED_TERMINATION)
                print(f"✅ {device_id}: Parental controls ENABLED (forced termination)")
                print(f"   🚫 {device_id}: Gaming will be forcibly stopped at time limits")
                print(f"   🚫 {device_id}: Bedtime restrictions active")
            else:
                # Disable restrictions (alarm mode - less restrictive)
                await device.set_restriction_mode(RestrictionMode.ALARM)
                print(f"✅ {device_id}: Parental controls DISABLED (alarm mode)")
                print(f"   ⚠️  {device_id}: Only alarms will show, gaming not forcibly stopped")
                print(f"   ⚠️  {device_id}: Bedtime restrictions relaxed")
            
            return True
            
        except Exception as e:
            print(f"❌ Error toggling {device_id} controls: {e}")
            return False
    
    def toggle_device_controls(self, device_id: str, enabled: bool) -> bool:
        """Toggle parental controls for a specific device (sync wrapper)"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.toggle_device_controls_async(device_id, enabled))
    
    async def set_daily_playtime_limit_async(self, device_id: str, minutes: int) -> bool:
        """Set daily playtime limit for a device (async)"""
        if not self.is_authenticated():
            return False
        
        if device_id not in self.devices:
            await self.update_devices()
            
        if device_id not in self.devices:
            return False
        
        device = self.devices[device_id]
        
        try:
            await device.update_max_daily_playtime(minutes)
            print(f"✅ {device_id}: Daily playtime limit set to {minutes} minutes")
            return True
        except Exception as e:
            print(f"❌ Error setting playtime limit for {device_id}: {e}")
            return False
    
    def set_daily_playtime_limit(self, device_id: str, minutes: int) -> bool:
        """Set daily playtime limit for a device (sync wrapper)"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.set_daily_playtime_limit_async(device_id, minutes))
    
    async def set_bedtime_async(self, device_id: str, bedtime_hour: int, bedtime_minute: int) -> bool:
        """Set bedtime for a device (async)"""
        if not self.is_authenticated():
            return False
        
        if device_id not in self.devices:
            await self.update_devices()
            
        if device_id not in self.devices:
            return False
        
        device = self.devices[device_id]
        
        try:
            await device.set_bedtime_alarm(bedtime_hour, bedtime_minute)
            print(f"✅ {device_id}: Bedtime set to {bedtime_hour:02d}:{bedtime_minute:02d}")
            return True
        except Exception as e:
            print(f"❌ Error setting bedtime for {device_id}: {e}")
            return False
    
    def set_bedtime(self, device_id: str, bedtime_hour: int, bedtime_minute: int) -> bool:
        """Set bedtime for a device (sync wrapper)"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.set_bedtime_async(device_id, bedtime_hour, bedtime_minute))
    
    def get_parental_control_status(self) -> Dict[str, Any]:
        """Get overall parental control status"""
        if not self.is_authenticated():
            return {'connected': False, 'devices': 0}
        
        return {
            'connected': True,
            'devices': len(self.devices),
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'api_available': NINTENDO_AVAILABLE
        }

# Test function
def test_real_nintendo_manager():
    """Test the real Nintendo manager"""
    print("🧪 Testing Real Nintendo Switch Manager...")
    
    manager = RealNintendoSwitchManager()
    
    print(f"📊 Authenticated: {manager.is_authenticated()}")
    print(f"📊 Nintendo Library Available: {NINTENDO_AVAILABLE}")
    
    if manager.is_authenticated():
        devices = manager.get_devices()
        print(f"📊 Found {len(devices)} devices")
        
        for device in devices:
            print(f"   🎮 {device['device_name']} ({device['device_id']})")
            print(f"      Current Game: {device['current_game']}")
            print(f"      Controls Enabled: {device['controls_enabled']}")
            print(f"      Daily Limit: {device['daily_limit_minutes']} min")

if __name__ == "__main__":
    test_real_nintendo_manager()
