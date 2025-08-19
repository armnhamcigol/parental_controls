#!/bin/bash

# 🎮 Enhanced Nintendo Switch Dashboard - Quick Deployment Script
# This script will update your Raspberry Pi with the enhanced dashboard

set -e

# Configuration - Update these values
PI_IP="${1:-192.168.1.100}"  # First argument or default IP
PI_USER="${2:-pi}"           # Second argument or default user
PI_PATH="/home/pi/parental-controls"

echo "🎮 Enhanced Nintendo Switch Dashboard Deployment"
echo "=================================================="
echo "Target: $PI_USER@$PI_IP"
echo "Path: $PI_PATH"
echo ""

# Check if we can reach the Pi
echo "🔍 Checking Pi connectivity..."
if ! ping -c 1 -W 3 "$PI_IP" > /dev/null 2>&1; then
    echo "❌ Cannot reach Pi at $PI_IP"
    echo "Please check:"
    echo "  - Pi IP address is correct"
    echo "  - Pi is powered on and connected"
    echo "  - Network connectivity"
    exit 1
fi
echo "✅ Pi is reachable"

# Test SSH connectivity
echo "🔐 Testing SSH connection..."
if ! ssh -o BatchMode=yes -o ConnectTimeout=5 "$PI_USER@$PI_IP" echo "SSH OK" > /dev/null 2>&1; then
    echo "❌ Cannot SSH to Pi"
    echo "Please ensure:"
    echo "  - SSH is enabled on Pi"
    echo "  - SSH keys are set up or you can provide password"
    echo "  - User '$PI_USER' exists on Pi"
    exit 1
fi
echo "✅ SSH connection works"

# Create backup directory on Pi
echo "📦 Creating backup on Pi..."
ssh "$PI_USER@$PI_IP" "
    cd $PI_PATH/src/web 2>/dev/null || { echo 'Web directory not found'; exit 1; }
    backup_dir=\"backup_\$(date +%Y%m%d_%H%M%S)\"
    mkdir -p \"\$backup_dir\"
    cp -r index.html app.js style.css \"\$backup_dir/\" 2>/dev/null || true
    echo \"📦 Backup created: \$backup_dir\"
"

# Deploy updated files
echo "📤 Deploying enhanced dashboard files..."

echo "  📄 Deploying index.html..."
scp "src/web/index.html" "$PI_USER@$PI_IP:$PI_PATH/src/web/index.html"

echo "  📄 Deploying app.js..."
scp "src/web/app.js" "$PI_USER@$PI_IP:$PI_PATH/src/web/app.js"

echo "  📄 Deploying style.css..."
scp "src/web/style.css" "$PI_USER@$PI_IP:$PI_PATH/src/web/style.css"

echo "✅ Files deployed successfully"

# Optional: Deploy enhanced backend if it exists
if [ -f "pi_backend_nintendo.py" ]; then
    echo "📤 Deploying enhanced backend..."
    scp "pi_backend_nintendo.py" "$PI_USER@$PI_IP:$PI_PATH/backend/"
    echo "✅ Backend deployed"
fi

# Optional: Deploy enhanced discovery module if it exists
if [ -f "enhanced_nintendo_discovery.py" ]; then
    echo "📤 Deploying enhanced discovery module..."
    scp "enhanced_nintendo_discovery.py" "$PI_USER@$PI_IP:$PI_PATH/"
    echo "✅ Enhanced discovery deployed"
fi

# Restart services
echo "🔄 Restarting services on Pi..."
ssh "$PI_USER@$PI_IP" "
    echo '🔄 Attempting to restart parental controls service...'
    
    # Try systemd first
    if sudo systemctl restart parental-controls 2>/dev/null; then
        echo '✅ Systemd service restarted'
    # Try Docker Compose if systemd fails
    elif cd $PI_PATH && docker-compose restart 2>/dev/null; then
        echo '✅ Docker services restarted'
    # Try killing and restarting Python process
    elif pkill -f 'python.*backend' && sleep 2; then
        echo '⚠️  Python process killed, may need manual restart'
    else
        echo '⚠️  Could not restart services automatically'
        echo '    Please restart manually:'
        echo '    sudo systemctl restart parental-controls'
        echo '    OR: cd $PI_PATH && docker-compose restart'
    fi
"

# Verify deployment
echo "🔍 Verifying deployment..."
sleep 5

# Check health endpoint
if curl -s "http://$PI_IP:3001/health" | grep -q "healthy"; then
    echo "✅ Backend health check passed"
else
    echo "⚠️  Backend health check failed - service may still be starting"
fi

# Check if Nintendo endpoint responds
if curl -s "http://$PI_IP:3001/api/nintendo/devices" | grep -q "success\|error"; then
    echo "✅ Nintendo API endpoint responding"
else
    echo "⚠️  Nintendo API not yet responding - may need authentication"
fi

echo ""
echo "🎉 Deployment Complete!"
echo "=================================================="
echo "Dashboard URL: http://$PI_IP:3001"
echo "Health Check: http://$PI_IP:3001/health"
echo "Nintendo API: http://$PI_IP:3001/api/nintendo/devices"
echo ""
echo "📋 Next Steps:"
echo "1. Open the dashboard in your browser"
echo "2. Verify Nintendo Switch devices appear"
echo "3. Test individual device controls"
echo "4. Check real-time updates are working"
echo ""
echo "🛠️  If issues occur:"
echo "   - Check Pi logs: ssh $PI_USER@$PI_IP 'journalctl -u parental-controls -f'"
echo "   - Verify Nintendo authentication"
echo "   - Ensure Pi can reach Nintendo Switch devices"
echo ""
echo "✨ Enhanced Nintendo Switch parental controls are now live!"
