#!/usr/bin/env python3
"""
Comprehensive Test Suite for Qwen Model Capabilities
Tests function calling, reasoning, code generation, and other features needed for MCP integration
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional

class QwenModelTester:
    def __init__(self, base_url: str = "http://192.168.123.240:8034", model: str = "qwen2.5:7b-instruct-q8_0"):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.generate_url = f"{self.base_url}/api/generate"
        self.chat_url = f"{self.base_url}/api/chat"
        self.tags_url = f"{self.base_url}/api/tags"
        
    def make_request(self, url: str, payload: Dict) -> Optional[Dict]:
        """Make API request with error handling"""
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode failed: {e}")
            return None

    def test_basic_connectivity(self) -> bool:
        """Test basic model connectivity"""
        print("\n🔗 Testing Basic Connectivity...")
        
        payload = {
            "model": self.model,
            "prompt": "Hello! Please respond with exactly: 'Model is working correctly.'",
            "stream": False
        }
        
        result = self.make_request(self.generate_url, payload)
        if result and 'response' in result:
            response = result['response'].strip()
            print(f"✅ Model Response: {response}")
            return True
        
        print("❌ Basic connectivity test failed")
        return False

    def test_available_endpoints(self):
        """Test what endpoints are available"""
        print("\n🌐 Testing Available Endpoints...")
        
        endpoints_to_test = [
            ("/api/generate", "generate endpoint"),
            ("/api/chat", "chat endpoint"),
            ("/api/tags", "tags endpoint"),
            ("/", "root endpoint")
        ]
        
        for endpoint, description in endpoints_to_test:
            try:
                url = f"{self.base_url}{endpoint}"
                if endpoint == "/api/tags":
                    response = requests.get(url, timeout=10)
                else:
                    # Try a minimal payload
                    test_payload = {"model": self.model, "prompt": "test"} if endpoint == "/api/generate" else {"model": self.model, "messages": [{"role": "user", "content": "test"}]}
                    response = requests.post(url, json=test_payload, timeout=10)
                
                if response.status_code in [200, 404, 405]:  # 405 Method Not Allowed is ok for discovery
                    print(f"✅ {description}: Available (Status: {response.status_code})")
                else:
                    print(f"⚠️ {description}: Status {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {description}: Failed - {str(e)[:100]}")

    def test_chat_endpoint(self) -> bool:
        """Test if chat endpoint works (needed for function calling)"""
        print("\n💬 Testing Chat Endpoint...")
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": "Say exactly: 'Chat endpoint working'"}
            ],
            "stream": False
        }
        
        result = self.make_request(self.chat_url, payload)
        if result and 'message' in result:
            response = result['message'].get('content', '').strip()
            print(f"✅ Chat Response: {response}")
            return True
        
        print("❌ Chat endpoint test failed")
        return False

    def test_function_calling_simple(self) -> bool:
        """Test basic function calling capability"""
        print("\n🔧 Testing Function Calling (Simple)...")
        
        # Define a simple function for testing
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "Get the current time",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": "What time is it? Use the get_current_time function."}
            ],
            "tools": tools,
            "stream": False
        }
        
        result = self.make_request(self.chat_url, payload)
        if result:
            print(f"📋 Raw Response: {json.dumps(result, indent=2)[:500]}...")
            
            # Check for tool calls in response
            message = result.get('message', {})
            if 'tool_calls' in message:
                print("✅ Function calling supported!")
                print(f"🔨 Tool calls: {message['tool_calls']}")
                return True
            else:
                print("⚠️ No tool_calls in response - may not support function calling")
                return False
        
        print("❌ Function calling test failed")
        return False

    def test_function_calling_complex(self) -> bool:
        """Test complex function calling with parental control functions"""
        print("\n⚙️ Testing Function Calling (Complex - Parental Controls)...")
        
        # Define parental control functions similar to our MCP server
        tools = [
            {
                "type": "function", 
                "function": {
                    "name": "toggle_parental_controls",
                    "description": "Enable or disable network-level parental controls",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "active": {
                                "type": "boolean",
                                "description": "True to enable blocking, false to disable"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Reason for the change"
                            }
                        },
                        "required": ["active"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_device",
                    "description": "Add a device to parental controls",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Device name"
                            },
                            "mac": {
                                "type": "string",
                                "description": "MAC address in format AA:BB:CC:DD:EE:FF"
                            }
                        },
                        "required": ["name", "mac"]
                    }
                }
            }
        ]
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": "Please block all devices and add a new device called 'Test Phone' with MAC address 'AA:BB:CC:DD:EE:FF'. Use the appropriate functions."}
            ],
            "tools": tools,
            "stream": False
        }
        
        result = self.make_request(self.chat_url, payload)
        if result:
            print(f"📋 Complex Function Call Response: {json.dumps(result, indent=2)[:800]}...")
            
            message = result.get('message', {})
            if 'tool_calls' in message and message['tool_calls']:
                print("✅ Complex function calling works!")
                print(f"🔨 Tool calls found: {len(message['tool_calls'])}")
                for i, tool_call in enumerate(message['tool_calls']):
                    print(f"   {i+1}. {tool_call}")
                return True
            else:
                print("⚠️ Complex function calling may not be supported")
                return False
        
        return False

    def test_reasoning_capability(self) -> bool:
        """Test the model's reasoning capability"""
        print("\n🧠 Testing Reasoning Capability...")
        
        payload = {
            "model": self.model,
            "prompt": """
You are a parental control assistant. A parent asks: "My child has been on their device for 3 hours today, and our daily limit is 2 hours. Should I block their access now?"

Please provide a reasoned response that considers:
1. The current usage vs limit
2. Potential consequences of immediate blocking
3. Alternative approaches
4. What action you recommend and why

Format your response with clear reasoning steps.
""",
            "stream": False
        }
        
        result = self.make_request(self.generate_url, payload)
        if result and 'response' in result:
            response = result['response']
            print(f"✅ Reasoning Response: {response[:500]}...")
            
            # Check for reasoning indicators
            reasoning_indicators = ['because', 'therefore', 'consider', 'recommend', 'however', 'alternatively']
            if any(indicator in response.lower() for indicator in reasoning_indicators):
                print("✅ Model shows good reasoning capability")
                return True
            else:
                print("⚠️ Limited reasoning capability detected")
                return False
        
        print("❌ Reasoning test failed")
        return False

    def test_json_output(self) -> bool:
        """Test if model can produce structured JSON output"""
        print("\n📋 Testing JSON Output Capability...")
        
        payload = {
            "model": self.model,
            "prompt": """
Please respond with ONLY valid JSON containing information about a parental control status:

{
  "controls_active": true,
  "blocked_devices": 3,
  "total_devices": 5,
  "last_action": "Manual toggle",
  "timestamp": "2025-08-19T22:55:00Z"
}

Respond with ONLY the JSON, no additional text.
""",
            "stream": False
        }
        
        result = self.make_request(self.generate_url, payload)
        if result and 'response' in result:
            response = result['response'].strip()
            print(f"📄 JSON Response: {response}")
            
            try:
                parsed = json.loads(response)
                print("✅ Valid JSON output capability confirmed")
                print(f"🔍 Parsed: {parsed}")
                return True
            except json.JSONDecodeError:
                print("⚠️ Model doesn't consistently produce valid JSON")
                return False
        
        print("❌ JSON output test failed")
        return False

    def test_model_info(self):
        """Get information about the model"""
        print("\n📊 Getting Model Information...")
        
        try:
            # Try to get model list
            response = requests.get(self.tags_url, timeout=10)
            if response.ok:
                tags_data = response.json()
                print(f"📋 Available Models: {json.dumps(tags_data, indent=2)}")
            else:
                print(f"⚠️ Could not get model list: {response.status_code}")
        except Exception as e:
            print(f"❌ Model info request failed: {e}")

    def test_context_window(self) -> bool:
        """Test the model's context window with a longer prompt"""
        print("\n📏 Testing Context Window...")
        
        # Create a longer prompt to test context handling
        long_context = "Here is some background information: " + "This is repeated context. " * 100
        
        payload = {
            "model": self.model,
            "prompt": f"{long_context}\n\nBased on all the context above, please respond with: 'Context processed successfully'",
            "stream": False
        }
        
        result = self.make_request(self.generate_url, payload)
        if result and 'response' in result:
            response = result['response'].strip()
            print(f"✅ Long Context Response: {response[:200]}...")
            return "Context processed" in response or "successfully" in response
        
        print("❌ Context window test failed")  
        return False

    def run_full_test_suite(self):
        """Run the complete test suite"""
        print("🧪 Starting Comprehensive Qwen Model Test Suite")
        print("=" * 60)
        
        results = {}
        
        # Run all tests
        test_methods = [
            ("Basic Connectivity", self.test_basic_connectivity),
            ("Available Endpoints", self.test_available_endpoints),
            ("Chat Endpoint", self.test_chat_endpoint), 
            ("Function Calling (Simple)", self.test_function_calling_simple),
            ("Function Calling (Complex)", self.test_function_calling_complex),
            ("Reasoning Capability", self.test_reasoning_capability),
            ("JSON Output", self.test_json_output),
            ("Context Window", self.test_context_window)
        ]
        
        for test_name, test_method in test_methods:
            if test_method == self.test_available_endpoints or test_method == self.test_model_info:
                test_method()  # These don't return bool
                continue
                
            try:
                result = test_method()
                results[test_name] = result
                time.sleep(1)  # Brief pause between tests
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        # Get model info
        self.test_model_info()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n🎯 Overall Score: {passed}/{total} ({passed/total*100:.1f}%)")
        
        # MCP Compatibility Assessment
        print("\n🤖 MCP INTEGRATION ASSESSMENT:")
        
        function_calling_works = results.get("Function Calling (Simple)", False) or results.get("Function Calling (Complex)", False)
        chat_endpoint_works = results.get("Chat Endpoint", False)
        reasoning_works = results.get("Reasoning Capability", False)
        
        if function_calling_works and chat_endpoint_works:
            print("✅ HIGH COMPATIBILITY: Model supports function calling and chat endpoint - Perfect for MCP!")
        elif chat_endpoint_works and reasoning_works:
            print("⚠️ MEDIUM COMPATIBILITY: Model has chat endpoint and reasoning - May work with MCP with modifications")
        else:
            print("❌ LOW COMPATIBILITY: Model lacks essential features for MCP integration")
        
        return results

if __name__ == "__main__":
    tester = QwenModelTester()
    results = tester.run_full_test_suite()
