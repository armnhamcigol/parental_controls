# AI Parental Controls - Raspberry Pi Deployment

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
