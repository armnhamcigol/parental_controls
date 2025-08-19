# 🎮 Enhanced Nintendo Switch Dashboard - Raspberry Pi Deployment

## 📋 Overview

This guide will help you deploy the enhanced Nintendo Switch parental controls dashboard to your Raspberry Pi. The updated dashboard includes:

- ✅ **Live Device Detection** - Real online/offline status
- ⚡ **Response Time Monitoring** - Network performance tracking  
- 🎯 **Game Activity Detection** - Currently playing game detection
- 📊 **Activity Level Analysis** - High/medium/low activity detection
- ⏱️ **Session Time Tracking** - Real play time monitoring
- 🔄 **Continuous Monitoring** - Updates every 30 seconds
- 🎛️ **Individual Device Control** - Toggle controls per device

## 🚀 Quick Deployment

### Method 1: Direct File Transfer (Recommended)

1. **Copy the updated files to your Raspberry Pi:**

```bash
# From your Windows machine, copy the updated dashboard files to Pi
scp C:/Warp/parental_control/src/web/* pi@YOUR_PI_IP:/home/pi/parental-controls/src/web/
```

2. **SSH into your Raspberry Pi:**

```bash
ssh pi@YOUR_PI_IP
```

3. **Backup existing dashboard (optional):**

```bash
cd /home/pi/parental-controls/src/web
cp -r . ./backup_$(date +%Y%m%d_%H%M%S)/
```

4. **Restart the backend service:**

```bash
sudo systemctl restart parental-controls
# OR if using Docker:
docker-compose restart
```

### Method 2: Manual File Update

If SCP is not available, manually update each file:

#### 1. Update `index.html`

```bash
sudo nano /home/pi/parental-controls/src/web/index.html
```

Copy the contents from `C:/Warp/parental_control/src/web/index.html`

#### 2. Update `app.js`

```bash
sudo nano /home/pi/parental-controls/src/web/app.js
```

Copy the contents from `C:/Warp/parental_control/src/web/app.js`

#### 3. Update `style.css`

```bash
sudo nano /home/pi/parental-controls/src/web/style.css
```

Copy the contents from `C:/Warp/parental_control/src/web/style.css`

## 🔧 Backend Integration Requirements

Ensure your Pi backend has the enhanced Nintendo Switch discovery integrated:

### 1. Update Backend Python File

```bash
# Copy the enhanced backend
scp C:/Warp/parental_control/pi_backend_nintendo.py pi@YOUR_PI_IP:/home/pi/parental-controls/backend/
```

### 2. Install Enhanced Discovery Module

```bash
ssh pi@YOUR_PI_IP
cd /home/pi/parental-controls
pip install -r requirements.txt
# Copy enhanced discovery module if needed
```

### 3. Update Configuration

Ensure your Pi backend configuration includes:

```python
# Nintendo Switch Configuration
NINTENDO_ENHANCED_DISCOVERY = True
NINTENDO_DISCOVERY_INTERVAL = 60  # seconds
NINTENDO_API_ENDPOINTS = [
    '/api/nintendo/devices',
    '/api/nintendo/device_toggle',
    '/api/nintendo/toggle',
    '/health'
]
```

## 📱 Dashboard Access

After deployment, access your enhanced dashboard at:

- **Main Dashboard:** `http://YOUR_PI_IP:3001`
- **Health Check:** `http://YOUR_PI_IP:3001/health`
- **Nintendo Devices API:** `http://YOUR_PI_IP:3001/api/nintendo/devices`

## 🔍 Verification Steps

1. **Check Backend Health:**

```bash
curl http://YOUR_PI_IP:3001/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Parental Controls Backend with Nintendo Switch",
  "version": "1.1.0",
  "components": {
    "opnsense": "healthy",
    "mac_manager": "healthy",
    "nintendo": "connected"
  }
}
```

2. **Test Nintendo Device Discovery:**

```bash
curl http://YOUR_PI_IP:3001/api/nintendo/devices
```

Expected response:
```json
{
  "success": true,
  "devices": [
    {
      "device_id": "newswitch",
      "device_name": "newswitch",
      "online": true,
      "current_game": "The Legend of Zelda: Breath of the Wild",
      "response_time_ms": 17.34,
      "enhanced_discovery": true
    }
  ],
  "count": 1
}
```

3. **Open Dashboard:**

Navigate to `http://YOUR_PI_IP:3001` and verify:
- ✅ Nintendo Switch devices appear
- ✅ Real-time status updates
- ✅ Individual device controls work
- ✅ Game detection is active

## 🛠️ Troubleshooting

### Dashboard Not Loading

```bash
# Check if service is running
sudo systemctl status parental-controls

# Check logs
journalctl -u parental-controls -f

# Restart service
sudo systemctl restart parental-controls
```

### Nintendo Devices Not Showing

```bash
# Check Nintendo authentication
python3 -c "from backend.nintendo_manager import NintendoManager; nm = NintendoManager(); print('Auth:', nm.is_authenticated())"

# Test device discovery
curl -v http://localhost:3001/api/nintendo/devices
```

### Enhanced Discovery Issues

```bash
# Check enhanced discovery module
python3 -c "
try:
    from enhanced_nintendo_discovery import EnhancedNintendoDiscovery
    print('✅ Enhanced discovery available')
except ImportError:
    print('❌ Enhanced discovery not found')
"
```

## 📁 File Structure

After deployment, your Pi should have:

```
/home/pi/parental-controls/
├── backend/
│   ├── pi_backend_nintendo.py      # Enhanced backend
│   └── nintendo_manager.py
├── src/web/
│   ├── index.html                  # Enhanced dashboard HTML
│   ├── app.js                      # Enhanced dashboard JS
│   └── style.css                   # Enhanced dashboard CSS
└── enhanced_nintendo_discovery.py  # Discovery module
```

## 🎯 Features Verification

After deployment, verify these features work:

- [ ] Dashboard loads at `http://YOUR_PI_IP:3001`
- [ ] Nintendo Switch devices appear in device cards
- [ ] Online/offline status shows correctly
- [ ] Current games are detected and displayed
- [ ] Response times are shown
- [ ] Activity levels are calculated
- [ ] Individual device toggles work
- [ ] Real-time updates every 30 seconds
- [ ] Enhanced discovery badge appears
- [ ] System status shows "Connected" for Nintendo

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify network connectivity to Nintendo Switch devices
3. Ensure Nintendo authentication is working
4. Check Pi system logs and resources
5. Verify backend API endpoints are responding

## 🎉 Completion

Once deployed successfully, you'll have a production-ready Nintendo Switch parental controls dashboard with:

- **Live monitoring** of all Nintendo Switch devices
- **Real-time game detection** and session tracking  
- **Individual device controls** with toggle switches
- **Enhanced network discovery** with performance metrics
- **Professional dashboard interface** with responsive design

Your enhanced Nintendo Switch parental controls are now ready for use!
