#!/usr/bin/env python3
"""
Test Nintendo Switch Integration
"""

# Import the integrated Nintendo manager
try:
    from integrated_nintendo_manager import IntegratedNintendoManager
    INTEGRATED_MANAGER_AVAILABLE = True
    print("✅ Integrated Nintendo Manager available")
except ImportError as e:
    INTEGRATED_MANAGER_AVAILABLE = False
    print(f"❌ Integrated Manager not available: {e}")

# Test the manager
if INTEGRATED_MANAGER_AVAILABLE:
    print("\n🧪 Testing Integrated Nintendo Manager...")
    
    manager = IntegratedNintendoManager()
    
    print(f"📊 Authenticated: {manager.is_authenticated()}")
    print(f"📊 Enhanced Discovery: {'✅' if manager.enhanced_discovery else '❌'}")
    print(f"📊 Real Nintendo: {'✅' if manager.real_nintendo else '❌'}")
    
    if manager.real_nintendo and manager.is_authenticated():
        print("\n🔍 Testing real Nintendo controls...")
        try:
            status = manager.get_parental_control_status()
            print("✅ Status retrieved successfully")
            print(f"   Enhanced Discovery: {status.get('enhanced_discovery_available', False)}")
            print(f"   Real Nintendo: {status.get('real_nintendo_available', False)}")
            print(f"   Authenticated: {status.get('authenticated', False)}")
        except Exception as e:
            print(f"❌ Status retrieval failed: {e}")
    
    # Test device discovery
    print("\n🔍 Testing device discovery...")
    try:
        devices = manager.get_devices()
        print(f"✅ Found {len(devices)} devices")
        
        for device in devices:
            print(f"   🎮 {device['device_name']} ({device['device_id']})")
            print(f"      Online: {device.get('online', 'Unknown')}")
            print(f"      Enhanced Discovery: {device.get('enhanced_discovery', False)}")
            print(f"      Real Nintendo Controls: {device.get('real_nintendo_controls', False)}")
            
    except Exception as e:
        print(f"❌ Device discovery failed: {e}")

else:
    print("\n⚠️  Cannot test - Integrated Manager not available")

print("\n🎯 Test completed!")
