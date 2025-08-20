#!/usr/bin/env python3
"""
Quick Test Suite for AI Parental Controls
Run various commands to test the AI assistant functionality
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"
API_KEY = "test-api-key-staging-12345"

def send_ai_command(message):
    """Send a command to the AI assistant"""
    url = f"{BASE_URL}/api/ai-staging/chat"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    payload = {
        "message": message,
        "session_id": "test-session"
    }
    
    print(f"\n🤖 Sending: '{message}'")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        
        # Print the AI response
        if 'response' in result:
            print(f"💬 AI Response: {result['response']}")
        
        # Print any tool executions
        if 'tool_executions' in result:
            print(f"\n🔧 Tools Used: {len(result['tool_executions'])}")
            for i, tool in enumerate(result['tool_executions']):
                print(f"   {i+1}. {tool.get('tool_name', 'Unknown')} -> {tool.get('status', 'Unknown')}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode failed: {e}")
        return False

def test_basic_commands():
    """Test basic AI commands"""
    print("🧪 TESTING BASIC COMMANDS")
    print("=" * 60)
    
    test_commands = [
        "What is the current system status?",
        "Show me all the devices in the system",
        "Block all devices now",
        "What's the status now?", 
        "Turn off parental controls",
        "Check the current status"
    ]
    
    for command in test_commands:
        success = send_ai_command(command)
        if not success:
            print(f"❌ Failed: {command}")
        time.sleep(2)  # Brief pause between commands

def test_device_management():
    """Test device management commands"""
    print("\n🔧 TESTING DEVICE MANAGEMENT")
    print("=" * 60)
    
    device_commands = [
        "Add a new device called 'Test iPhone' with MAC address 'AA:BB:CC:DD:EE:01'",
        "List all devices again",
        "Update the device named 'Test iPhone' to have MAC address 'AA:BB:CC:DD:EE:02'",
        "Remove the device named 'Test iPhone'",
        "Show me the final device list"
    ]
    
    for command in device_commands:
        success = send_ai_command(command)
        if not success:
            print(f"❌ Failed: {command}")
        time.sleep(2)

def test_conversational_ai():
    """Test conversational AI capabilities"""
    print("\n💭 TESTING CONVERSATIONAL AI")
    print("=" * 60)
    
    conversation_commands = [
        "I want to limit my child's internet access during homework time. What should I do?",
        "How many devices do we currently have configured?",
        "Can you help me understand what happens when I block devices?",
        "Is there a way to temporarily disable controls for 10 minutes?"
    ]
    
    for command in conversation_commands:
        success = send_ai_command(command)
        if not success:
            print(f"❌ Failed: {command}")
        time.sleep(3)  # Longer pause for conversational responses

def check_server_health():
    """Check if server is running and healthy"""
    print("🏥 CHECKING SERVER HEALTH")
    print("=" * 60)
    
    try:
        # Check main status endpoint
        response = requests.get(f"{BASE_URL}/api/status")
        if response.ok:
            status = response.json()
            print("✅ Server is healthy")
            print(f"📊 Status: {json.dumps(status, indent=2)}")
            return True
        else:
            print(f"❌ Server unhealthy: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Cannot reach server: {e}")
        return False

if __name__ == "__main__":
    print("🚀 AI PARENTAL CONTROLS TEST SUITE")
    print("=" * 60)
    
    # Check server health first
    if not check_server_health():
        print("❌ Server is not responding. Make sure to run: python run_server.py")
        exit(1)
    
    print("\n⚡ Starting comprehensive tests...")
    
    # Run test suites
    test_basic_commands()
    test_device_management() 
    test_conversational_ai()
    
    print("\n" + "=" * 60)
    print("🎯 TEST SUITE COMPLETED!")
    print("Check the server logs for detailed execution information.")
    print("=" * 60)
