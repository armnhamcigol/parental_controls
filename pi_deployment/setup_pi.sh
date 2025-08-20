#!/bin/bash
# AI Parental Controls - Pi Setup Script

echo "🚀 Setting up AI Parental Controls on Raspberry Pi"
echo "=" * 50

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
echo "🐍 Installing Python packages..."
pip3 install -r requirements.txt

# Create logs directory
mkdir -p logs

# Make scripts executable
chmod +x run_pi_server.py

echo "✅ Setup complete!"
echo ""
echo "To start the server, run:"
echo "  python3 run_pi_server.py"
echo ""
echo "Then access from any device on your network:"
echo "  http://192.168.123.240:5000/ai-staging"
