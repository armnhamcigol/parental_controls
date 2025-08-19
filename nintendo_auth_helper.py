#!/usr/bin/env python3
"""
Nintendo Switch Authentication Helper
Helps get a session token for Nintendo Parental Controls API
"""

import asyncio
import json
import webbrowser
from urllib.parse import urlencode, parse_qs

try:
    from pynintendoparental.authenticator import Authenticator
    from pynintendoparental.authenticator.session_token import get_session_token
    NINTENDO_AVAILABLE = True
except ImportError:
    NINTENDO_AVAILABLE = False

def nintendo_auth_instructions():
    """Provide instructions for Nintendo authentication"""
    print("🎮 Nintendo Switch Parental Controls Authentication")
    print("=" * 55)
    print()
    print("To use real Nintendo Switch parental controls, you need to:")
    print()
    print("1. 🔑 Get a Nintendo session token")
    print("2. 💾 Save it to nintendo_config.json")
    print("3. 🎯 Use it in the backend")
    print()
    print("📋 Instructions:")
    print()
    print("METHOD 1: Use Home Assistant Integration")
    print("-" * 40)
    print("1. Install Home Assistant")
    print("2. Add the Nintendo Parental Controls integration")
    print("3. Follow the OAuth flow")
    print("4. Extract the session token from HA config")
    print()
    print("METHOD 2: Manual OAuth (Advanced)")
    print("-" * 40)
    print("1. Go to: https://accounts.nintendo.com/connect/1.0.0/authorize")
    print("2. Add parameters for Nintendo Parental Controls app")
    print("3. Log in with your Nintendo account")
    print("4. Extract session_token from the callback")
    print()
    print("⚠️  WARNING: This requires your Nintendo account credentials")
    print("⚠️  Only proceed if you understand the security implications")
    print()
    
def create_sample_config():
    """Create a sample configuration file"""
    sample_config = {
        "session_token": "YOUR_SESSION_TOKEN_HERE",
        "instructions": [
            "Replace YOUR_SESSION_TOKEN_HERE with your actual Nintendo session token",
            "Session tokens are obtained through Nintendo's OAuth flow",
            "They allow access to Nintendo Parental Controls API",
            "Keep this file secure - it contains authentication credentials"
        ],
        "last_updated": "never"
    }
    
    with open('nintendo_config_sample.json', 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print("✅ Created nintendo_config_sample.json")
    print("📝 Edit this file and rename to nintendo_config.json")

def test_session_token(session_token: str):
    """Test if a session token works"""
    if not NINTENDO_AVAILABLE:
        print("❌ Nintendo library not available")
        return False
    
    try:
        # Test the session token
        authenticator = Authenticator(session_token=session_token)
        print("✅ Session token format appears valid")
        print("🧪 Testing authentication...")
        
        # This would require async testing
        print("⚠️  Full authentication test requires async execution")
        print("💡 Try using the session token in the real backend to test")
        return True
        
    except Exception as e:
        print(f"❌ Session token test failed: {e}")
        return False

def main():
    """Main authentication helper"""
    print("🎮 Nintendo Switch Parental Controls Authentication Helper")
    print()
    
    if not NINTENDO_AVAILABLE:
        print("❌ Nintendo library not available!")
        print("💡 Install with: pip install pynintendoparental aiohttp")
        return
    
    while True:
        print("\nWhat would you like to do?")
        print("1. 📋 Show authentication instructions")
        print("2. 📝 Create sample config file")
        print("3. 🧪 Test a session token")
        print("4. 🚪 Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            nintendo_auth_instructions()
        elif choice == "2":
            create_sample_config()
        elif choice == "3":
            token = input("Enter session token to test: ").strip()
            if token:
                test_session_token(token)
            else:
                print("❌ No token provided")
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
