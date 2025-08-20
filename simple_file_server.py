#!/usr/bin/env python3
"""
Simple HTTP File Server for Pi Deployment
Serves the deployment ZIP file so Pi can download it directly
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

def start_file_server():
    """Start a simple HTTP server to serve the deployment files"""
    
    port = 8080
    
    # Change to the current directory to serve files
    os.chdir(Path(__file__).parent)
    
    # Create a simple HTTP server
    handler = http.server.SimpleHTTPRequestHandler
    
    print("🌐 Starting File Server for Pi Deployment")
    print("=" * 50)
    print(f"📂 Serving files from: {os.getcwd()}")
    print(f"🌍 Server URL: http://192.168.123.XXX:{port}")
    print("📦 Deployment file: ai_parental_controls_pi.zip")
    print("=" * 50)
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"✅ Server started on port {port}")
            print("\n📋 To download on your Pi, run:")
            print(f"   wget http://[YOUR_WINDOWS_IP]:{port}/ai_parental_controls_pi.zip")
            print("\n⚡ Or browse to:")
            print(f"   http://[YOUR_WINDOWS_IP]:{port}")
            print("\n🛑 Press Ctrl+C to stop the server")
            print("=" * 50)
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use. Try a different port.")
        else:
            print(f"❌ Server error: {e}")

if __name__ == "__main__":
    # Check if deployment ZIP exists
    zip_file = Path("ai_parental_controls_pi.zip")
    if not zip_file.exists():
        print("❌ Deployment ZIP not found. Run deploy_to_pi.py first!")
        exit(1)
    
    start_file_server()
