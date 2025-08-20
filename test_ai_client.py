#!/usr/bin/env python3
"""
Interactive Test Client for AI Parental Controls
Tests the AI functionality with real HTTP requests
"""

import requests
import json
import time
from datetime import datetime

class AITestClient:
    def __init__(self, base_url="http://127.0.0.1:5000", api_key="test-api-key-staging-12345"):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session_id = f"test_session_{int(time.time())}"
        
    def test_basic_endpoints(self):
        """Test basic server endpoints"""
        print("🔍 Testing Basic Server Endpoints")
        print("=" * 40)
        
        endpoints = [
            ("/", "Main Dashboard"),
            ("/health", "Health Check"),
            ("/api/status", "System Status")
        ]
        
        for endpoint, name in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                status = "✅ OK" if response.ok else f"❌ {response.status_code}"
                print(f"{status} {name}: {endpoint}")
                
                if endpoint == "/api/status" and response.ok:
                    data = response.json()
                    if data.get('success'):
                        print(f"    Controls Active: {data.get('controlsActive', 'unknown')}")
                        print(f"    Devices: {data.get('devices', {}).get('total', 0)} total")
                
            except Exception as e:
                print(f"❌ {name}: Error - {str(e)[:50]}")
        
        print()
    
    def test_ai_chat(self, message):
        """Test AI chat functionality"""
        print(f"🤖 Testing AI Chat: '{message}'")
        print("-" * 50)
        
        try:
            payload = {
                "session_id": self.session_id,
                "message": message
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-Api-Key": self.api_key
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/ai-staging/chat",
                json=payload,
                headers=headers,
                timeout=30
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.ok:
                data = response.json()
                if data.get('success'):
                    print(f"✅ Success! ({response_time:.0f}ms)")
                    print(f"🤖 AI Reply: {data.get('reply', 'No reply')}")
                    
                    if data.get('tool_calls'):
                        print(f"🔨 Tools Called: {', '.join(data['tool_calls'])}")
                        
                        for i, result in enumerate(data.get('tool_results', [])):
                            status = "✅" if result.get('success') else "❌"
                            print(f"   {status} Tool {i+1}: {result.get('message', str(result)[:100])}")
                else:
                    print(f"❌ AI Error: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Request Error: {e}")
        
        print()
    
    def test_ai_page_access(self):
        """Test if AI page loads"""
        print("🌐 Testing AI Page Access")
        print("-" * 30)
        
        try:
            response = requests.get(f"{self.base_url}/ai-staging", timeout=10)
            if response.ok:
                if "AI Assistant" in response.text and "chat" in response.text.lower():
                    print("✅ AI page loads correctly")
                    print(f"📄 Page size: {len(response.text)} characters")
                else:
                    print("⚠️  AI page loads but content may be incorrect")
            else:
                print(f"❌ AI page failed to load: {response.status_code}")
        except Exception as e:
            print(f"❌ AI page access error: {e}")
        
        print()
    
    def run_comprehensive_test(self):
        """Run comprehensive test suite"""
        print(f"🧪 AI Parental Controls Test Suite")
        print(f"Time: {datetime.now().isoformat()}")
        print(f"Server: {self.base_url}")
        print(f"Session: {self.session_id}")
        print("=" * 60)
        
        # Test basic endpoints
        self.test_basic_endpoints()
        
        # Test AI page access
        self.test_ai_page_access()
        
        # Test AI chat functionality with various commands
        test_messages = [
            "Hello! What is the current system status?",
            "Show me all devices that are being managed",
            "Block all devices now",
            "Allow internet access for all devices", 
            "Add a new device named Test iPhone with MAC address AA:BB:CC:DD:EE:FF",
            "What Nintendo controls are available?"
        ]
        
        for message in test_messages:
            self.test_ai_chat(message)
            time.sleep(2)  # Small delay between requests
        
        print("🎯 Test Summary:")
        print("✅ If you see AI replies and tool executions above, the integration is working!")
        print("🌐 You can now open: http://127.0.0.1:5000/ai-staging in your browser")
        print(f"🔑 Use API Key: {self.api_key}")

if __name__ == "__main__":
    # Check if server is running first
    try:
        response = requests.get("http://127.0.0.1:5000/health", timeout=5)
        if not response.ok:
            print("❌ Server doesn't appear to be running on port 5000")
            print("Please start the server first with: python start_test_server.py")
            exit(1)
    except:
        print("❌ Cannot connect to server on port 5000")
        print("Please start the server first with: python start_test_server.py")
        exit(1)
    
    # Run tests
    client = AITestClient()
    client.run_comprehensive_test()
