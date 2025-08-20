#!/usr/bin/env python3
"""
Simple Runner for AI Parental Controls Server
"""

import os
import sys
from pathlib import Path

# Set up environment
os.environ.update({
    'AI_MCP_MODE': 'staging',
    'AI_API_KEY': 'test-api-key-staging-12345',
    'OLLAMA_HOST': 'http://192.168.123.240:8034',
    'OLLAMA_MODEL': 'qwen2.5:7b-instruct-q8_0',
})

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

# Import and run
from backend.real_backend import app

if __name__ == '__main__':
    print("🤖 Starting AI-Enabled Parental Controls")
    print("=" * 50)
    print("🌐 Server will be available at: http://127.0.0.1:5000")
    print("🤖 AI Assistant at: http://127.0.0.1:5000/ai-staging")
    print(f"🔑 API Key: {os.environ['AI_API_KEY']}")
    print("=" * 50)
    
    app.run(host='127.0.0.1', port=5000, debug=False)
