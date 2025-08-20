#!/usr/bin/env python3
"""
AI Parental Controls - Raspberry Pi Deployment Script
Creates a deployment package for the Raspberry Pi
"""

import os
import shutil
import zipfile
from pathlib import Path

def create_deployment_package():
    """Create a complete deployment package for Raspberry Pi"""
    
    # Create deployment directory
    deploy_dir = Path("pi_deployment")
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    deploy_dir.mkdir()
    
    print("🚀 Creating Raspberry Pi Deployment Package")
    print("=" * 50)
    
    # Core backend files
    backend_files = [
        "backend/real_backend.py",
        "backend/mcp_server.py", 
        "backend/opnsense_integration.py",
        "backend/mac_manager.py",
        "backend/mac_api.py",
        "backend/nintendo_integration.py"
    ]
    
    # Create backend directory
    (deploy_dir / "backend").mkdir()
    
    for file in backend_files:
        if Path(file).exists():
            shutil.copy2(file, deploy_dir / file)
            print(f"✅ Copied: {file}")
        else:
            print(f"⚠️ Missing: {file}")
    
    # Frontend files
    frontend_files = [
        "enhanced_dashboard.html",
    ]
    
    for file in frontend_files:
        if Path(file).exists():
            shutil.copy2(file, deploy_dir / file)
            print(f"✅ Copied: {file}")
    
    # Configuration and run files
    config_files = [
        "run_server.py",
        "quick_test.py",
        "test_commands.txt"
    ]
    
    for file in config_files:
        if Path(file).exists():
            shutil.copy2(file, deploy_dir / file)
            print(f"✅ Copied: {file}")
    
    # Create Pi-specific requirements.txt
    requirements = """flask==3.0.0
requests==2.31.0
paramiko==3.4.0
cryptography==41.0.8
python-dateutil==2.8.2
"""
    
    with open(deploy_dir / "requirements.txt", "w", encoding='utf-8') as f:
        f.write(requirements)
    print("✅ Created: requirements.txt")
    
    # Create Pi-specific run script
    pi_run_script = """#!/usr/bin/env python3
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
"""
    
    with open(deploy_dir / "run_pi_server.py", "w", encoding='utf-8') as f:
        f.write(pi_run_script)
    print("✅ Created: run_pi_server.py")
    
    # Create setup script for Pi
    setup_script = """#!/bin/bash
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
"""
    
    with open(deploy_dir / "setup_pi.sh", "w", encoding='utf-8') as f:
        f.write(setup_script)
    os.chmod(deploy_dir / "setup_pi.sh", 0o755)
    print("✅ Created: setup_pi.sh")
    
    # Create README for Pi deployment
    readme = """# AI Parental Controls - Raspberry Pi Deployment

## Quick Setup

1. Copy this entire folder to your Raspberry Pi:
   ```bash
   scp -r pi_deployment/ pi@192.168.123.240:/home/pi/ai_parental_controls/
   ```

2. SSH to your Pi and run setup:
   ```bash
   ssh pi@192.168.123.240
   cd ai_parental_controls
   chmod +x setup_pi.sh
   ./setup_pi.sh
   ```

3. Start the server:
   ```bash
   python3 run_pi_server.py
   ```

4. Access from any device on your network:
   ```
   http://192.168.123.240:5000/ai-staging
   ```

## Manual Setup (if SSH doesn't work)

1. Copy the files to a USB drive
2. Insert into Pi and copy to `/home/pi/ai_parental_controls/`
3. Install dependencies: `pip3 install -r requirements.txt`
4. Run: `python3 run_pi_server.py`

## Configuration

- **API Key**: `test-api-key-staging-12345`
- **Ollama Host**: Uses local Pi Ollama instance at port 8034
- **Server Port**: 5000 (accessible from network)

## Testing

Run the test script:
```bash
python3 quick_test.py
```

Or use the web interface at:
```
http://192.168.123.240:5000/ai-staging
```

## Troubleshooting

1. **Can't access from other devices**: Check Pi firewall
2. **AI not responding**: Verify Ollama is running on port 8034
3. **Permission issues**: Make sure scripts are executable

## Files Included

- `backend/` - All Python backend modules
- `run_pi_server.py` - Pi-optimized server runner
- `setup_pi.sh` - Automated setup script
- `requirements.txt` - Python dependencies
- `quick_test.py` - Test script
- `enhanced_dashboard.html` - Web dashboard
"""
    
    with open(deploy_dir / "README_PI.md", "w", encoding='utf-8') as f:
        f.write(readme)
    print("✅ Created: README_PI.md")
    
    # Create a ZIP archive for easy transfer
    with zipfile.ZipFile("ai_parental_controls_pi.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(deploy_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = str(file_path.relative_to(deploy_dir))
                zipf.write(file_path, arcname)
    
    print(f"✅ Created: ai_parental_controls_pi.zip")
    
    print("\n" + "=" * 50)
    print("🎯 DEPLOYMENT PACKAGE READY!")
    print("=" * 50)
    print("📁 Deployment folder: pi_deployment/")
    print("📦 ZIP package: ai_parental_controls_pi.zip")
    print("\n🚀 Next steps:")
    print("1. Transfer the ZIP to your Pi (USB, SCP, or web download)")
    print("2. Extract and run setup_pi.sh") 
    print("3. Start with: python3 run_pi_server.py")
    print("4. Access at: http://192.168.123.240:5000/ai-staging")
    
    return True

if __name__ == "__main__":
    create_deployment_package()
