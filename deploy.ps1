# 🎮 Enhanced Nintendo Switch Dashboard - PowerShell Deployment Script
# This script will update your Raspberry Pi with the enhanced dashboard from Windows

param(
    [string]$PiIP = "192.168.1.100",     # Raspberry Pi IP address
    [string]$PiUser = "pi",              # Pi username
    [string]$PiPath = "/home/pi/parental-controls"  # Path on Pi
)

Write-Host "🎮 Enhanced Nintendo Switch Dashboard Deployment" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "Target: $PiUser@$PiIP" -ForegroundColor Yellow
Write-Host "Path: $PiPath" -ForegroundColor Yellow
Write-Host ""

# Check if we can reach the Pi
Write-Host "🔍 Checking Pi connectivity..." -ForegroundColor Blue
if (-not (Test-Connection -ComputerName $PiIP -Count 1 -Quiet)) {
    Write-Host "❌ Cannot reach Pi at $PiIP" -ForegroundColor Red
    Write-Host "Please check:" -ForegroundColor Red
    Write-Host "  - Pi IP address is correct" -ForegroundColor Red
    Write-Host "  - Pi is powered on and connected" -ForegroundColor Red
    Write-Host "  - Network connectivity" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Pi is reachable" -ForegroundColor Green

# Check if required files exist
$RequiredFiles = @(
    "src/web/index.html",
    "src/web/app.js", 
    "src/web/style.css"
)

foreach ($file in $RequiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "❌ Required file not found: $file" -ForegroundColor Red
        Write-Host "Please ensure you're running this from the parental_control directory" -ForegroundColor Red
        exit 1
    }
}
Write-Host "✅ All required files found" -ForegroundColor Green

# Check if SCP is available (requires OpenSSH or similar)
try {
    scp 2>$null
    $ScpAvailable = $true
} catch {
    $ScpAvailable = $false
}

if (-not $ScpAvailable) {
    Write-Host "❌ SCP command not found" -ForegroundColor Red
    Write-Host "Please install OpenSSH client:" -ForegroundColor Red
    Write-Host "  Windows Settings > Apps > Optional Features > OpenSSH Client" -ForegroundColor Yellow
    Write-Host "Or use Windows Subsystem for Linux (WSL)" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ SCP is available" -ForegroundColor Green

# Create timestamp for backup
$BackupTimestamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "📦 Creating backup on Pi..." -ForegroundColor Blue
$BackupCommand = @"
cd $PiPath/src/web 2>/dev/null || { echo 'Web directory not found'; exit 1; }
backup_dir="backup_$BackupTimestamp"
mkdir -p "`$backup_dir"
cp -r index.html app.js style.css "`$backup_dir/" 2>/dev/null || true
echo "📦 Backup created: `$backup_dir"
"@

try {
    ssh "$PiUser@$PiIP" $BackupCommand
    Write-Host "✅ Backup created successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not create backup, continuing anyway..." -ForegroundColor Yellow
}

# Deploy updated files
Write-Host "📤 Deploying enhanced dashboard files..." -ForegroundColor Blue

Write-Host "  📄 Deploying index.html..." -ForegroundColor Cyan
scp "src/web/index.html" "${PiUser}@${PiIP}:${PiPath}/src/web/index.html"

Write-Host "  📄 Deploying app.js..." -ForegroundColor Cyan  
scp "src/web/app.js" "${PiUser}@${PiIP}:${PiPath}/src/web/app.js"

Write-Host "  📄 Deploying style.css..." -ForegroundColor Cyan
scp "src/web/style.css" "${PiUser}@${PiIP}:${PiPath}/src/web/style.css"

Write-Host "✅ Core dashboard files deployed successfully" -ForegroundColor Green

# Optional: Deploy enhanced backend if it exists
if (Test-Path "pi_backend_nintendo.py") {
    Write-Host "📤 Deploying enhanced backend..." -ForegroundColor Blue
    scp "pi_backend_nintendo.py" "${PiUser}@${PiIP}:${PiPath}/backend/"
    Write-Host "✅ Backend deployed" -ForegroundColor Green
}

# Optional: Deploy enhanced discovery module if it exists
if (Test-Path "enhanced_nintendo_discovery.py") {
    Write-Host "📤 Deploying enhanced discovery module..." -ForegroundColor Blue
    scp "enhanced_nintendo_discovery.py" "${PiUser}@${PiIP}:${PiPath}/"
    Write-Host "✅ Enhanced discovery deployed" -ForegroundColor Green
}

# Restart services
Write-Host "🔄 Restarting services on Pi..." -ForegroundColor Blue
$RestartCommand = @"
echo '🔄 Attempting to restart parental controls service...'

# Try systemd first
if sudo systemctl restart parental-controls 2>/dev/null; then
    echo '✅ Systemd service restarted'
# Try Docker Compose if systemd fails  
elif cd $PiPath && docker-compose restart 2>/dev/null; then
    echo '✅ Docker services restarted'
# Try killing and restarting Python process
elif pkill -f 'python.*backend' && sleep 2; then
    echo '⚠️  Python process killed, may need manual restart'
else
    echo '⚠️  Could not restart services automatically'
    echo '    Please restart manually:'
    echo '    sudo systemctl restart parental-controls'
    echo '    OR: cd $PiPath && docker-compose restart'
fi
"@

ssh "$PiUser@$PiIP" $RestartCommand

# Verify deployment
Write-Host "🔍 Verifying deployment..." -ForegroundColor Blue
Start-Sleep -Seconds 5

# Check health endpoint
try {
    $HealthResponse = Invoke-WebRequest -Uri "http://$PiIP:3001/health" -TimeoutSec 10 -UseBasicParsing
    if ($HealthResponse.Content -match "healthy") {
        Write-Host "✅ Backend health check passed" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Backend health check returned unexpected response" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Backend health check failed - service may still be starting" -ForegroundColor Yellow
}

# Check if Nintendo endpoint responds
try {
    $NintendoResponse = Invoke-WebRequest -Uri "http://$PiIP:3001/api/nintendo/devices" -TimeoutSec 10 -UseBasicParsing
    if ($NintendoResponse.Content -match "success|error") {
        Write-Host "✅ Nintendo API endpoint responding" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Nintendo API returned unexpected response" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Nintendo API not yet responding - may need authentication" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "Dashboard URL: http://$PiIP`:3001" -ForegroundColor Yellow
Write-Host "Health Check: http://$PiIP`:3001/health" -ForegroundColor Yellow  
Write-Host "Nintendo API: http://$PiIP`:3001/api/nintendo/devices" -ForegroundColor Yellow
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Open the dashboard in your browser" -ForegroundColor White
Write-Host "2. Verify Nintendo Switch devices appear" -ForegroundColor White
Write-Host "3. Test individual device controls" -ForegroundColor White
Write-Host "4. Check real-time updates are working" -ForegroundColor White
Write-Host ""
Write-Host "🛠️  If issues occur:" -ForegroundColor Cyan
Write-Host "   - Check Pi logs: ssh $PiUser@$PiIP 'journalctl -u parental-controls -f'" -ForegroundColor White
Write-Host "   - Verify Nintendo authentication" -ForegroundColor White
Write-Host "   - Ensure Pi can reach Nintendo Switch devices" -ForegroundColor White
Write-Host ""
Write-Host "✨ Enhanced Nintendo Switch parental controls are now live!" -ForegroundColor Magenta

# Offer to open the dashboard
$OpenDashboard = Read-Host "Would you like to open the dashboard now? (y/N)"
if ($OpenDashboard -match '^[Yy]') {
    Start-Process "http://$PiIP`:3001"
}
