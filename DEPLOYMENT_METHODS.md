# AI Parental Controls - Pi Deployment Methods

## 🎯 **DEPLOYMENT PACKAGE READY!**

Your complete AI parental control system is packaged and ready for deployment:
- **📁 Folder:** `pi_deployment/`
- **📦 ZIP file:** `ai_parental_controls_pi.zip`

## 🚀 **Deployment Options**

### **Option A: SSH Transfer (Recommended if SSH works)**
```bash
# Test SSH first
ssh pi@192.168.123.240 "echo 'SSH working'"

# If SSH works, transfer the files
scp ai_parental_controls_pi.zip pi@192.168.123.240:/home/pi/
ssh pi@192.168.123.240 "cd /home/pi && unzip ai_parental_controls_pi.zip && mv pi_deployment ai_parental_controls"
```

### **Option B: USB Transfer (Most Reliable)**
1. **Copy to USB:**
   - Copy `ai_parental_controls_pi.zip` to a USB drive
   
2. **On the Pi:**
   ```bash
   # Insert USB and mount if needed
   sudo mkdir -p /mnt/usb
   sudo mount /dev/sda1 /mnt/usb  # Adjust device as needed
   
   # Copy and extract
   cp /mnt/usb/ai_parental_controls_pi.zip /home/pi/
   cd /home/pi
   unzip ai_parental_controls_pi.zip
   mv pi_deployment ai_parental_controls
   ```

### **Option C: Web Transfer (If Pi has web server)**
If your Pi is running a web server, you can download directly:
```bash
# On the Pi
wget http://[YOUR_WINDOWS_IP]:8000/ai_parental_controls_pi.zip
unzip ai_parental_controls_pi.zip
mv pi_deployment ai_parental_controls
```

### **Option D: Network Share (SMB/CIFS)**
If you have network sharing set up:
```bash
# Mount Windows share and copy
sudo mount -t cifs //192.168.123.XXX/share /mnt/share -o username=yourusername
cp /mnt/share/ai_parental_controls_pi.zip /home/pi/
```

## 🔧 **Setup on Pi (After File Transfer)**

1. **Navigate to the directory:**
   ```bash
   cd /home/pi/ai_parental_controls
   ```

2. **Make setup script executable:**
   ```bash
   chmod +x setup_pi.sh
   ```

3. **Run setup (installs dependencies):**
   ```bash
   ./setup_pi.sh
   ```

4. **Start the AI server:**
   ```bash
   python3 run_pi_server.py
   ```

## 🌐 **Access from Network**

Once running, access from any device on your network:
- **Main Dashboard:** `http://192.168.123.240:5000`
- **AI Assistant:** `http://192.168.123.240:5000/ai-staging`
- **API Key:** `test-api-key-staging-12345`

## 📋 **What's Included in Package**

✅ **Backend Files:**
- `real_backend.py` - Main Flask server
- `mcp_server.py` - AI integration layer  
- `opnsense_integration.py` - Firewall control
- `mac_manager.py` - Device management
- `nintendo_integration.py` - Nintendo Switch controls

✅ **Frontend:**
- `enhanced_dashboard.html` - Web interface

✅ **Configuration:**
- `run_pi_server.py` - Pi-optimized startup script
- `requirements.txt` - Python dependencies
- `setup_pi.sh` - Automated setup script

✅ **Testing:**
- `quick_test.py` - Functionality tests
- `test_commands.txt` - Manual test commands

## 🔍 **Pi Compatibility Notes**

- **Python 3.7+** required (standard on Raspberry Pi OS)
- **Flask 3.0.0** for web server
- **Paramiko 3.4.0** for SSH connections
- **Requests 2.31.0** for HTTP calls
- **Network accessible** on port 5000
- **Ollama connection** to port 8034 (your existing setup)

## 🧪 **Testing on Pi**

After setup, test with:
```bash
# Basic connectivity
python3 quick_test.py

# Or manual web interface
# Open browser to: http://192.168.123.240:5000/ai-staging
```

## 🚨 **Troubleshooting**

1. **Permission denied:** `chmod +x run_pi_server.py`
2. **Port already in use:** Check for existing servers with `netstat -tlnp | grep :5000`
3. **Can't access from other devices:** Check Pi firewall with `sudo ufw status`
4. **AI not responding:** Verify Ollama running with `curl http://localhost:8034/api/tags`

Which deployment method would work best for you?
