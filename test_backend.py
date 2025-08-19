#!/usr/bin/env python3
"""
Test Backend Import and Basic Functionality
"""

try:
    print("🧪 Testing backend import...")
    import pi_backend_nintendo
    print("✅ Backend imports successfully")
    
    # Test manager
    print(f"🎮 Nintendo Manager Type: {type(pi_backend_nintendo.nintendo_manager).__name__}")
    print(f"📊 Is Authenticated: {pi_backend_nintendo.nintendo_manager.is_authenticated()}")
    
    # Test enhanced discovery availability
    if hasattr(pi_backend_nintendo.nintendo_manager, 'enhanced_discovery_available'):
        print(f"📡 Enhanced Discovery: {'✅' if pi_backend_nintendo.nintendo_manager.enhanced_discovery_available else '❌'}")
    
    print("🎯 Backend test completed successfully!")
    
except Exception as e:
    print(f"❌ Backend test failed: {e}")
    import traceback
    print(f"Traceback: {traceback.format_exc()}")
