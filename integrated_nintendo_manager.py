#!/usr/bin/env python3
"""
Integrated Nintendo Switch Manager
Combines Enhanced Network Discovery with Real Nintendo Parental Controls
"""

import asyncio
import json
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# Enhanced Discovery import
try:
    from enhanced_nintendo_discovery import EnhancedNintendoDiscovery
    ENHANCED_DISCOVERY_AVAILABLE = True
except ImportError:
    ENHANCED_DISCOVERY_AVAILABLE = False

# Real Nintendo Controls import
try:
    from real_nintendo_manager import RealNintendoSwitchManager
    REAL_NINTENDO_AVAILABLE = True
except ImportError:
    REAL_NINTENDO_AVAILABLE = False

class IntegratedNintendoManager:
    """Integrated Nintendo Switch Manager - Best of Both Worlds"""
    
    def __init__(self, config_file='nintendo_config.json'):
        self.config_file = config_file
        
        # Initialize both systems
        self.enhanced_discovery = None
        self.real_nintendo = None
        
        # Device state storage
        self.device_states = {}  # Store per-device toggle states
        self.last_update = None
        
        # Initialize Enhanced Discovery
        if ENHANCED_DISCOVERY_AVAILABLE:
            try:
                self.enhanced_discovery = EnhancedNintendoDiscovery()
                print("✅ Enhanced Nintendo Discovery initialized")
            except Exception as e:
                print(f"❌ Enhanced Discovery failed: {e}")
        
        # Initialize Real Nintendo Controls
        if REAL_NINTENDO_AVAILABLE:
            try:
                self.real_nintendo = RealNintendoSwitchManager(config_file)
                print("✅ Real Nintendo Controls initialized")
            except Exception as e:
                print(f"❌ Real Nintendo Controls failed: {e}")
        
        # Load device states
        self.load_device_states()
        
        self.enhanced_discovery_available = ENHANCED_DISCOVERY_AVAILABLE
    
    def load_device_states(self):
        """Load device toggle states from config"""
        try:
            if os.path.exists('device_states.json'):
                with open('device_states.json', 'r') as f:
                    self.device_states = json.load(f)
                print(f"✅ Loaded device states: {list(self.device_states.keys())}")
        except Exception as e:
            print(f"❌ Error loading device states: {e}")
    
    def save_device_states(self):
        """Save device toggle states to config"""
        try:
            with open('device_states.json', 'w') as f:
                json.dump(self.device_states, f, indent=2)
            print("✅ Saved device states")
        except Exception as e:
            print(f"❌ Error saving device states: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if authenticated (uses Real Nintendo for actual auth)"""
        if self.real_nintendo:
            return self.real_nintendo.is_authenticated()
        return True  # Enhanced discovery doesn't need auth
    
    def get_devices(self) -> List[Dict[str, Any]]:
        """Get combined device information from both systems"""
        devices = []
        
        # Start with Enhanced Discovery for live monitoring
        if self.enhanced_discovery:
            try:
                enhanced_devices = self.enhanced_discovery.discover_all_devices()
                devices = self.convert_enhanced_devices_to_dashboard_format(enhanced_devices)
                print(f"📡 Enhanced Discovery found {len(devices)} devices")
            except Exception as e:
                print(f"❌ Enhanced Discovery error: {e}")
        
        # If we have Real Nintendo, merge the control capabilities
        if self.real_nintendo and self.real_nintendo.is_authenticated():
            try:
                real_devices = self.real_nintendo.get_devices()
                devices = self.merge_real_controls_with_enhanced_data(devices, real_devices)
                print(f"🎮 Merged with Real Nintendo controls")
            except Exception as e:
                print(f"❌ Real Nintendo error: {e}")
        
        # Apply stored device states
        for device in devices:
            device_id = device['device_id']
            if device_id in self.device_states:
                device['controls_enabled'] = self.device_states[device_id].get('controls_enabled', True)
                device['daily_limit_minutes'] = self.device_states[device_id].get('daily_limit_minutes', 120)
        
        self.last_update = datetime.now()
        return devices
    
    def convert_enhanced_devices_to_dashboard_format(self, enhanced_devices):
        """Convert enhanced discovery data to dashboard format"""
        dashboard_devices = []
        for device in enhanced_devices:
            dashboard_device = {
                'device_id': device['device_id'],
                'device_name': device['device_name'],
                'device_type': device['device_type'],
                'ip_address': device['ip_address'],
                'mac_address': device.get('mac_address'),
                'location': device['location'],
                'online': device['online'],
                'response_time_ms': device.get('response_time_ms'),
                'last_seen': device['last_seen'],
                
                # Enhanced monitoring data
                'current_game': device['current_game'],
                'network_activity_level': device['network_activity_level'],
                'estimated_game_active': device.get('estimated_game_activity', False),
                'activity_score': device.get('activity_score', 0),
                
                # Session tracking
                'current_session_minutes': device['current_session_minutes'],
                'today_play_time_minutes': device['today_play_time_minutes'],
                'session_active': device['session_active'],
                
                # Default control states (will be overridden by stored states)
                'controls_enabled': True,
                'parental_controls_enabled': True,
                'daily_limit_minutes': 120,
                
                # Discovery metadata
                'network_discovered': True,
                'enhanced_discovery': True,
                'real_nintendo_controls': False,  # Will be updated if real controls available
                'production_mode': True
            }
            dashboard_devices.append(dashboard_device)
        return dashboard_devices
    
    def merge_real_controls_with_enhanced_data(self, enhanced_devices, real_devices):
        """Merge real Nintendo control capabilities with enhanced monitoring data"""
        # Create lookup for real devices
        real_devices_lookup = {dev['device_name']: dev for dev in real_devices}
        
        for device in enhanced_devices:
            device_name = device['device_name']
            
            # If we have real Nintendo data for this device, merge capabilities
            if device_name in real_devices_lookup:
                real_device = real_devices_lookup[device_name]
                
                # Update with real Nintendo control capabilities
                device['real_nintendo_controls'] = True
                device['real_device_id'] = real_device['device_id']
                
                # Keep enhanced discovery data for monitoring, but use real controls for limits
                # Enhanced discovery provides better real-time network monitoring
                # Real Nintendo provides actual parental control enforcement
                
                print(f"🔗 Merged {device_name}: Enhanced monitoring + Real controls")
        
        return enhanced_devices
    
    def toggle_device_controls(self, device_id: str, enabled: bool) -> bool:
        """Toggle parental controls for a specific device"""
        print(f"🎯 Toggling controls for {device_id}: {'ON' if enabled else 'OFF'}")
        
        # Store the state locally
        if device_id not in self.device_states:
            self.device_states[device_id] = {}
        
        self.device_states[device_id]['controls_enabled'] = enabled
        self.save_device_states()
        
        # If we have real Nintendo controls, apply them
        if self.real_nintendo and self.real_nintendo.is_authenticated():
            try:
                # Find the real device ID for this enhanced device
                real_device_id = self.find_real_device_id(device_id)
                if real_device_id:
                    success = self.real_nintendo.toggle_device_controls(real_device_id, enabled)
                    if success:
                        print(f"✅ {device_id}: Real Nintendo controls {'enabled' if enabled else 'disabled'}")
                        return True
                    else:
                        print(f"❌ {device_id}: Real Nintendo control toggle failed")
                        return False
                else:
                    print(f"⚠️  {device_id}: No matching real Nintendo device found")
            except Exception as e:
                print(f"❌ Error toggling real Nintendo controls for {device_id}: {e}")
        
        # If no real controls, just store the state (for UI feedback)
        print(f"💾 {device_id}: State stored (controls {'enabled' if enabled else 'disabled'})")
        print(f"⚠️  Note: Real Nintendo controls not available - state stored for future use")
        return True
    
    def set_daily_playtime_limit(self, device_id: str, minutes: int) -> bool:
        """Set daily playtime limit for a device"""
        print(f"⏰ Setting daily limit for {device_id}: {minutes} minutes")
        
        # Store the limit locally
        if device_id not in self.device_states:
            self.device_states[device_id] = {}
        
        self.device_states[device_id]['daily_limit_minutes'] = minutes
        self.save_device_states()
        
        # If we have real Nintendo controls, apply the limit
        if self.real_nintendo and self.real_nintendo.is_authenticated():
            try:
                real_device_id = self.find_real_device_id(device_id)
                if real_device_id:
                    success = self.real_nintendo.set_daily_playtime_limit(real_device_id, minutes)
                    if success:
                        print(f"✅ {device_id}: Real Nintendo daily limit set to {minutes} minutes")
                        return True
                    else:
                        print(f"❌ {device_id}: Real Nintendo limit setting failed")
                        return False
                else:
                    print(f"⚠️  {device_id}: No matching real Nintendo device found")
            except Exception as e:
                print(f"❌ Error setting real Nintendo limit for {device_id}: {e}")
        
        # If no real controls, just store the limit
        print(f"💾 {device_id}: Daily limit stored ({minutes} minutes)")
        print(f"⚠️  Note: Real Nintendo controls not available - limit stored for future use")
        return True
    
    def set_bedtime(self, device_id: str, bedtime_hour: int, bedtime_minute: int) -> bool:
        """Set bedtime for a device"""
        print(f"🌙 Setting bedtime for {device_id}: {bedtime_hour:02d}:{bedtime_minute:02d}")
        
        # Store bedtime locally
        if device_id not in self.device_states:
            self.device_states[device_id] = {}
        
        self.device_states[device_id]['bedtime'] = {'hour': bedtime_hour, 'minute': bedtime_minute}
        self.save_device_states()
        
        # If we have real Nintendo controls, apply bedtime
        if self.real_nintendo and self.real_nintendo.is_authenticated():
            try:
                real_device_id = self.find_real_device_id(device_id)
                if real_device_id:
                    success = self.real_nintendo.set_bedtime(real_device_id, bedtime_hour, bedtime_minute)
                    if success:
                        print(f"✅ {device_id}: Real Nintendo bedtime set")
                        return True
                    else:
                        print(f"❌ {device_id}: Real Nintendo bedtime setting failed")
                        return False
                else:
                    print(f"⚠️  {device_id}: No matching real Nintendo device found")
            except Exception as e:
                print(f"❌ Error setting real Nintendo bedtime for {device_id}: {e}")
        
        print(f"💾 {device_id}: Bedtime stored")
        return True
    
    def find_real_device_id(self, enhanced_device_id: str) -> Optional[str]:
        """Find the real Nintendo device ID for an enhanced discovery device"""
        if not self.real_nintendo:
            return None
        
        try:
            real_devices = self.real_nintendo.get_devices()
            
            # Try to match by device name
            for real_device in real_devices:
                if real_device['device_name'] == enhanced_device_id:
                    return real_device['device_id']
            
            # If no exact match, return None
            return None
            
        except Exception as e:
            print(f"❌ Error finding real device ID: {e}")
            return None
    
    def get_parental_control_status(self) -> Dict[str, Any]:
        """Get overall parental control status"""
        status = {
            'enhanced_discovery_available': ENHANCED_DISCOVERY_AVAILABLE,
            'real_nintendo_available': REAL_NINTENDO_AVAILABLE,
            'authenticated': self.is_authenticated(),
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'device_states_stored': len(self.device_states)
        }
        
        # Add real Nintendo status if available
        if self.real_nintendo:
            real_status = self.real_nintendo.get_parental_control_status()
            status['real_nintendo_status'] = real_status
        
        return status
    
    def start_continuous_monitoring(self, interval: int = 60):
        """Start continuous monitoring (enhanced discovery)"""
        if self.enhanced_discovery:
            try:
                self.enhanced_discovery.start_continuous_monitoring(interval)
                print(f"✅ Started continuous monitoring (every {interval}s)")
            except Exception as e:
                print(f"❌ Error starting continuous monitoring: {e}")

# Test function
def test_integrated_manager():
    """Test the integrated manager"""
    print("🧪 Testing Integrated Nintendo Switch Manager...")
    
    manager = IntegratedNintendoManager()
    
    print(f"📊 Enhanced Discovery: {'✅' if ENHANCED_DISCOVERY_AVAILABLE else '❌'}")
    print(f"📊 Real Nintendo: {'✅' if REAL_NINTENDO_AVAILABLE else '❌'}")
    print(f"📊 Authenticated: {manager.is_authenticated()}")
    
    devices = manager.get_devices()
    print(f"📊 Found {len(devices)} devices")
    
    for device in devices:
        print(f"   🎮 {device['device_name']} ({device['device_id']})")
        print(f"      Online: {device['online']}")
        print(f"      Current Game: {device['current_game']}")
        print(f"      Controls Enabled: {device['controls_enabled']}")
        print(f"      Daily Limit: {device['daily_limit_minutes']} min")
        print(f"      Real Nintendo Controls: {device.get('real_nintendo_controls', False)}")
        print(f"      Enhanced Discovery: {device.get('enhanced_discovery', False)}")

if __name__ == "__main__":
    test_integrated_manager()
