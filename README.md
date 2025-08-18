# Parental Controls Automation System

Used to easily control devices and block access for kids that haven't done their chores.

A comprehensive parental controls system that integrates multiple platforms and provides network-level blocking through OPNsense firewall integration.

## 🎯 Overview

This system provides automated parental controls with:
- **Web Dashboard**: Simple toggle interface for enabling/disabling controls
- **Network-Level Blocking**: Integration with OPNsense firewall for MAC address-based device blocking
- **Platform Integration Ready**: Architecture supports Nintendo Switch, Google Family, Microsoft Family
- **Raspberry Pi Deployment**: Containerized deployment with Docker and nginx
- **Real-time Control**: Instant toggle of parental controls with visual feedback

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Dashboard │    │  Flask Backend  │    │ OPNsense Router │
│                 │    │                 │    │                 │
│ • Toggle UI     │◄──►│ • MAC Management│◄──►│ • Firewall Rules│
│ • Status Display│    │ • API Endpoints │    │ • Device Blocking│
│ • Activity Log  │    │ • SSH Integration│    │ • Network Control│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Features

### ✅ Currently Working
- **Network Blocking**: MAC address-based device blocking via OPNsense firewall
- **Web Dashboard**: Modern, responsive interface with real-time status
- **Device Management**: Add/remove/edit devices to be controlled
- **Instant Toggle**: Enable/disable parental controls with a single click
- **Visual Feedback**: Color-coded status (red=blocked, green=allowed)
- **Activity Logging**: Track all control changes with timestamps
- **Docker Deployment**: Containerized for easy Raspberry Pi deployment

### 🚧 Platform Integrations (Planned)
- Nintendo Switch parental controls API
- Google Family API integration
- Microsoft Family API integration

## 📋 Prerequisites

- **Raspberry Pi** (3B+ or newer recommended)
- **OPNsense Router** with SSH access
- **Docker & Docker Compose** installed on Pi
- **SSH Key Access** to OPNsense router

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone https://github.com/armnhamcigol/parental_controls.git
cd parental_controls
```

### 2. Configure Device List
Edit `mac_addresses/devices.txt` with your devices:
```
# Format: MAC Address, Device Name, Notes
aa:bb:cc:dd:ee:ff, Johnny's Switch, Nintendo Switch
11:22:33:44:55:66, Sarah's Tablet, Android Tablet
```

### 3. Set Up SSH Keys
```bash
# Generate SSH key for OPNsense access
ssh-keygen -t ed25519 -f ~/.ssh/opnsense_ed25519

# Copy public key to OPNsense router
ssh-copy-id -i ~/.ssh/opnsense_ed25519.pub root@your-opnsense-ip
```

### 4. Configure Backend
Edit `backend/backend.py` settings:
```python
OPNSENSE_HOST = "192.168.1.1"  # Your OPNsense IP
SSH_KEY_PATH = "/home/pi/.ssh/opnsense_ed25519"
MAC_FILE_PATH = "/home/pi/parental-controls/mac_addresses/devices.txt"
```

### 5. Deploy to Raspberry Pi
```bash
# Copy project to Pi
scp -r . pi@your-pi-ip:/home/pi/parental-controls/

# Run deployment script
ssh pi@your-pi-ip
cd /home/pi/parental-controls
chmod +x scripts/deploy-pi.sh
./scripts/deploy-pi.sh
```

## 🌐 Usage

### Access Dashboard
Open your browser to: `https://your-pi-ip:8443`

### Toggle Controls
- **Green Toggle**: Parental controls OFF (kids have access)
- **Red Toggle**: Parental controls ON (devices blocked)

### Add/Remove Devices
1. Edit `mac_addresses/devices.txt`
2. Restart the backend service
3. Changes are automatically synced to OPNsense

## 📁 Project Structure

```
parental-controls-automation/
├── README.md                 # This file
├── WARP.md                  # Development history
├── package.json             # Node.js dependencies
├── docker-compose.yml       # Docker orchestration
├── Dockerfile               # Container definition
├── .gitignore              # Git ignore rules
│
├── src/                     # Source code
│   ├── web/                # Frontend files
│   │   ├── index.html      # Dashboard HTML
│   │   ├── style.css       # Dashboard styles
│   │   └── app.js          # Dashboard JavaScript
│   ├── utils/              # Utility modules
│   │   ├── logger.js       # Winston logging
│   │   ├── config.js       # Configuration manager
│   │   └── validation.js   # System validation
│   └── server.js           # Express server (demo)
│
├── backend/                 # Python backend
│   ├── backend.py          # Main Flask application
│   ├── mac_manager.py      # MAC address management
│   └── opnsense_integration.py # OPNsense firewall integration
│
├── config/                  # Configuration files
│   └── *.json              # Various config files
│
├── mac_addresses/           # Device management
│   └── devices.txt         # MAC address list
│
├── scripts/                 # Deployment & utility scripts
│   ├── deploy-pi.sh        # Raspberry Pi deployment
│   ├── add_static_routes.py # Network utilities
│   └── debug_opnsense_rule.py # Debugging tools
│
├── logs/                    # Application logs
├── tests/                   # Test files
└── archive/                 # Development artifacts
```

## 🔧 Configuration

### OPNsense Settings
The system creates:
- **Firewall Alias**: `parental_control_devices` containing MAC addresses
- **Firewall Rule**: Blocks traffic from devices in the alias
- **Toggle Control**: Enable/disable the rule via SSH

### Network Requirements
- All devices must be on the same subnet as OPNsense
- OPNsense must have SSH access enabled
- MAC address filtering must be supported by your network setup

## 🔍 Troubleshooting

### Dashboard Not Loading
1. Check if backend is running: `ssh pi "ps aux | grep backend.py"`
2. Check backend logs: `ssh pi "tail -f /home/pi/parental-controls/backend/backend.log"`
3. Verify nginx is running: `ssh pi "sudo systemctl status nginx"`

### Devices Not Being Blocked
1. Verify OPNsense SSH connectivity: `ssh root@opnsense-ip`
2. Check firewall rule exists: Log into OPNsense web interface → Firewall → Rules
3. Verify MAC addresses are correct in devices.txt
4. Check OPNsense logs for blocked traffic

### Toggle Not Working
1. Open browser developer tools (F12) and check console for errors
2. Clear browser cache and hard refresh (Ctrl+Shift+R)
3. Check backend API status: `curl http://pi-ip:3001/api/status`

## 📊 API Reference

### GET /api/status
Returns current system status
```json
{
  "controlsActive": true,
  "systemStatus": "ready",
  "uptime": 3600,
  "opnsense": {
    "alias_exists": true,
    "rule_exists": true,
    "rule_enabled": true,
    "device_count": 7
  }
}
```

### POST /api/toggle?active=true&reason=Manual
Toggle parental controls
```json
{
  "success": true,
  "controlsActive": true,
  "message": "Parental controls activated"
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎯 Roadmap

- [ ] Nintendo Switch API integration
- [ ] Google Family API integration  
- [ ] Microsoft Family API integration
- [ ] Mobile app for remote control
- [ ] Scheduling and time-based controls
- [ ] Usage analytics and reporting
- [ ] Multi-user support with different profiles

## 🙏 Acknowledgments

- OPNsense team for excellent firewall software
- Flask and Express.js communities
- Docker team for containerization platform

---

*Built with ❤️ for better family digital wellness*
