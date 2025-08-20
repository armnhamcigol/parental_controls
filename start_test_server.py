#!/usr/bin/env python3
"""
Start Test Server for AI-Enabled Parental Controls
Sets up environment and runs the Flask backend with proper configuration
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def check_port_available(port):
    """Check if a port is available"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result != 0
    except:
        return False

def check_ollama_connection():
    """Check if Ollama is accessible"""
    try:
        response = requests.get("http://192.168.123.240:8034/api/tags", timeout=5)
        if response.ok:
            models = response.json().get('models', [])
            qwen_available = any(model['name'] == 'qwen2.5:7b-instruct-q8_0' for model in models)
            return True, qwen_available, models
        return False, False, []
    except Exception as e:
        return False, False, str(e)

def setup_environment():
    """Set up environment variables"""
    env_vars = {
        'AI_MCP_MODE': 'staging',
        'AI_API_KEY': 'test-api-key-staging-12345',
        'OLLAMA_HOST': 'http://192.168.123.240:8034',
        'OLLAMA_MODEL': 'qwen2.5:7b-instruct-q8_0',
        'FLASK_PORT': '5000',
        'FLASK_HOST': '127.0.0.1'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"✅ Set {key}={value}")
    
    return env_vars

def start_server():
    """Start the Flask server"""
    print("\n🚀 Starting AI-Enabled Parental Controls Server...")
    print("=" * 60)
    
    # Check port availability
    port = int(os.environ.get('FLASK_PORT', 5000))
    if not check_port_available(port):
        print(f"❌ Port {port} is already in use!")
        print("Please stop the existing service or choose a different port.")
        return False
    
    # Check Ollama connection
    print("\n🔍 Checking Ollama Connection...")
    ollama_ok, qwen_available, models = check_ollama_connection()
    
    if not ollama_ok:
        print("❌ Cannot connect to Ollama at http://192.168.123.240:8034")
        print("Please ensure Ollama is running and accessible.")
        return False
    
    print("✅ Ollama connection successful")
    
    if qwen_available:
        print("✅ Qwen 2.5 7B model is available")
    else:
        print("⚠️  Qwen 2.5 7B model not found. Available models:")
        for model in models:
            print(f"   - {model.get('name', 'Unknown')}")
        print("\nWARNING: AI features may not work optimally")
    
    # Create logs directory
    logs_dir = Path(__file__).parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Start the Flask server
    backend_path = Path(__file__).parent / 'backend' / 'real_backend.py'
    
    print(f"\n🌐 Starting server on http://{os.environ['FLASK_HOST']}:{port}")
    print("📍 Available endpoints:")
    print(f"   • Main Dashboard: http://127.0.0.1:{port}/")
    print(f"   • AI Assistant (Staging): http://127.0.0.1:{port}/ai-staging")
    print(f"   • System Status: http://127.0.0.1:{port}/api/status")
    print(f"   • Health Check: http://127.0.0.1:{port}/health")
    
    print("\n🤖 AI Commands you can test:")
    print("   • 'What is the current system status?'")
    print("   • 'Show me all devices'")
    print("   • 'Block all devices now'")
    print("   • 'Allow internet access'")
    print("   • 'Add device named Test iPhone with MAC AA:BB:CC:DD:EE:FF'")
    
    print(f"\n🔑 API Key for testing: {os.environ['AI_API_KEY']}")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Import and run the Flask app directly
        sys.path.insert(0, str(Path(__file__).parent / 'backend'))
        
        # Set up environment for Flask
        os.environ['FLASK_RUN_HOST'] = os.environ['FLASK_HOST']
        os.environ['FLASK_RUN_PORT'] = str(port)
        os.environ['FLASK_DEBUG'] = '1'
        
        # Import the Flask app
        from backend.real_backend import app
        
        print("\n✅ Flask app imported successfully")
        
        # Run the app
        app.run(
            host=os.environ['FLASK_HOST'],
            port=port,
            debug=False,  # Disable debug to avoid double-restart
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down server...")
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
        print("✅ Server stopped")
        return True
    
    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        return False

if __name__ == "__main__":
    print("🤖 AI-Enabled Parental Controls Test Server")
    print("=" * 50)
    
    # Setup environment
    env_vars = setup_environment()
    
    # Start server
    success = start_server()
    
    if not success:
        print("\n💡 Troubleshooting Tips:")
        print("1. Ensure Ollama is running: docker ps | grep ollama")
        print("2. Check Ollama models: curl http://192.168.123.240:8034/api/tags")
        print("3. Install Qwen model: ollama pull qwen2.5:7b-instruct-q8_0")
        print("4. Check firewall settings for port access")
        sys.exit(1)
