#!/usr/bin/env python3
"""
Test MCP Server with Qwen Integration
"""

import os
import sys
import json
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.mcp_server import MCPOrchestrator

# Mock managers for testing
class MockOPNsenseManager:
    def get_parental_control_status(self):
        return {"controls_active": False, "alias_exists": True}
    
    def create_or_update_mac_alias(self):
        return True
    
    def toggle_parental_controls(self, active):
        print(f"[MOCK] Toggling parental controls: {active}")
        return True

class MockMACManager:
    def get_enabled_devices(self):
        return [{"id": 1, "name": "Test Device", "mac": "AA:BB:CC:DD:EE:FF"}]
    
    def get_all_devices(self):
        return [{"id": 1, "name": "Test Device", "mac": "AA:BB:CC:DD:EE:FF"}]
    
    def add_device(self, name, mac):
        print(f"[MOCK] Adding device: {name} ({mac})")
        return {"id": 2, "name": name, "mac": mac}

class MockNintendoManager:
    def get_parental_control_status(self):
        return {"enabled": False, "playtime_limit": 120}
    
    def enable_parental_controls(self):
        return True
    
    def disable_parental_controls(self):
        return True

def test_mcp_integration():
    """Test MCP orchestrator with Qwen model"""
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Initialize mock managers
    opnsense_mgr = MockOPNsenseManager()
    mac_mgr = MockMACManager()
    nintendo_mgr = MockNintendoManager()
    
    # Initialize MCP orchestrator with Qwen
    mcp = MCPOrchestrator(
        opnsense_manager=opnsense_mgr,
        mac_manager=mac_mgr,
        nintendo_manager=nintendo_mgr,
        ollama_host="http://192.168.123.240:8034",
        ollama_model="qwen2.5:7b-instruct-q8_0",
        logger=logger
    )
    
    print("🤖 Testing MCP Server with Qwen Integration")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        "What is the current system status?",
        "Block all devices now",
        "Show me all devices",
        "Add a new device named Test Phone with MAC address BB:CC:DD:EE:FF:AA"
    ]
    
    session_id = "test_session_123"
    
    for i, test_message in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_message}")
        print("-" * 30)
        
        try:
            result = mcp.chat(session_id, test_message)
            
            if result.get('success'):
                print(f"✅ Success!")
                print(f"🤖 AI Reply: {result.get('reply', '')}")
                
                if result.get('tool_calls'):
                    print(f"🔨 Tools Called: {', '.join(result['tool_calls'])}")
                    
                    for j, tool_result in enumerate(result.get('tool_results', [])):
                        status = "✅" if tool_result.get('success') else "❌"
                        print(f"   {status} Tool {j+1}: {tool_result}")
                        
                print(f"⏱️  Response Time: {result.get('response_time_ms', 0)}ms")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print()
    
    print("✅ All tests completed!")

if __name__ == "__main__":
    test_mcp_integration()
