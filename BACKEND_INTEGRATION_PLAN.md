# Parental Controls Backend Integration Plan

## Architecture Overview

The parental controls system will have multiple layers of control:

### 1. **Network-Level Controls** (Primary)
- **Router/Firewall Integration**: Block/allow traffic at network level
- **DNS Filtering**: Redirect gaming/social media domains
- **Local iptables Rules**: Backup firewall on Pi itself

### 2. **Device-Specific Controls** (Secondary)  
- **Nintendo Switch**: Parental Controls API
- **Google/Android**: Family Link API
- **Microsoft/Xbox**: Family Safety API
- **iOS Devices**: Screen Time API (if available)

### 3. **Service-Level Controls** (Tertiary)
- **Time-based scheduling**: Automatic enable/disable
- **Activity monitoring**: Track usage and violations
- **Notification system**: Alert parents of status changes

## Implementation Strategy

### Phase 1: Network-Level Controls (Start Here)
```
Pi → Router API/SSH → Block gaming sites/services
└── Fallback: Pi iptables rules for known gaming IPs
```

**Benefits:**
- ✅ Works for ALL devices on network
- ✅ Cannot be bypassed by kids
- ✅ No device-specific setup needed
- ✅ Immediate effect

**Implementation Options:**
1. **OPNSense/pfSense API** (if router supports)
2. **Router SSH/Telnet** (for advanced routers)
3. **DNS manipulation** (Pi-hole style)
4. **Local iptables** (as backup/standalone)

### Phase 2: Device-Specific Controls
```
Pi → Device APIs → Platform-specific restrictions
├── Nintendo Switch Parental Controls
├── Google Family Link
├── Microsoft Family Safety
└── Custom device agents
```

### Phase 3: Advanced Features
- **Schedule-based controls**
- **Activity tracking and reporting**
- **Mobile app notifications**
- **Integration with calendar/homework schedule**

## Quick Implementation: DNS + iptables

Let's start with a simple but effective approach:

### DNS Blackholing
```bash
# Block gaming domains via /etc/hosts or Pi-hole
echo "127.0.0.1 nintendo.com" >> /etc/hosts
echo "127.0.0.1 xbox.com" >> /etc/hosts
echo "127.0.0.1 playstation.com" >> /etc/hosts
```

### iptables Firewall Rules
```bash
# Block known gaming services by IP
iptables -A FORWARD -d gaming-servers -j DROP
iptables -A OUTPUT -d gaming-servers -j DROP
```

### Router Integration
```python
# Example router API call
import requests

def toggle_parental_controls(enable=True):
    router_api = "http://192.168.123.1/api/firewall/rules"
    payload = {"block_gaming": enable}
    response = requests.post(router_api, auth=("admin", password), json=payload)
    return response.status_code == 200
```

## Backend API Structure

Replace the demo `/api/toggle` endpoint with real functionality:

```javascript
// Real backend toggle
app.post('/api/toggle', async (req, res) => {
    try {
        const { active } = req.body;
        
        // 1. Update network rules
        await updateNetworkRules(active);
        
        // 2. Update device controls  
        await updateDeviceControls(active);
        
        // 3. Log the change
        await logToggleEvent(active, req.ip);
        
        res.json({
            success: true,
            controlsActive: active,
            message: `Parental controls ${active ? 'activated' : 'deactivated'}`,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});
```

## Integration Targets

### High Priority (Network-Level)
- ✅ **DNS blackholing** - Block gaming domains
- ✅ **iptables rules** - Block gaming IPs  
- ✅ **Router integration** - If API available
- ✅ **Time-based automation** - Schedule controls

### Medium Priority (Device-Level)
- 🎮 **Nintendo Switch** - Parental Controls API
- 📱 **Google Family Link** - Android device management
- 🎮 **Xbox/Microsoft** - Family Safety API
- 📺 **Smart TV controls** - Samsung/LG APIs

### Low Priority (Advanced)
- 📊 **Usage tracking** - Monitor blocked attempts
- 📱 **Mobile notifications** - Push alerts to parents
- 🗓️ **Calendar integration** - Homework/bedtime schedule
- 🏠 **Home automation** - Smart home device integration

## Next Steps

1. **Implement DNS blackholing** (Quick win)
2. **Add iptables integration** (Robust backup)
3. **Create real backend API** (Replace demo mode)
4. **Test with actual gaming devices** (Validation)
5. **Add router integration** (If supported)
6. **Expand to device APIs** (Future enhancement)

This approach gives us immediate functionality while building toward a comprehensive solution.
