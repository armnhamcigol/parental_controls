#!/usr/bin/env python3
"""
MCP Server Module for Parental Controls AI Assistant
Integrates with Ollama for conversational AI control over parental controls
"""

import os
import re
import json
import time
import logging
import hashlib
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from flask import Flask, request, jsonify, render_template_string


class MCPOrchestrator:
    """Orchestrates AI chat with tool calling for parental controls"""
    
    def __init__(self, opnsense_manager, mac_manager, nintendo_manager, 
                 ollama_host: str, ollama_model: str, logger: logging.Logger = None):
        self.opnsense_manager = opnsense_manager
        self.mac_manager = mac_manager
        self.nintendo_manager = nintendo_manager
        self.ollama_host = ollama_host.rstrip('/')
        self.ollama_model = ollama_model
        self.logger = logger or logging.getLogger(__name__)
        
        # Simple in-memory session store for conversation history
        self.sessions = {}
        
        # Rate limiting: simple token bucket per session
        self.rate_limits = {}
        self.rate_limit_per_minute = 10
        
        # System prompt for consistent AI behavior
        self.system_prompt = """You are the Parental Controls AI assistant. You help manage network access and Nintendo Switch restrictions through OPNsense firewall and device control.

Key guidelines:
- Always confirm potentially disruptive actions before executing them
- Provide clear summaries of what you're doing and results
- If you need device information, fetch it first with get_devices - never fabricate device IDs
- When operations fail, explain the error clearly and suggest next steps
- Be concise but informative in your responses
- Use tools when action is requested by the user

Available capabilities:
- Network blocking: Enable/disable parental controls for all managed devices
- Device management: Add, update, remove devices from control lists
- Nintendo controls: Manage Nintendo Switch parental controls, playtime limits, bedtime restrictions
- Status monitoring: Check system status and device information

Always prioritize safety and ask for clarification when requests are ambiguous."""

    def _log_audit(self, session_id: str, user_message: str, tools_invoked: List[str], 
                   tool_results: List[Dict], response_time_ms: int, error: str = None):
        """Log AI assistant interactions for audit purposes"""
        try:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            # Hash the user message for privacy while maintaining uniqueness
            message_hash = hashlib.sha256(user_message.encode()).hexdigest()[:16]
            
            audit_entry = {
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'user_message_hash': message_hash,
                'user_message_length': len(user_message),
                'tools_invoked': tools_invoked,
                'tool_success_count': sum(1 for r in tool_results if r.get('success', False)),
                'tool_error_count': sum(1 for r in tool_results if not r.get('success', False)),
                'response_time_ms': response_time_ms,
                'error': error
            }
            
            log_file = os.path.join(log_dir, 'ai_assistant.log')
            with open(log_file, 'a') as f:
                f.write(json.dumps(audit_entry) + '\n')
                
        except Exception as e:
            self.logger.error(f"Failed to write audit log: {e}")

    def _check_rate_limit(self, session_id: str) -> bool:
        """Simple token bucket rate limiting per session"""
        now = time.time()
        
        if session_id not in self.rate_limits:
            self.rate_limits[session_id] = {
                'tokens': self.rate_limit_per_minute,
                'last_refill': now
            }
        
        bucket = self.rate_limits[session_id]
        
        # Refill tokens based on time passed
        time_passed = now - bucket['last_refill']
        tokens_to_add = int(time_passed / 60 * self.rate_limit_per_minute)
        
        if tokens_to_add > 0:
            bucket['tokens'] = min(self.rate_limit_per_minute, bucket['tokens'] + tokens_to_add)
            bucket['last_refill'] = now
        
        # Check if we have tokens available
        if bucket['tokens'] > 0:
            bucket['tokens'] -= 1
            return True
        
        return False

    def _validate_mac_address(self, mac: str) -> bool:
        """Validate MAC address format"""
        mac_pattern = r'^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$'
        return bool(re.match(mac_pattern, mac))

    def _validate_time_format(self, time_str: str) -> bool:
        """Validate HH:MM 24-hour format"""
        time_pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
        return bool(re.match(time_pattern, time_str))

    def get_tools(self) -> List[Dict]:
        """Return tool definitions for Ollama function calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "toggle_parental_controls",
                    "description": "Enable or disable network-level parental controls via OPNsense firewall. This blocks/unblocks all managed devices.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "active": {
                                "type": "boolean", 
                                "description": "True to enable blocking (devices cannot access internet), false to disable blocking (devices can access internet)"
                            },
                            "reason": {
                                "type": "string", 
                                "description": "Optional reason for the toggle action"
                            }
                        },
                        "required": ["active"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_system_status",
                    "description": "Get current parental controls status, device counts, and platform connectivity.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_devices",
                    "description": "Get list of all devices that can be managed by parental controls.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_device",
                    "description": "Add a new device to parental controls management. Device will be automatically synced to OPNsense.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Human-readable name for the device (e.g., 'Johnny iPhone', 'Sarah Laptop')"
                            },
                            "mac": {
                                "type": "string",
                                "description": "MAC address in format AA:BB:CC:DD:EE:FF",
                                "pattern": "^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$"
                            }
                        },
                        "required": ["name", "mac"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_device",
                    "description": "Update an existing device's properties. Only provided fields will be updated.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "integer",
                                "description": "ID of the device to update"
                            },
                            "name": {
                                "type": "string",
                                "description": "New name for the device"
                            },
                            "mac": {
                                "type": "string",
                                "description": "New MAC address",
                                "pattern": "^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$"
                            },
                            "enabled": {
                                "type": "boolean",
                                "description": "Whether device should be subject to parental controls"
                            }
                        },
                        "required": ["device_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_device",
                    "description": "Remove a device from parental controls management.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "device_id": {
                                "type": "integer",
                                "description": "ID of the device to delete"
                            }
                        },
                        "required": ["device_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "sync_devices",
                    "description": "Synchronize device list with OPNsense firewall to ensure rules are up to date.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "nintendo_toggle_controls",
                    "description": "Enable or disable Nintendo Switch parental controls.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "active": {
                                "type": "boolean",
                                "description": "True to enable Nintendo restrictions, false to disable"
                            }
                        },
                        "required": ["active"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "nintendo_set_playtime",
                    "description": "Set daily playtime limit for Nintendo Switch.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "minutes": {
                                "type": "integer",
                                "description": "Daily playtime limit in minutes",
                                "minimum": 0,
                                "maximum": 1440
                            }
                        },
                        "required": ["minutes"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "nintendo_set_bedtime",
                    "description": "Set bedtime restrictions for Nintendo Switch.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_time": {
                                "type": "string",
                                "description": "Bedtime start in HH:MM format (24-hour)",
                                "pattern": "^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
                            },
                            "end_time": {
                                "type": "string",
                                "description": "Bedtime end in HH:MM format (24-hour)",
                                "pattern": "^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
                            }
                        },
                        "required": ["start_time", "end_time"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_nintendo_status",
                    "description": "Get current Nintendo Switch parental controls status.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_nintendo_usage",
                    "description": "Get Nintendo Switch usage statistics and data.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        ]

    def execute_tool(self, tool_name: str, args: Dict) -> Dict:
        """Execute a tool and return results"""
        try:
            self.logger.info(f"Executing tool: {tool_name} with args: {json.dumps(args, default=str)}")
            
            if tool_name == "toggle_parental_controls":
                # Update MAC alias first, then toggle
                alias_success = self.opnsense_manager.create_or_update_mac_alias()
                if not alias_success:
                    return {
                        "success": False,
                        "error": "Failed to update MAC address alias in OPNsense",
                        "timestamp": datetime.now().isoformat()
                    }
                
                active = bool(args.get('active', False))
                reason = args.get('reason', 'AI Assistant toggle')
                
                success = self.opnsense_manager.toggle_parental_controls(active)
                
                if success:
                    status = self.opnsense_manager.get_parental_control_status()
                    return {
                        "success": True,
                        "controls_active": active,
                        "message": f"Parental controls {'activated' if active else 'deactivated'} successfully",
                        "reason": reason,
                        "opnsense_status": status,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to toggle firewall rule in OPNsense",
                        "timestamp": datetime.now().isoformat()
                    }
            
            elif tool_name == "get_system_status":
                # Reuse existing status logic from the Flask app
                opnsense_status = self.opnsense_manager.get_parental_control_status()
                enabled_devices = self.mac_manager.get_enabled_devices()
                all_devices = self.mac_manager.get_all_devices()
                
                return {
                    "success": True,
                    "data": {
                        "controls_active": opnsense_status.get('controls_active', False),
                        "system_status": 'ready' if not opnsense_status.get('error') else 'error',
                        "devices": {
                            "total": len(all_devices),
                            "enabled": len(enabled_devices),
                            "disabled": len(all_devices) - len(enabled_devices)
                        },
                        "platforms": {
                            "opnsense": 'connected' if opnsense_status.get('alias_exists') else 'error',
                            "nintendo": 'available',
                            "google": 'planned',
                            "microsoft": 'planned'
                        },
                        "opnsense": opnsense_status
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            elif tool_name == "get_devices":
                devices = self.mac_manager.get_all_devices()
                return {
                    "success": True,
                    "data": {
                        "devices": devices,
                        "count": len(devices)
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            elif tool_name == "add_device":
                name = args.get('name', '').strip()
                mac = args.get('mac', '').strip()
                
                if not name or not mac:
                    return {
                        "success": False,
                        "error": "Both name and MAC address are required",
                        "timestamp": datetime.now().isoformat()
                    }
                
                if not self._validate_mac_address(mac):
                    return {
                        "success": False,
                        "error": f"Invalid MAC address format: {mac}. Expected format: AA:BB:CC:DD:EE:FF",
                        "timestamp": datetime.now().isoformat()
                    }
                
                device = self.mac_manager.add_device(name, mac)
                
                # Auto-sync with OPNsense
                sync_success = self.opnsense_manager.create_or_update_mac_alias()
                
                return {
                    "success": True,
                    "data": {
                        "device": device,
                        "synced_to_opnsense": sync_success
                    },
                    "message": f"Device '{name}' added successfully" + 
                              (" and synced to OPNsense" if sync_success else " but sync to OPNsense failed"),
                    "timestamp": datetime.now().isoformat()
                }
            
            elif tool_name == "update_device":
                device_id = args.get('device_id')
                name = args.get('name')
                mac = args.get('mac')
                enabled = args.get('enabled')
                
                if device_id is None:
                    return {
                        "success": False,
                        "error": "Device ID is required",
                        "timestamp": datetime.now().isoformat()
                    }
                
                if mac and not self._validate_mac_address(mac):
                    return {
                        "success": False,
                        "error": f"Invalid MAC address format: {mac}. Expected format: AA:BB:CC:DD:EE:FF",
                        "timestamp": datetime.now().isoformat()
                    }
                
                device = self.mac_manager.update_device(device_id, name=name, mac=mac, enabled=enabled)
                
                # Auto-sync with OPNsense
                sync_success = self.opnsense_manager.create_or_update_mac_alias()
                
                return {
                    "success": True,
                    "data": {
                        "device": device,
                        "synced_to_opnsense": sync_success
                    },
                    "message": f"Device updated successfully" + 
                              (" and synced to OPNsense" if sync_success else " but sync to OPNsense failed"),
                    "timestamp": datetime.now().isoformat()
                }
            
            elif tool_name == "delete_device":
                device_id = args.get('device_id')
                
                if device_id is None:
                    return {
                        "success": False,
                        "error": "Device ID is required",
                        "timestamp": datetime.now().isoformat()
                    }
                
                success = self.mac_manager.delete_device(device_id)
                
                if success:
                    # Auto-sync with OPNsense
                    sync_success = self.opnsense_manager.create_or_update_mac_alias()
                    
                    return {
                        "success": True,
                        "data": {
                            "synced_to_opnsense": sync_success
                        },
                        "message": f"Device deleted successfully" + 
                                  (" and synced to OPNsense" if sync_success else " but sync to OPNsense failed"),
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to delete device with ID {device_id}",
                        "timestamp": datetime.now().isoformat()
                    }
            
            elif tool_name == "sync_devices":
                success = self.opnsense_manager.create_or_update_mac_alias()
                enabled_devices = self.mac_manager.get_enabled_devices()
                
                return {
                    "success": success,
                    "data": {
                        "device_count": len(enabled_devices)
                    },
                    "message": f"Device list {'synced' if success else 'failed to sync'} with OPNsense ({len(enabled_devices)} devices)",
                    "timestamp": datetime.now().isoformat()
                }
            
            elif tool_name == "nintendo_toggle_controls":
                active = bool(args.get('active', False))
                
                if active:
                    success = self.nintendo_manager.enable_parental_controls()
                else:
                    success = self.nintendo_manager.disable_parental_controls()
                
                return {
                    "success": success,
                    "data": {
                        "nintendo_controls_active": active if success else not active
                    },
                    "message": f"Nintendo Switch controls {'enabled' if active else 'disabled'}" + 
                              (" successfully" if success else " - operation failed"),
                    "timestamp": datetime.now().isoformat()
                }
            
            elif tool_name == "nintendo_set_playtime":
                minutes = args.get('minutes', 120)
                
                if not isinstance(minutes, int) or minutes < 0 or minutes > 1440:
                    return {
                        "success": False,
                        "error": "Playtime must be between 0 and 1440 minutes (24 hours)",
                        "timestamp": datetime.now().isoformat()
                    }
                
                success = self.nintendo_manager.set_play_time_limit(minutes)
                
                return {
                    "success": success,
                    "data": {
                        "playtime_limit_minutes": minutes if success else None
                    },
                    "message": f"Nintendo playtime limit {'set to' if success else 'failed to set to'} {minutes} minutes/day",
                    "timestamp": datetime.now().isoformat()
                }
            
            elif tool_name == "nintendo_set_bedtime":
                start_time = args.get('start_time', '21:00')
                end_time = args.get('end_time', '07:00')
                
                if not self._validate_time_format(start_time):
                    return {
                        "success": False,
                        "error": f"Invalid start time format: {start_time}. Use HH:MM (24-hour)",
                        "timestamp": datetime.now().isoformat()
                    }
                
                if not self._validate_time_format(end_time):
                    return {
                        "success": False,
                        "error": f"Invalid end time format: {end_time}. Use HH:MM (24-hour)",
                        "timestamp": datetime.now().isoformat()
                    }
                
                success = self.nintendo_manager.set_bedtime_mode(start_time, end_time)
                
                return {
                    "success": success,
                    "data": {
                        "bedtime_start": start_time if success else None,
                        "bedtime_end": end_time if success else None
                    },
                    "message": f"Nintendo bedtime {'set' if success else 'failed to set'}: {start_time} - {end_time}",
                    "timestamp": datetime.now().isoformat()
                }
            
            elif tool_name == "get_nintendo_status":
                status = self.nintendo_manager.get_parental_control_status()
                return {
                    "success": True,
                    "data": {
                        "nintendo_status": status
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            elif tool_name == "get_nintendo_usage":
                stats = self.nintendo_manager.get_usage_stats()
                return {
                    "success": True,
                    "data": {
                        "usage_stats": stats
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}",
                    "timestamp": datetime.now().isoformat()
                }
                
        except ValueError as e:
            return {
                "success": False,
                "error": f"Validation error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Tool execution error for {tool_name}: {e}")
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def chat(self, session_id: str, user_message: str) -> Dict:
        """Handle a chat interaction with tool calling"""
        start_time = time.time()
        tools_invoked = []
        tool_results = []
        error = None
        
        try:
            # Rate limiting check
            if not self._check_rate_limit(session_id):
                return {
                    "success": False,
                    "error": "Rate limit exceeded. Please wait before sending another message.",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Initialize or get session
            if session_id not in self.sessions:
                self.sessions[session_id] = {
                    "messages": [{"role": "system", "content": self.system_prompt}],
                    "created_at": datetime.now().isoformat()
                }
            
            session = self.sessions[session_id]
            
            # Add user message to conversation
            session["messages"].append({"role": "user", "content": user_message})
            
            # Call Ollama with tools
            ollama_payload = {
                "model": self.ollama_model,
                "messages": session["messages"],
                "tools": self.get_tools(),
                "stream": False
            }
            
            response = requests.post(
                f"{self.ollama_host}/api/chat",
                json=ollama_payload,
                timeout=30
            )
            
            if not response.ok:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            ollama_response = response.json()
            assistant_message = ollama_response.get("message", {})
            
            # Check if there are tool calls
            tool_calls = assistant_message.get("tool_calls", [])
            
            if tool_calls:
                # Execute tools and collect results
                for tool_call in tool_calls:
                    function_data = tool_call.get("function", {})
                    tool_name = function_data.get("name")
                    tool_args = function_data.get("arguments", {})
                    
                    tools_invoked.append(tool_name)
                    result = self.execute_tool(tool_name, tool_args)
                    tool_results.append(result)
                    
                    # Add tool result to conversation
                    session["messages"].append({
                        "role": "tool",
                        "content": json.dumps(result)
                    })
                
                # Get final response from Ollama with tool results
                final_payload = {
                    "model": self.ollama_model,
                    "messages": session["messages"],
                    "stream": False
                }
                
                final_response = requests.post(
                    f"{self.ollama_host}/api/chat",
                    json=final_payload,
                    timeout=30
                )
                
                if final_response.ok:
                    final_data = final_response.json()
                    assistant_message = final_data.get("message", assistant_message)
            
            # Add assistant response to conversation
            session["messages"].append(assistant_message)
            
            # Keep conversation history manageable (last 20 messages)
            if len(session["messages"]) > 21:  # system + 20 messages
                # Keep system message and last 19 messages
                session["messages"] = [session["messages"][0]] + session["messages"][-19:]
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            result = {
                "success": True,
                "reply": assistant_message.get("content", "I encountered an issue processing your request."),
                "tool_calls": tools_invoked,
                "tool_results": tool_results,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "response_time_ms": response_time_ms
            }
            
            # Log for audit
            self._log_audit(session_id, user_message, tools_invoked, tool_results, response_time_ms)
            
            return result
            
        except requests.exceptions.RequestException as e:
            error = f"Ollama connection error: {str(e)}"
            self.logger.error(error)
            response_time_ms = int((time.time() - start_time) * 1000)
            self._log_audit(session_id, user_message, tools_invoked, tool_results, response_time_ms, error)
            
            return {
                "success": False,
                "error": error,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            error = f"Chat processing error: {str(e)}"
            self.logger.error(error)
            response_time_ms = int((time.time() - start_time) * 1000)
            self._log_audit(session_id, user_message, tools_invoked, tool_results, response_time_ms, error)
            
            return {
                "success": False,
                "error": error,
                "timestamp": datetime.now().isoformat()
            }


def register_ai_routes(app: Flask, orchestrator: MCPOrchestrator, mode: str = "staging"):
    """Register AI assistant routes in Flask app"""
    
    def require_api_key(f):
        """Decorator to require API key authentication"""
        def decorated_function(*args, **kwargs):
            api_key = request.headers.get('X-Api-Key')
            expected_key = os.environ.get('AI_API_KEY')
            
            if not expected_key:
                return jsonify({
                    "success": False,
                    "error": "AI assistant not properly configured - missing API key"
                }), 503
            
            if not api_key or api_key != expected_key:
                return jsonify({
                    "success": False,
                    "error": "Invalid or missing API key"
                }), 401
            
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    
    # AI Assistant Page HTML Template
    AI_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 AI Assistant - Parental Controls</title>
    <link rel="icon" href="data:image/svg+xml,%3csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22%3e%3ctext y=%22.9em%22 font-size=%2290%22%3e🤖%3c/text%3e%3c/svg%3e">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background: linear-gradient(135deg, #1e3a8a 0%, #312e81 100%);
            color: #ffffff;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        header {
            text-align: center;
            margin-bottom: 20px;
        }
        
        header h1 {
            font-size: 2rem;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .nav-links {
            margin-bottom: 20px;
            text-align: center;
        }
        
        .nav-links a {
            display: inline-block;
            margin: 5px 10px;
            padding: 8px 16px;
            background: rgba(255,255,255,0.2);
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.3s ease;
        }
        
        .nav-links a:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            margin-bottom: 20px;
            min-height: 400px;
            max-height: 600px;
        }
        
        .message {
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
        }
        
        .message.user {
            justify-content: flex-end;
        }
        
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
        }
        
        .message.user .message-content {
            background: rgba(59, 130, 246, 0.8);
            margin-left: auto;
        }
        
        .message.assistant .message-content {
            background: rgba(255,255,255,0.2);
            margin-right: auto;
        }
        
        .message.system .message-content {
            background: rgba(34, 197, 94, 0.8);
            font-style: italic;
            text-align: center;
            margin: 0 auto;
        }
        
        .quick-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 15px;
        }
        
        .quick-action {
            padding: 8px 12px;
            background: rgba(255,255,255,0.2);
            border: none;
            border-radius: 15px;
            color: white;
            cursor: pointer;
            font-size: 0.85rem;
            transition: background 0.3s ease;
        }
        
        .quick-action:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .chat-input {
            display: flex;
            gap: 10px;
        }
        
        .chat-input input {
            flex: 1;
            padding: 12px 16px;
            border: none;
            border-radius: 25px;
            background: rgba(255,255,255,0.2);
            color: white;
            font-size: 1rem;
        }
        
        .chat-input input::placeholder {
            color: rgba(255,255,255,0.7);
        }
        
        .chat-input button {
            padding: 12px 20px;
            border: none;
            border-radius: 25px;
            background: rgba(34, 197, 94, 0.8);
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s ease;
        }
        
        .chat-input button:hover:not(:disabled) {
            background: rgba(34, 197, 94, 1);
        }
        
        .chat-input button:disabled {
            background: rgba(107, 114, 128, 0.5);
            cursor: not-allowed;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .error {
            background: rgba(239, 68, 68, 0.8) !important;
        }
        
        .tool-summary {
            font-size: 0.9rem;
            margin-top: 8px;
            padding: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 AI Assistant for Parental Controls</h1>
            <p>Control your network and devices using natural language</p>
        </header>
        
        <div class="nav-links">
            <a href="/">← Back to Dashboard</a>
            <a href="/api/status">System Status</a>
            <a href="/health">Health Check</a>
        </div>
        
        <div class="chat-container">
            <div class="chat-messages" id="chatMessages">
                <div class="message system">
                    <div class="message-content">
                        <strong>AI Assistant Ready!</strong><br>
                        I can help you manage parental controls. Try asking me to:
                        <ul style="text-align: left; margin: 8px 0;">
                            <li>"Block all devices now"</li>
                            <li>"Add device named Johnny iPhone with MAC AA:BB:CC:DD:EE:FF"</li>
                            <li>"What's the current system status?"</li>
                            <li>"Turn off Nintendo controls"</li>
                            <li>"Set Nintendo bedtime 21:00 to 07:00"</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <div class="quick-actions">
                <button class="quick-action" onclick="sendQuickMessage('What is the current system status?')">📊 System Status</button>
                <button class="quick-action" onclick="sendQuickMessage('Block all devices now')">🚫 Block All</button>
                <button class="quick-action" onclick="sendQuickMessage('Allow internet access')">✅ Allow All</button>
                <button class="quick-action" onclick="sendQuickMessage('Show me all devices')">📱 List Devices</button>
                <button class="quick-action" onclick="sendQuickMessage('Turn off Nintendo now')">🎮 Nintendo Off</button>
            </div>
            
            <div class="chat-input">
                <input type="text" id="messageInput" placeholder="Ask me to control parental settings..." 
                       onkeypress="if(event.key==='Enter')sendMessage()">
                <button id="sendButton" onclick="sendMessage()">Send</button>
            </div>
        </div>
    </div>

    <script>
        // Configuration
        const API_BASE = '{{ api_base }}';
        const API_KEY = '{{ api_key }}';
        let sessionId = localStorage.getItem('ai_session_id') || generateSessionId();
        
        function generateSessionId() {
            const id = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('ai_session_id', id);
            return id;
        }
        
        function addMessage(content, type = 'user', toolSummary = null) {
            const messagesContainer = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            
            let messageContent = `<div class="message-content">${content}</div>`;
            
            if (toolSummary) {
                messageContent += `<div class="tool-summary"><strong>Actions taken:</strong> ${toolSummary}</div>`;
            }
            
            messageDiv.innerHTML = messageContent;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function formatToolSummary(toolCalls, toolResults) {
            if (!toolCalls || toolCalls.length === 0) return null;
            
            return toolCalls.map((tool, index) => {
                const result = toolResults[index];
                const status = result?.success ? '✅' : '❌';
                return `${status} ${tool}`;
            }).join(', ');
        }
        
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const sendButton = document.getElementById('sendButton');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message
            addMessage(message, 'user');
            
            // Clear input and disable button
            input.value = '';
            sendButton.disabled = true;
            sendButton.innerHTML = '<div class="loading"></div>';
            
            try {
                const response = await fetch(`${API_BASE}/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Api-Key': API_KEY
                    },
                    body: JSON.stringify({
                        session_id: sessionId,
                        message: message
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    const toolSummary = formatToolSummary(data.tool_calls, data.tool_results);
                    addMessage(data.reply, 'assistant', toolSummary);
                } else {
                    addMessage(`Error: ${data.error}`, 'assistant error');
                }
                
            } catch (error) {
                addMessage(`Connection error: ${error.message}`, 'assistant error');
            } finally {
                sendButton.disabled = false;
                sendButton.innerHTML = 'Send';
                input.focus();
            }
        }
        
        function sendQuickMessage(message) {
            document.getElementById('messageInput').value = message;
            sendMessage();
        }
        
        // Initialize
        document.getElementById('messageInput').focus();
        
        // Load initial system status
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const status = data.controlsActive ? '🔴 ACTIVE (devices blocked)' : '🟢 INACTIVE (devices allowed)';
                    addMessage(`System Status: ${status} | Devices: ${data.devices?.total || 0} total, ${data.devices?.enabled || 0} managed`, 'system');
                }
            })
            .catch(() => {
                addMessage('Welcome! I\\'m ready to help manage your parental controls.', 'system');
            });
    </script>
</body>
</html>"""
    
    # Staging routes
    @app.route('/ai-staging')
    def ai_page_staging():
        """Serve AI assistant page for staging"""
        api_key = os.environ.get('AI_API_KEY', 'demo-key-staging')
        return render_template_string(AI_PAGE_TEMPLATE, 
                                    api_base='/api/ai-staging', 
                                    api_key=api_key)
    
    @app.route('/api/ai-staging/chat', methods=['POST'])
    @require_api_key
    def ai_chat_staging():
        """AI chat endpoint for staging"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "success": False,
                    "error": "No data provided"
                }), 400
            
            session_id = data.get('session_id')
            message = data.get('message')
            
            if not session_id or not message:
                return jsonify({
                    "success": False,
                    "error": "session_id and message are required"
                }), 400
            
            result = orchestrator.chat(session_id, message)
            return jsonify(result)
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Chat processing failed: {str(e)}"
            }), 500
    
    # Production routes (only if mode is prod)
    if mode == "prod":
        @app.route('/ai')
        def ai_page_prod():
            """Serve AI assistant page for production"""
            api_key = "use-server-cookie"  # Don't embed real key in production
            return render_template_string(AI_PAGE_TEMPLATE, 
                                        api_base='/api/ai', 
                                        api_key=api_key)
        
        @app.route('/api/ai/chat', methods=['POST'])
        @require_api_key
        def ai_chat_prod():
            """AI chat endpoint for production"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        "success": False,
                        "error": "No data provided"
                    }), 400
                
                session_id = data.get('session_id')
                message = data.get('message')
                
                if not session_id or not message:
                    return jsonify({
                        "success": False,
                        "error": "session_id and message are required"
                    }), 400
                
                result = orchestrator.chat(session_id, message)
                return jsonify(result)
                
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": f"Chat processing failed: {str(e)}"
                }), 500
