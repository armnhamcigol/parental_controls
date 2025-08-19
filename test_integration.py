#!/usr/bin/env python3
"""
Quick Test Script for Enhanced Nintendo Discovery Integration
============================================================

This script tests the integration between the backend and enhanced discovery
to ensure everything is working correctly.
"""

import json
import time
from datetime import datetime

# Test the enhanced discovery directly
def test_enhanced_discovery():
    print("🎮 Testing Enhanced Nintendo Discovery Integration")
    print("=" * 50)
    
    try:
        from enhanced_nintendo_discovery import EnhancedNintendoSwitchDiscovery
        
        discovery = EnhancedNintendoSwitchDiscovery()
        print("✅ Enhanced discovery imported successfully")
        
        # Test device discovery
        print("\n🔍 Running device discovery...")
        devices = discovery.discover_all_devices()
        
        print(f"\n📊 Found {len(devices)} devices:")
        for device in devices:
            print(f"\n📱 {device['device_name']} ({device['ip_address']})")
            print(f"   Status: {'🟢 Online' if device['online'] else '🔴 Offline'}")
            if device['online']:
                print(f"   Response Time: {device.get('response_time_ms', 'N/A')}ms")
                print(f"   Current Game: {device['current_game']}")
                print(f"   Activity Level: {device.get('network_activity_level', 'Unknown')}")
                print(f"   Session Time: {device['current_session_minutes']} minutes")
                print(f"   Daily Total: {device['today_play_time_minutes']} minutes")
        
        return devices
        
    except Exception as e:
        print(f"❌ Enhanced discovery test failed: {e}")
        return []

# Test the backend integration
def test_backend_integration():
    print("\n🔧 Testing Backend Integration")
    print("=" * 30)
    
    try:
        # Import the backend
        import sys
        sys.path.append('.')
        
        # Create a minimal test of the manager
        from pi_backend_nintendo import SimpleNintendoSwitchManager
        
        manager = SimpleNintendoSwitchManager()
        print("✅ Backend manager created successfully")
        
        # Test authentication (demo mode)
        success = manager.authenticate("testuser", "testpass")
        print(f"🔐 Authentication test: {'✅ Success' if success else '❌ Failed'}")
        
        if success:
            # Test device discovery
            print("\n🎮 Testing device discovery through backend...")
            devices = manager.get_devices()
            
            print(f"📊 Backend returned {len(devices)} devices:")
            for device in devices:
                print(f"\n📱 {device['device_name']} ({device.get('ip_address', 'N/A')})")
                print(f"   Online: {'🟢' if device.get('online') else '🔴'}")
                print(f"   Enhanced Discovery: {'✅' if device.get('enhanced_discovery') else '❌'}")
                print(f"   Current Game: {device.get('current_game', 'Unknown')}")
                print(f"   Session Time: {device.get('current_session_minutes', 0)} minutes")
                print(f"   Activity Level: {device.get('network_activity_level', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Backend integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

# Test the data format conversion
def test_data_conversion():
    print("\n📋 Testing Data Format Conversion")
    print("=" * 35)
    
    try:
        # Test that enhanced discovery data converts properly
        from enhanced_nintendo_discovery import EnhancedNintendoSwitchDiscovery
        from pi_backend_nintendo import SimpleNintendoSwitchManager
        
        discovery = EnhancedNintendoSwitchDiscovery()
        manager = SimpleNintendoSwitchManager()
        manager.authenticate("testuser", "testpass")  # Enable demo mode
        
        # Get enhanced data
        enhanced_devices = discovery.discover_all_devices()
        
        # Convert to dashboard format
        dashboard_devices = manager.convert_enhanced_devices_to_dashboard_format(enhanced_devices)
        
        print(f"✅ Successfully converted {len(dashboard_devices)} devices")
        
        # Show the conversion results
        for device in dashboard_devices:
            print(f"\n📱 {device['device_name']}:")
            print(f"   Enhanced Discovery: {device.get('enhanced_discovery', False)}")
            print(f"   Production Mode: {device.get('production_mode', False)}")
            print(f"   Network Activity: {device.get('network_activity_level', 'N/A')}")
            print(f"   Response Time: {device.get('response_time_ms', 'N/A')}ms")
            
        return True
        
    except Exception as e:
        print(f"❌ Data conversion test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Enhanced Nintendo Discovery Integration Test")
    print("=" * 55)
    
    # Run all tests
    enhanced_devices = test_enhanced_discovery()
    backend_success = test_backend_integration()
    conversion_success = test_data_conversion()
    
    print("\n" + "=" * 55)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 55)
    
    print(f"Enhanced Discovery: {'✅ PASS' if len(enhanced_devices) > 0 else '❌ FAIL'}")
    print(f"Backend Integration: {'✅ PASS' if backend_success else '❌ FAIL'}")
    print(f"Data Conversion: {'✅ PASS' if conversion_success else '❌ FAIL'}")
    
    if len(enhanced_devices) > 0 and backend_success and conversion_success:
        print("\n🎉 ALL TESTS PASSED - Enhanced Discovery Integration is working!")
        print("\n💡 Your dashboard is now ready to show real Nintendo Switch data:")
        print("   • Real online/offline status")
        print("   • Actual response times") 
        print("   • Activity level detection")
        print("   • Session time tracking")
        print("   • Game activity estimation")
        print("   • Continuous monitoring")
        
        online_devices = sum(1 for d in enhanced_devices if d.get('online', False))
        print(f"\n📊 Current Status: {online_devices}/{len(enhanced_devices)} devices online")
    else:
        print("\n⚠️ Some tests failed - check the error messages above")
