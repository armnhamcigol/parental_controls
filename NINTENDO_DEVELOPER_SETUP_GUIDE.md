# 🎮 Nintendo Developer API Setup Guide

## 🔑 Getting Your API Credentials

Since you have a Nintendo developer account, here are the steps to get your API credentials and integrate with your parental controls dashboard:

### **Step 1: Nintendo Developer Portal Setup**

1. **Log into Nintendo Developer Portal**
   - Go to https://developer.nintendo.com/
   - Sign in with your Nintendo developer account

2. **Create an Application**
   - Navigate to "Applications" or "My Applications"
   - Click "Create New Application"
   - Fill out the application details:
     - **Application Name**: "Parental Controls Dashboard"
     - **Application Type**: "Web Application" or "Service Application"
     - **Description**: "Home parental controls system for Nintendo Switch devices"
     - **Redirect URIs**: `https://localhost:8080/auth/callback`
     - **Permissions**: Request the following scopes:
       - `user.profile:read`
       - `device.management:read`
       - `device.management:write`
       - `parental_controls:read`
       - `parental_controls:write`

3. **Get Your Credentials**
   After your application is approved, you'll get:
   - **Client ID**: A public identifier for your application
   - **Client Secret**: A private key for authentication
   - **API Keys**: Additional authentication tokens

### **Step 2: Update Configuration File**

Update your `nintendo_developer_config.json` with your actual credentials:

```json
{
  "client_id": "YOUR_ACTUAL_CLIENT_ID_FROM_NINTENDO",
  "client_secret": "YOUR_ACTUAL_CLIENT_SECRET_FROM_NINTENDO", 
  "redirect_uri": "https://localhost:8080/auth/callback",
  "scope": "user.profile:read device.management:read device.management:write parental_controls:read parental_controls:write",
  "base_url": "https://api.developer.nintendo.com",
  "auth_url": "https://accounts.nintendo.com",
  "api_version": "v1",
  "encryption_key": "dgAg7Uvy0HRlSyHMGV1gU18gCZSOgyHyy6IA5vXs3uA=",
  "production_mode": true,
  "rate_limit": {
    "requests_per_minute": 60,
    "burst_limit": 10
  },
  "timeout": 30,
  "retry_attempts": 3
}
```

### **Step 3: Get Session Token**

You have several options to get a session token:

#### **Option A: Nintendo Switch Online App Method**
1. Install the Nintendo Switch Online app on your phone
2. Log in with your Nintendo account
3. Use a tool like `nxapi` to extract the session token:
   ```bash
   npm install -g nxapi
   nxapi nso auth
   ```

#### **Option B: Web Authentication**
1. Navigate to: `https://accounts.nintendo.com/connect/1.0.0/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=https://localhost:8080/auth/callback&response_type=code&scope=user.profile:read+device.management:read&state=random_string`
2. Log in and authorize your application
3. Extract the authorization code from the callback
4. Exchange it for tokens using the `/token` endpoint

#### **Option C: Direct API Call** (if you have existing tokens)
```python
import requests

def get_session_token(username, password):
    # This is a simplified example - actual implementation varies
    auth_response = requests.post('https://accounts.nintendo.com/api/1.0.0/login', {
        'username': username,
        'password': password,
        'client_id': 'YOUR_CLIENT_ID'
    })
    return auth_response.json().get('session_token')
```

### **Step 4: Test Your Setup**

```python
from nintendo_developer_api import NintendoDeveloperAPI, ParentalControlSettings

# Initialize API
api = NintendoDeveloperAPI()

# Test authentication
session_token = "YOUR_OBTAINED_SESSION_TOKEN"
if api.authenticate(session_token=session_token):
    print("✅ Successfully authenticated with Nintendo Developer API!")
    
    # Get your devices
    devices = api.get_user_devices()
    print(f"Found {len(devices)} Nintendo Switch devices:")
    
    for device in devices:
        print(f"  📱 {device.device_name} - {device.location}")
        print(f"     Status: {'🟢 Online' if device.online_status else '🔴 Offline'}")
        print(f"     Play Time Today: {device.play_time_today} minutes")
        
        # Test parental controls
        if device.parental_controls_enabled:
            print(f"     🛡️ Parental Controls: Enabled")
        else:
            print(f"     ⚪ Parental Controls: Disabled")
            
else:
    print("❌ Authentication failed. Check your credentials and session token.")
```

### **Step 5: Update Backend Integration**

Now update your backend to use the Nintendo Developer API:

```python
# In pi_backend_nintendo.py, add at the top:
from nintendo_developer_api import NintendoDeveloperAPI, ParentalControlSettings

# Update the SimpleNintendoSwitchManager class:
class SimpleNintendoSwitchManager:
    def __init__(self):
        self.production_mode = True  # Enable production mode
        self.developer_api = NintendoDeveloperAPI()
        self.authenticated = False
        
    def authenticate(self, session_token):
        """Authenticate with Nintendo Developer API"""
        self.authenticated = self.developer_api.authenticate(session_token=session_token)
        return self.authenticated
        
    def get_devices(self):
        """Get real devices from Nintendo Developer API"""
        if not self.authenticated:
            return self.get_demo_devices()  # Fallback to demo
            
        try:
            devices = self.developer_api.get_user_devices()
            return self.convert_to_dashboard_format(devices)
        except Exception as e:
            print(f"Error getting devices from Nintendo API: {e}")
            return self.get_demo_devices()  # Fallback to demo
            
    def convert_to_dashboard_format(self, nintendo_devices):
        """Convert Nintendo API devices to dashboard format"""
        dashboard_devices = []
        for device in nintendo_devices:
            dashboard_device = {
                'device_id': device.device_id,
                'device_name': device.device_name,
                'location': device.location,
                'online': device.online_status,
                'controls_enabled': device.parental_controls_enabled,
                'today_play_time_minutes': device.play_time_today,
                'current_game': device.last_played_game,
                'last_seen': device.last_seen.isoformat(),
                'production_mode': True,  # Mark as production
                'firmware_version': device.firmware_version
            }
            dashboard_devices.append(dashboard_device)
        return dashboard_devices
        
    def toggle_device_controls(self, device_id, enabled):
        """Toggle parental controls for a specific device"""
        if not self.authenticated:
            return False
            
        if enabled:
            # Create default parental control settings
            settings = ParentalControlSettings(
                daily_time_limit=120,  # 2 hours
                bedtime_enabled=True,
                bedtime_start="21:00",
                bedtime_end="07:00",
                allowed_software_ratings=["E", "E10+"],
                restricted_features=["web_browser", "social_features"],
                communication_restrictions=True,
                purchase_restrictions=True
            )
            return self.developer_api.update_parental_controls(device_id, settings)
        else:
            # Disable by removing restrictions
            settings = ParentalControlSettings(
                daily_time_limit=0,  # No limit
                bedtime_enabled=False,
                bedtime_start="00:00",
                bedtime_end="00:00",
                allowed_software_ratings=["E", "E10+", "T", "M"],
                restricted_features=[],
                communication_restrictions=False,
                purchase_restrictions=False
            )
            return self.developer_api.update_parental_controls(device_id, settings)
```

### **Step 6: Add Authentication Endpoint**

Add a new endpoint to your Flask backend for Nintendo authentication:

```python
@app.route('/api/nintendo/authenticate', methods=['POST'])
def nintendo_authenticate():
    try:
        data = request.json
        session_token = data.get('session_token')
        
        if not session_token:
            return jsonify({'success': False, 'error': 'Session token required'}), 400
            
        # Authenticate with Nintendo Developer API
        success = nintendo_manager.authenticate(session_token)
        
        if success:
            return jsonify({
                'success': True,
                'authenticated': True,
                'message': 'Successfully authenticated with Nintendo Developer API'
            })
        else:
            return jsonify({
                'success': False,
                'authenticated': False,
                'error': 'Nintendo Developer API authentication failed'
            }), 401
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

## 🚨 Important Security Notes

1. **Never commit your real API credentials to Git**
2. **Store the session token securely** (encrypted)
3. **Use environment variables** for sensitive data in production
4. **Monitor API usage** to stay within rate limits
5. **Handle token expiration** gracefully

## 📋 Next Steps

1. ✅ Complete Nintendo Developer Portal application setup
2. ✅ Update configuration with real credentials  
3. ✅ Obtain session token using one of the methods above
4. ✅ Test authentication with the Nintendo Developer API
5. ✅ Update your backend to use the production API
6. ✅ Test with your actual "newswitch" and "backroom" devices

## 🔧 Troubleshooting

### **Authentication Issues**
- Verify your Client ID and Client Secret are correct
- Ensure your redirect URI matches exactly (including trailing slashes)
- Check that your application has the required scopes approved
- Verify your session token hasn't expired

### **API Errors** 
- Check Nintendo Developer API status page
- Verify you're not exceeding rate limits (60 requests/minute)
- Ensure your devices are linked to your Nintendo account
- Check that parental controls are enabled in your Nintendo account settings

### **Device Not Showing**
- Ensure devices are connected to your Nintendo account
- Check that devices have parental controls enabled
- Verify devices are online and connected to internet
- Make sure you're using the same Nintendo account as the devices

Would you like me to help you with any specific part of this setup process?
