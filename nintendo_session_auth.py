#!/usr/bin/env python3
"""
Nintendo Session Authentication Helper
Helps set up and test Nintendo API authentication for parental controls
"""

import json
import os
import asyncio
import getpass
from datetime import datetime
from pathlib import Path

# Check for required dependencies
try:
    import pynintendoparental
    NINTENDO_LIB_AVAILABLE = True
    print("✅ pynintendoparental library found")
except ImportError:
    NINTENDO_LIB_AVAILABLE = False
    print("❌ pynintendoparental library not found")

def create_sample_config():
    """Create a sample Nintendo configuration file"""
    sample_config = {
        "session_token": "",
        "device_mapping": {
            "example_device_1": "real_nintendo_device_id_1",
            "example_device_2": "real_nintendo_device_id_2"
        },
        "last_updated": datetime.now().isoformat(),
        "setup_completed": False
    }
    
    config_path = "nintendo_config.json"
    
    try:
        with open(config_path, 'w') as f:
            json.dump(sample_config, f, indent=2)
        print(f"✅ Created sample config: {config_path}")
        print("📝 Edit this file to add your actual session token")
        return True
    except Exception as e:
        print(f"❌ Error creating config: {e}")
        return False

def load_config():
    """Load Nintendo configuration"""
    config_path = "nintendo_config.json"
    
    if not Path(config_path).exists():
        print(f"⚠️  Config file not found: {config_path}")
        return None
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        print(f"✅ Loaded config from: {config_path}")
        return config
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None

def save_config(config):
    """Save Nintendo configuration"""
    config_path = "nintendo_config.json"
    config['last_updated'] = datetime.now().isoformat()
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Config saved to: {config_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving config: {e}")
        return False

async def test_session_token(session_token):
    """Test if a session token works"""
    if not NINTENDO_LIB_AVAILABLE:
        print("❌ Cannot test session token - pynintendoparental not available")
        return False
    
    try:
        print("🧪 Testing session token...")
        
        # Initialize the authenticator with the session token
        auth = await pynintendoparental.Authenticator.complete_login(None, session_token, True)
        
        if auth:
            print("✅ Session token authentication successful!")
            
            # Create Nintendo Parental API instance
            nintendo_api = await pynintendoparental.NintendoParental.create(auth)
            
            # Try to get account devices
            devices_data = await nintendo_api._api.async_get_account_devices()
            devices = devices_data.get('devices', [])
            
            print(f"📱 Found {len(devices)} Nintendo devices:")
            
            for device in devices:
                device_name = device.get('name', 'Unknown')
                device_id = device.get('deviceId', 'Unknown')
                print(f"   🎮 {device_name} (ID: {device_id})")
            
            return True
        else:
            print("❌ Session token authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing session token: {e}")
        import traceback
        print(f"Debug traceback: {traceback.format_exc()}")
        return False

def setup_manual_token():
    """Manual session token setup"""
    print("\n🔧 Manual Session Token Setup")
    print("=" * 50)
    
    print("\n📋 To get a Nintendo session token:")
    print("1. Install and use 'nxapi' tool: https://github.com/samuelthomas2774/nxapi")
    print("2. Or use browser developer tools on accounts.nintendo.com")
    print("3. Or use the Nintendo Switch Parental Controls app")
    print("\n⚠️  Session tokens are long-lived but may expire")
    print("⚠️  Keep your session token secure - it provides full account access")
    
    # Get session token from user
    print("\n🔑 Enter your Nintendo session token:")
    session_token = getpass.getpass("Session Token (hidden input): ").strip()
    
    if not session_token:
        print("❌ No session token provided")
        return False
    
    # Load or create config
    config = load_config()
    if not config:
        print("📝 Creating new config...")
        config = {
            "session_token": "",
            "device_mapping": {},
            "last_updated": "",
            "setup_completed": False
        }
    
    # Update config with new token
    config['session_token'] = session_token
    config['setup_completed'] = True
    
    # Save config
    if save_config(config):
        print("✅ Session token saved to configuration")
        return True
    else:
        return False

async def full_setup_and_test():
    """Complete setup and testing workflow"""
    print("🎮 Nintendo Switch Authentication Setup")
    print("=" * 50)
    
    # Check if config exists
    config = load_config()
    
    if not config:
        print("📝 No configuration found. Creating sample config...")
        create_sample_config()
        config = load_config()
    
    # Check if session token is configured
    if not config or not config.get('session_token'):
        print("\n⚙️  Session token not configured")
        
        choice = input("\nWould you like to set up the session token now? (y/n): ").lower().strip()
        
        if choice == 'y':
            if setup_manual_token():
                config = load_config()  # Reload updated config
            else:
                print("❌ Session token setup failed")
                return False
        else:
            print("ℹ️  Setup skipped. You can run this again later.")
            return False
    
    # Test the session token
    if config and config.get('session_token'):
        print(f"\n🧪 Testing configured session token...")
        
        session_token = config['session_token']
        success = await test_session_token(session_token)
        
        if success:
            print("\n🎉 Nintendo authentication setup complete!")
            print("✅ Your Nintendo Switch parental controls are ready to use")
            
            # Update config to mark setup as complete
            config['setup_completed'] = True
            config['last_tested'] = datetime.now().isoformat()
            save_config(config)
            
            return True
        else:
            print("\n❌ Session token test failed")
            print("💡 You may need to generate a new session token")
            
            # Mark setup as incomplete
            config['setup_completed'] = False
            save_config(config)
            
            return False
    
    return False

def show_current_status():
    """Show current authentication status"""
    print("📊 Current Nintendo Authentication Status")
    print("=" * 50)
    
    print(f"📚 pynintendoparental library: {'✅ Available' if NINTENDO_LIB_AVAILABLE else '❌ Not available'}")
    
    config = load_config()
    if config:
        has_token = bool(config.get('session_token'))
        is_setup = config.get('setup_completed', False)
        last_updated = config.get('last_updated', 'Never')
        last_tested = config.get('last_tested', 'Never')
        
        print(f"🔧 Configuration file: ✅ Found")
        print(f"🔑 Session token: {'✅ Configured' if has_token else '❌ Not configured'}")
        print(f"✅ Setup completed: {'✅ Yes' if is_setup else '❌ No'}")
        print(f"📅 Last updated: {last_updated}")
        print(f"🧪 Last tested: {last_tested}")
        
        if config.get('device_mapping'):
            print(f"📱 Device mapping: {len(config['device_mapping'])} entries")
            for local_name, nintendo_id in config['device_mapping'].items():
                print(f"   🎮 {local_name} → {nintendo_id}")
    else:
        print(f"🔧 Configuration file: ❌ Not found")
    
    print()

def main():
    """Main menu"""
    while True:
        print("\n🎮 Nintendo Switch Authentication Helper")
        print("=" * 50)
        print("1. Show current status")
        print("2. Create sample configuration")
        print("3. Set up session token")
        print("4. Test session token")
        print("5. Complete setup and test")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == '1':
            show_current_status()
            
        elif choice == '2':
            create_sample_config()
            
        elif choice == '3':
            setup_manual_token()
            
        elif choice == '4':
            config = load_config()
            if config and config.get('session_token'):
                asyncio.run(test_session_token(config['session_token']))
            else:
                print("❌ No session token configured")
                
        elif choice == '5':
            asyncio.run(full_setup_and_test())
            
        elif choice == '6':
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid option. Please choose 1-6.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
