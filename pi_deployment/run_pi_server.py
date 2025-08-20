#!/usr/bin/env python3
'''
AI Parental Controls - Raspberry Pi Runner
'''

import os
import sys
from pathlib import Path

# Set up environment for Pi
os.environ.update({
    'AI_MCP_MODE': 'staging',
    'AI_API_KEY': 'test-api-key-staging-12345',
    'OLLAMA_HOST': 'http://192.168.123.240:8034',  # Local Ollama on Pi
    'OLLAMA_MODEL': 'qwen2.5:7b-instruct-q8_0',
})

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

# Import and run
from backend.real_backend import app

if __name__ == '__main__':
    print("🤖 Starting AI-Enabled Parental Controls on Raspberry Pi")
    print("=" * 60)
    print("🌐 Server will be available at: http://192.168.123.240:5000")
    print("🤖 AI Assistant at: http://192.168.123.240:5000/ai-staging")
    print(f"🔑 API Key: {os.environ['AI_API_KEY']}")
    print("=" * 60)
    
    # Run on all interfaces so it's accessible from other machines
    app.run(host='0.0.0.0', port=5000, debug=False)
