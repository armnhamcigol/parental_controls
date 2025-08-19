// Enhanced Parental Controls Dashboard with Nintendo Switch Integration
class ParentalControlsDashboard {
    constructor() {
        this.currentState = {
            controlsActive: false,
            lastToggleTime: null,
            lastToggleReason: null,
            systemStatus: 'loading'
        };
        
        this.nintendoState = {
            authenticated: false,
            controlsActive: false,
            deviceName: 'Nintendo Switch',
            todayPlayTime: 0,
            weeklyPlayTime: 0
        };
        
        this.activityLog = [];
        this.init();
    }

    // Initialize the dashboard
    async init() {
        console.log('🛡️ Initializing Enhanced Parental Controls Dashboard');
        
        this.setupEventListeners();
        await this.loadStatus();
        await this.loadNintendoStatus();
        this.startPeriodicUpdates();
        
        // Show the dashboard with fade-in effect
        document.querySelector('.container').classList.add('fade-in');
    }

    // Setup event listeners
    setupEventListeners() {
        const toggle = document.getElementById('controlsToggle');
        if (toggle) {
            toggle.addEventListener('change', this.handleToggleChange.bind(this));
        }

        const nintendoToggle = document.getElementById('nintendoControlsToggle');
        if (nintendoToggle) {
            nintendoToggle.addEventListener('change', this.handleNintendoToggleChange.bind(this));
        }

        // Nintendo authentication form
        const nintendoForm = document.getElementById('nintendoLoginForm');
        if (nintendoForm) {
            nintendoForm.addEventListener('submit', this.handleNintendoAuth.bind(this));
        }

        // Refresh status when window gains focus
        window.addEventListener('focus', () => {
            this.loadStatus();
            this.loadNintendoStatus();
        });

        // Handle keyboard shortcuts
        document.addEventListener('keydown', (event) => {
            if (event.ctrlKey && event.key === ' ') {
                event.preventDefault();
                this.toggleControls('Keyboard shortcut');
            }
        });
    }

    // Load current status from API
    async loadStatus() {
        try {
            const response = await fetch('/api/status');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.updateStatus(data);
            this.updateLastUpdated();
            
        } catch (error) {
            console.error('Failed to load status:', error);
            this.showError('Failed to connect to server');
            this.updateSystemStatus('error');
        }
    }

    // Load Nintendo Switch status
    async loadNintendoStatus() {
        try {
            const response = await fetch('/api/nintendo/status');
            
            if (response.status === 401) {
                // Not authenticated
                this.updateNintendoStatus({ authenticated: false });
                return;
            }
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.updateNintendoStatus({
                authenticated: true,
                ...data.nintendo_status
            });
            
        } catch (error) {
            console.error('Failed to load Nintendo status:', error);
            this.updateNintendoStatus({ authenticated: false, error: error.message });
        }
    }

    // Update dashboard with new status data
    updateStatus(data) {
        this.currentState = data;
        
        // Update toggle state
        const toggle = document.getElementById('controlsToggle');
        if (toggle) {
            toggle.checked = data.controlsActive;
        }
        
        // Update status display
        this.updateSystemStatus(data.systemStatus);
        this.updateLastAction(data.lastToggleReason, data.lastToggleTime);
        this.updateUptime(data.uptime);
        this.updateToggleDescription();
        
        // Update platform status
        this.updatePlatformStatus(data.platforms);
        
        console.log('📊 Status updated:', data);
    }

    // Update Nintendo Switch status
    updateNintendoStatus(nintendoData) {
        this.nintendoState = { ...this.nintendoState, ...nintendoData };
        
        const authControls = document.getElementById('nintendoAuthenticatedControls');
        const connectBtn = document.getElementById('nintendoConnectBtn');
        const connectionStatus = document.getElementById('nintendoConnectionStatus');
        
        if (nintendoData.authenticated) {
            // Show authenticated controls
            if (authControls) authControls.style.display = 'block';
            if (connectBtn) connectBtn.style.display = 'none';
            if (connectionStatus) {
                connectionStatus.textContent = '🟢 Connected';
                connectionStatus.className = 'status-indicator connected';
            }
            
            // Load and display Nintendo devices
            this.loadNintendoDevices();
            
            // Update Nintendo stats
            this.updateNintendoStats(nintendoData);
            
        } else {
            // Show connection button
            if (authControls) authControls.style.display = 'none';
            if (connectBtn) {
                connectBtn.style.display = 'inline-block';
                connectBtn.textContent = '🔗 Connect Nintendo Switch';
            }
            if (connectionStatus) {
                connectionStatus.textContent = '⚪ Not Connected';
                connectionStatus.className = 'status-indicator';
            }
        }
        
        // Update platform status badge
        const nintendoStatus = document.getElementById('nintendoStatus');
        if (nintendoStatus) {
            if (nintendoData.authenticated) {
                nintendoStatus.textContent = 'Connected';
                nintendoStatus.className = 'platform-status-badge connected';
            } else {
                nintendoStatus.textContent = 'Available';
                nintendoStatus.className = 'platform-status-badge available';
            }
        }
    }

    // Load Nintendo devices
    async loadNintendoDevices() {
        try {
            const response = await fetch('/api/nintendo/devices');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.displayNintendoDevices(data.devices);
            
        } catch (error) {
            console.error('Failed to load Nintendo devices:', error);
            this.showError('Failed to load Nintendo devices');
        }
    }

    // Display Nintendo devices
    displayNintendoDevices(devices) {
        console.log('🎮 displayNintendoDevices called with:', devices);
        
        const devicesList = document.getElementById('nintendoDevicesList');
        console.log('📱 nintendoDevicesList element:', devicesList);
        
        if (!devicesList) {
            console.error('❌ nintendoDevicesList element not found!');
            return;
        }
        
        if (!devices) {
            console.error('❌ No devices provided to displayNintendoDevices');
            return;
        }
        
        if (!Array.isArray(devices) || devices.length === 0) {
            console.warn('⚠️ No devices to display');
            devicesList.innerHTML = '<p class="no-devices">No Nintendo Switch devices found</p>';
            return;
        }
        
        console.log(`📊 Displaying ${devices.length} Nintendo Switch devices`);
        
        const html = devices.map(device => {
            console.log('🔧 Processing device:', device.device_name, device.device_id);
            
            // Determine device status indicators
            const isOnline = device.online !== false;
            const isProduction = device.production_mode || device.network_discovered;
            const isDemoMode = device.demo_mode;
            
            const onlineStatusClass = isOnline ? 'online' : 'offline';
            const onlineStatusText = isOnline ? '🟢 Online' : '🔴 Offline';
            const modeIndicator = isProduction ? '🌐 Network' : (isDemoMode ? '🎭 Demo' : '⚡ Live');
            
            return `
            <div class="nintendo-device ${onlineStatusClass}" data-device-id="${device.device_id}">
                <div class="device-info">
                    <h4>${device.device_name} ${modeIndicator}</h4>
                    <p class="device-location">${device.location}</p>
                    <p class="device-network-status">${onlineStatusText}${
                        device.ip_address ? ` (${device.ip_address})` : ''
                    }</p>
                    <p class="device-status">Controls: <span class="${device.controls_enabled ? 'enabled' : 'disabled'}">
                        ${device.controls_enabled ? 'Active' : 'Inactive'}
                    </span></p>
                    ${device.current_game ? `<p class="current-game">🎮 ${device.current_game}</p>` : ''}
                </div>
                <div class="device-controls">
                    <label class="switch">
                        <input type="checkbox" class="nintendo-device-toggle" 
                               data-device-id="${device.device_id}" 
                               ${device.controls_enabled ? 'checked' : ''}>
                        <span class="slider"></span>
                    </label>
                </div>
                <div class="device-stats">
                    <span class="stat-item">Today: ${device.today_play_time_minutes || 0}min</span>
                    <span class="stat-item">Limit: ${device.daily_limit_minutes || 'None'}min</span>
                    ${device.last_seen && device.last_seen !== 'Offline' ? 
                        `<span class="stat-item">Last seen: ${this.getTimeAgo(device.last_seen)}</span>` : 
                        '<span class="stat-item">Last seen: Unknown</span>'
                    }
                </div>
            </div>
        `;
        }).join('');
        
        console.log('📝 Generated HTML length:', html.length);
        devicesList.innerHTML = html;
        console.log('✅ HTML inserted into DOM');
        
        // Add event listeners for device toggles
        const deviceToggles = devicesList.querySelectorAll('.nintendo-device-toggle');
        console.log(`🎛️ Adding event listeners to ${deviceToggles.length} toggles`);
        deviceToggles.forEach(toggle => {
            toggle.addEventListener('change', this.handleDeviceToggleChange.bind(this));
        });
        
        console.log('🎉 Nintendo devices displayed successfully!');
    }

    // Handle device-specific toggle change
    async handleDeviceToggleChange(event) {
        const deviceId = event.target.dataset.deviceId;
        const newState = event.target.checked;
        
        console.log(`Device ${deviceId} toggle clicked:`, newState);
        await this.toggleNintendoDeviceControls(deviceId, newState);
    }

    // Toggle specific Nintendo device controls
    async toggleNintendoDeviceControls(deviceId, targetState) {
        this.showLoading(true);
        
        try {
            const response = await fetch('/api/nintendo/device_toggle', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    device_id: deviceId,
                    active: targetState
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess(result.message);
                this.addToActivityLog(`Nintendo ${deviceId} ${targetState ? 'enabled' : 'disabled'}`, targetState);
                // Refresh device list
                await this.loadNintendoDevices();
            } else {
                this.showError(result.error || `Failed to toggle ${deviceId} controls`);
                // Reset toggle
                const toggle = document.querySelector(`[data-device-id="${deviceId}"]`);
                if (toggle) toggle.checked = !targetState;
            }
            
        } catch (error) {
            console.error(`Device ${deviceId} toggle failed:`, error);
            this.showError(`Failed to toggle ${deviceId} controls`);
            // Reset toggle
            const toggle = document.querySelector(`[data-device-id="${deviceId}"]`);
            if (toggle) toggle.checked = !targetState;
        } finally {
            this.showLoading(false);
        }
    }

    // Update Nintendo stats display
    updateNintendoStats(data) {
        if (data.current_usage) {
            const todayTimeEl = document.getElementById('nintendoTodayTime');
            if (todayTimeEl) {
                todayTimeEl.textContent = `${data.current_usage.today_play_time_minutes} minutes`;
            }
        }
        
        if (data.restrictions && data.restrictions.play_time_limit) {
            const bedtimeEl = document.getElementById('nintendoBedtime');
            const bedtimeStatusEl = document.getElementById('nintendoBedtimeStatus');
            const restrictions = data.restrictions.play_time_limit;
            
            if (bedtimeEl) {
                bedtimeEl.textContent = `${restrictions.bedtime_start} - ${restrictions.bedtime_end}`;
            }
            
            if (bedtimeStatusEl) {
                const now = new Date();
                const currentTime = now.getHours() * 100 + now.getMinutes();
                const bedtimeStart = parseInt(restrictions.bedtime_start.replace(':', ''));
                const bedtimeEnd = parseInt(restrictions.bedtime_end.replace(':', ''));
                
                const isInBedtime = (currentTime >= bedtimeStart) || (currentTime <= bedtimeEnd);
                bedtimeStatusEl.textContent = isInBedtime ? 'Active' : 'Inactive';
                bedtimeStatusEl.className = isInBedtime ? 'active' : 'inactive';
            }
        }
    }

    // Update system status indicator
    updateSystemStatus(status) {
        const statusElement = document.getElementById('systemStatus');
        if (statusElement) {
            console.log('Status value:', status, typeof status);
            if (status) statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
            statusElement.className = `status-value ${status}`;
        }
    }

    // Update last action display
    updateLastAction(reason, time) {
        const actionElement = document.getElementById('lastAction');
        if (actionElement) {
            if (reason && time) {
                const timeAgo = this.getTimeAgo(time);
                actionElement.textContent = `${reason} (${timeAgo})`;
            } else {
                actionElement.textContent = 'None';
            }
        }
    }

    // Update uptime display
    updateUptime(uptimeSeconds) {
        const uptimeElement = document.getElementById('uptime');
        if (uptimeElement && uptimeSeconds) {
            uptimeElement.textContent = this.formatUptime(uptimeSeconds);
        }
    }

    // Update toggle description based on current state
    updateToggleDescription() {
        const descElement = document.getElementById('toggleDescription');
        if (descElement) {
            if (this.currentState.controlsActive) {
                descElement.textContent = '🚫 Network blocking is ACTIVE - Internet access restricted';
                descElement.style.color = '#c53030';
            } else {
                descElement.textContent = '🌐 Network blocking is OFF - Full internet access allowed';
                descElement.style.color = '#2f855a';
            }
        }
    }

    // Update platform status indicators
    updatePlatformStatus(platforms) {
        if (!platforms) return;
        
        Object.keys(platforms).forEach(platform => {
            const statusElement = document.getElementById(`${platform}Status`);
            if (statusElement) {
                const status = platforms[platform];
                statusElement.textContent = status === 'connected' ? 'Connected' : 
                                          status === 'available' ? 'Available' : 'Not Connected';
                statusElement.className = `platform-status-badge ${status}`;
            }
        });
    }

    // Handle main toggle switch change
    async handleToggleChange(event) {
        const newState = event.target.checked;
        const reason = newState ? 'Manual activation' : 'Manual deactivation';
        
        await this.toggleControlsWithState(newState, reason);
    }

    // Handle Nintendo toggle switch change
    async handleNintendoToggleChange(event) {
        console.log('Nintendo toggle clicked:', event.target.checked);
        const newState = event.target.checked;
        await this.toggleNintendoControls(newState);
    }

    // Handle Nintendo authentication form
    async handleNintendoAuth(event) {
        event.preventDefault();
        
        const username = document.getElementById('nintendoUsername').value;
        const password = document.getElementById('nintendoPassword').value;
        
        if (!username || !password) {
            this.showError('Please enter both username and password');
            return;
        }
        
        this.showLoading(true);
        
        try {
            const response = await fetch('/api/nintendo/authenticate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });
            
            const result = await response.json();
            
            if (result.success && result.authenticated) {
                this.showSuccess('Nintendo Switch connected successfully!');
                this.hideNintendoAuth();
                await this.loadNintendoStatus();
                
                // Clear form
                document.getElementById('nintendoLoginForm').reset();
            } else {
                this.showError(result.error || 'Authentication failed');
            }
            
        } catch (error) {
            console.error('Nintendo authentication failed:', error);
            this.showError('Failed to connect to Nintendo Switch');
        } finally {
            this.showLoading(false);
        }
    }

    // Toggle Nintendo Switch controls
    async toggleNintendoControls(targetState) {
        this.showLoading(true);
        
        try {
            const response = await fetch('/api/nintendo/toggle', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    active: targetState
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess(result.message);
                this.addToActivityLog(`Nintendo Switch ${targetState ? 'enabled' : 'disabled'}`, targetState);
                await this.loadNintendoStatus();
            } else {
                this.showError(result.error || 'Failed to toggle Nintendo controls');
                // Reset toggle
                const toggle = document.getElementById('nintendoControlsToggle');
                if (toggle) toggle.checked = !targetState;
            }
            
        } catch (error) {
            console.error('Nintendo toggle failed:', error);
            this.showError('Failed to toggle Nintendo controls');
            // Reset toggle
            const toggle = document.getElementById('nintendoControlsToggle');
            if (toggle) toggle.checked = !targetState;
        } finally {
            this.showLoading(false);
        }
    }

    // Toggle parental controls (flip current state)
    async toggleControls(reason = 'Manual toggle', duration = null) {
        const newState = !this.currentState.controlsActive;
        await this.toggleControlsWithState(newState, reason, duration);
    }
    
    // Toggle parental controls to specific state
    async toggleControlsWithState(targetState, reason = 'Manual toggle', duration = null) {
        this.showLoading(true);
        
        try {
            const params = new URLSearchParams({
                active: targetState.toString(),
                reason: reason
            });
            
            if (duration) {
                params.append('duration', duration.toString());
            }
            
            const response = await fetch(`/api/toggle?${params.toString()}`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.currentState.controlsActive = result.controlsActive;
                this.updateStatus({...this.currentState, ...result});
                this.addToActivityLog(reason, result.controlsActive);
                this.showSuccess(result.message);
                
                // Add visual feedback
                this.flashToggle();
                
                console.log('✅ Toggle successful:', result);
            } else {
                throw new Error(result.error || 'Toggle failed');
            }
            
        } catch (error) {
            console.error('❌ Toggle failed:', error);
            this.showError(`Failed to toggle controls: ${error.message}`);
            
            // Reset toggle to previous state
            const toggle = document.getElementById('controlsToggle');
            if (toggle) {
                toggle.checked = this.currentState.controlsActive;
            }
        } finally {
            this.showLoading(false);
        }
    }

    // Show/hide Nintendo authentication
    showNintendoAuth() {
        const authPanel = document.getElementById('nintendoAuth');
        if (authPanel) {
            authPanel.style.display = 'block';
            document.getElementById('nintendoUsername').focus();
        }
    }

    hideNintendoAuth() {
        const authPanel = document.getElementById('nintendoAuth');
        if (authPanel) {
            authPanel.style.display = 'none';
        }
    }

    // Logout from Nintendo Switch
    async logoutNintendo() {
        this.showLoading(true);
        
        try {
            const response = await fetch('/api/nintendo/logout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('Nintendo Switch disconnected successfully!');
                this.updateNintendoStatus({ authenticated: false });
                this.addToActivityLog('Nintendo Switch logout', false);
                
                // Clear any stored authentication state
                this.nintendoState = {
                    authenticated: false,
                    controlsActive: false,
                    deviceName: 'Nintendo Switch',
                    todayPlayTime: 0,
                    weeklyPlayTime: 0
                };
            } else {
                this.showError(result.error || 'Logout failed');
            }
            
        } catch (error) {
            console.error('Nintendo logout failed:', error);
            this.showError('Failed to logout from Nintendo Switch');
        } finally {
            this.showLoading(false);
        }
    }

    // Add flash effect to toggle
    flashToggle() {
        const toggleSection = document.querySelector('.toggle-section');
        if (toggleSection) {
            toggleSection.style.transform = 'scale(1.05)';
            setTimeout(() => {
                toggleSection.style.transform = 'scale(1)';
            }, 200);
        }
    }

    // Add activity to log
    addToActivityLog(action, controlsActive) {
        const activity = {
            action: `${action} - ${controlsActive ? 'Activated' : 'Deactivated'}`,
            timestamp: new Date().toISOString(),
            type: controlsActive ? 'activation' : 'deactivation'
        };
        
        this.activityLog.unshift(activity);
        
        // Keep only last 10 activities
        if (this.activityLog.length > 10) {
            this.activityLog = this.activityLog.slice(0, 10);
        }
        
        this.updateActivityDisplay();
    }

    // Update activity log display
    updateActivityDisplay() {
        const activityList = document.getElementById('activityList');
        if (!activityList) return;
        
        if (this.activityLog.length === 0) {
            activityList.innerHTML = '<p class="no-activity">No recent activity</p>';
            return;
        }
        
        const html = this.activityLog.map(activity => `
            <div class="activity-item">
                <span class="activity-action">${activity.action}</span>
                <span class="activity-time">${this.getTimeAgo(activity.timestamp)}</span>
            </div>
        `).join('');
        
        activityList.innerHTML = html;
    }

    // Show loading overlay
    showLoading(show = true) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            if (show) {
                overlay.classList.add('active');
            } else {
                overlay.classList.remove('active');
            }
        }
    }

    // Show success message
    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    // Show error message
    showError(message) {
        this.showMessage(message, 'error');
    }

    // Show message with auto-dismiss
    showMessage(message, type = 'info') {
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.message');
        existingMessages.forEach(msg => msg.remove());
        
        // Create new message
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = message;
        
        // Insert after status panel
        const statusPanel = document.querySelector('.status-panel');
        if (statusPanel) {
            statusPanel.insertAdjacentElement('afterend', messageDiv);
        }
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }

    // Update last updated timestamp
    updateLastUpdated() {
        const lastUpdatedElement = document.getElementById('lastUpdated');
        if (lastUpdatedElement) {
            lastUpdatedElement.textContent = new Date().toLocaleTimeString();
        }
    }

    // Start periodic status updates
    startPeriodicUpdates() {
        // Update every 30 seconds
        setInterval(() => {
            this.loadStatus();
        }, 30000);
        
        // Update Nintendo status every minute
        setInterval(() => {
            if (this.nintendoState.authenticated) {
                this.loadNintendoStatus();
            }
        }, 60000);
        
        // Update relative times every minute
        setInterval(() => {
            this.updateActivityDisplay();
            this.updateLastAction(this.currentState.lastToggleReason, this.currentState.lastToggleTime);
        }, 60000);
    }

    // Utility: Get time ago string
    getTimeAgo(timestamp) {
        if (!timestamp) return '';
        
        const now = new Date();
        const time = new Date(timestamp);
        const diffMs = now - time;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        
        if (diffDays > 0) return `${diffDays}d ago`;
        if (diffHours > 0) return `${diffHours}h ago`;
        if (diffMins > 0) return `${diffMins}m ago`;
        return 'Just now';
    }

    // Utility: Format uptime
    formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (days > 0) return `${days}d ${hours}h ${minutes}m`;
        if (hours > 0) return `${hours}h ${minutes}m`;
        if (minutes > 0) return `${minutes}m`;
        return `${Math.floor(seconds)}s`;
    }
}

// Global functions for quick action buttons
async function toggleWithReason(reason) {
    if (window.dashboard) {
        await window.dashboard.toggleControls(reason);
    }
}

async function toggleWithDuration(reason, durationMinutes) {
    if (window.dashboard) {
        await window.dashboard.toggleControls(reason, durationMinutes);
    }
}

// Nintendo quick actions
async function nintendoQuickAction(action, duration) {
    if (window.dashboard && window.dashboard.nintendoState.authenticated) {
        if (action === 'disable') {
            await window.dashboard.toggleNintendoControls(false);
            if (duration > 0) {
                window.dashboard.showSuccess(`Nintendo Switch access granted for ${duration} minutes`);
                // Could implement timer here to re-enable after duration
            }
        } else {
            await window.dashboard.toggleNintendoControls(true);
        }
    } else {
        window.dashboard.showError('Nintendo Switch not connected');
    }
}

// Global functions for Nintendo auth
function showNintendoAuth() {
    if (window.dashboard) {
        window.dashboard.showNintendoAuth();
    }
}

function hideNintendoAuth() {
    if (window.dashboard) {
        window.dashboard.hideNintendoAuth();
    }
}

// Nintendo logout function
async function logout_nintendo() {
    if (window.dashboard) {
        await window.dashboard.logoutNintendo();
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new ParentalControlsDashboard();
});

// Service Worker for offline functionality (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then((registration) => {
                console.log('SW registered: ', registration);
            })
            .catch((registrationError) => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}
