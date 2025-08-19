#!/usr/bin/env python3
"""
API Test Client for Enhanced Nintendo Discovery
==============================================

This script tests the web API endpoints to ensure the enhanced discovery
integration is working through the web interface.
"""

import requests
import json
import time

API_BASE = "http://localhost:3001"

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        print(f"🏥 Health Check: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Service: {health_data.get('service', 'Unknown')}")
            print(f"   Version: {health_data.get('version', 'Unknown')}")
            print(f"   Nintendo Status: {health_data.get('components', {}).get('nintendo', 'Unknown')}")
            return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    return False

def test_nintendo_auth():
    """Test Nintendo authentication"""
    try:
        auth_data = {
            "username": "testuser",
            "password": "testpass"
        }
        
        response = requests.post(
            f"{API_BASE}/api/nintendo/authenticate",
            json=auth_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"🔐 Nintendo Auth: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Success: {result.get('success', False)}")
            print(f"   Authenticated: {result.get('authenticated', False)}")
            print(f"   Message: {result.get('message', 'No message')}")
            return result.get('success', False)
        else:
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Nintendo auth failed: {e}")
    
    return False

def test_nintendo_devices():
    """Test getting Nintendo devices with enhanced discovery"""
    try:
        response = requests.get(f"{API_BASE}/api/nintendo/devices", timeout=30)
        
        print(f"🎮 Nintendo Devices: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            devices = result.get('devices', [])
            print(f"   Found {len(devices)} devices:")
            
            for device in devices:
                print(f"\n   📱 {device.get('device_name', 'Unknown')}")
                print(f"      IP: {device.get('ip_address', 'N/A')}")
                print(f"      Online: {'🟢' if device.get('online') else '🔴'}")
                print(f"      Enhanced: {'✅' if device.get('enhanced_discovery') else '❌'}")
                print(f"      Game: {device.get('current_game', 'Unknown')}")
                print(f"      Response Time: {device.get('response_time_ms', 'N/A')}ms")
                print(f"      Activity Level: {device.get('network_activity_level', 'N/A')}")
                print(f"      Session Time: {device.get('current_session_minutes', 0)} min")
                print(f"      Daily Time: {device.get('today_play_time_minutes', 0)} min")
                
            return len(devices) > 0
        else:
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Nintendo devices test failed: {e}")
    
    return False

def test_device_toggle():
    """Test toggling device controls"""
    try:
        toggle_data = {
            "device_id": "backroom",
            "active": True
        }
        
        response = requests.post(
            f"{API_BASE}/api/nintendo/device_toggle",
            json=toggle_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"🎛️ Device Toggle: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Success: {result.get('success', False)}")
            print(f"   Message: {result.get('message', 'No message')}")
            return result.get('success', False)
        else:
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Device toggle test failed: {e}")
    
    return False

def main():
    print("🚀 Enhanced Nintendo Discovery API Test")
    print("=" * 50)
    
    # Test sequence
    health_ok = test_health()
    print()
    
    if not health_ok:
        print("❌ Backend health check failed - is the server running?")
        return
    
    auth_ok = test_nintendo_auth()
    print()
    
    if not auth_ok:
        print("❌ Nintendo authentication failed")
        return
    
    devices_ok = test_nintendo_devices()
    print()
    
    if devices_ok:
        toggle_ok = test_device_toggle()
        print()
        
        if toggle_ok:
            print("🎉 ALL API TESTS PASSED!")
            print("\n💡 Your enhanced Nintendo discovery is working perfectly!")
            print("✅ Backend is healthy")
            print("✅ Nintendo authentication works")
            print("✅ Enhanced device discovery is active")
            print("✅ Device controls can be toggled")
            print("\n🌐 Ready to use the web dashboard at:")
            print("   http://localhost:3001")
        else:
            print("⚠️ Device toggle test failed, but discovery is working")
    else:
        print("❌ Device discovery failed")

if __name__ == "__main__":
    main()
